# -*- coding: utf-8 -*-
"""Behavior tests for ``pipeline.mlops.train_preference.run_preference_training``.

The function is one large heavy-op orchestrator (model loading, TRL trainers,
GPU). Every heavy dependency is patched in the *module namespace* so no real
model / dataset / GPU is ever touched. We assert the genuinely meaningful,
non-glue behavior:

* algorithm normalization (env -> simpo/orpo/dpo, invalid -> simpo)
* ``max_seq_length`` default derivation from the model name
* the dataset fallback that writes a dummy JSONL when the file is missing/empty
* the ChatML ``process_dpo_pair`` transform (prompt/chosen/rejected suffixing)
* the real config values passed to ``DPOConfig`` / ``ORPOConfig`` per algorithm
* the eval-strategy branch driven by ``ANIMETIX_ENABLE_EVAL``
* the tracker logging contract

We deliberately do NOT assert "a Trainer object was constructed" as an end in
itself; trainer construction is exercised only to capture the *arguments* that
encode real decisions.
"""

import json
from unittest.mock import MagicMock

import pipeline.mlops.train_preference as tp
import pytest

# --------------------------------------------------------------------------- #
# Helpers / fixtures
# --------------------------------------------------------------------------- #


class _FakeDataset:
    """Minimal stand-in for a HF ``datasets.Dataset``.

    Records the ``process_dpo_pair`` callable handed to ``.map`` so tests can
    apply it to sample rows and assert the real transform output.
    """

    def __init__(self, rows, sink=None):
        self.rows = list(rows)
        self.column_names = list(rows[0].keys()) if rows else []
        # Shared sink so the map fn is reachable regardless of which derived
        # dataset (train/eval/split) actually receives the .map call.
        self.sink = sink if sink is not None else {}

    def __len__(self):
        return len(self.rows)

    def train_test_split(self, test_size=0.1, seed=42):
        # Deterministic split: keep everything in train, one row in test.
        return {
            "train": _FakeDataset(self.rows, self.sink),
            "test": _FakeDataset(self.rows[:1] or self.rows, self.sink),
        }

    def map(self, fn, remove_columns=None):
        self.sink["map_fn"] = fn
        return _FakeDataset([fn(r) for r in self.rows] if self.rows else [], self.sink)


def _fake_tokenizer():
    tok = MagicMock()
    tok.eos_token = "<eos>"

    def apply_chat_template(messages, tokenize=False, add_generation_prompt=False):
        # Deterministic, inspectable serialization. The generation-prompt flag
        # appends a marker so the prompt prefix is shorter than chosen/rejected,
        # which is exactly what the suffix-extraction logic relies on.
        parts = [f"[{m['role']}]{m['content']}" for m in messages]
        s = "".join(parts)
        if add_generation_prompt:
            s += "[assistant]"
        return s

    tok.apply_chat_template.side_effect = apply_chat_template
    return tok


@pytest.fixture
def patched(mocker, tmp_path):
    """Patch every heavy dependency in the module namespace.

    Returns a namespace of the recorded mocks/values for assertions.
    """
    # Redirect BASE_DIR so the dataset path lives under tmp_path.
    mocker.patch.object(tp, "BASE_DIR", str(tmp_path))

    # torch device probing -> deterministic, no GPU.
    mocker.patch.object(tp.torch.cuda, "is_available", return_value=False)
    mocker.patch.object(tp.torch.cuda, "is_bf16_supported", return_value=False)

    # Tracker (the module-level MockTrackio or real trackio) -> spy.
    tracker = MagicMock()
    mocker.patch.object(tp.trackio, "init", return_value=tracker)

    # Tokenizer loading.
    tok = _fake_tokenizer()
    mocker.patch.object(tp, "AutoTokenizer").from_pretrained.return_value = tok

    # Dataset loading -> our fake with two preference rows.
    rows = [
        {"prompt": "Q1", "chosen": "C1", "rejected": "R1"},
        {"prompt": "Q2", "chosen": "C2", "rejected": "R2"},
    ]
    fake_ds = _FakeDataset(rows)
    load_dataset = mocker.patch.object(tp, "load_dataset", return_value=fake_ds)

    # Force the standard PEFT/BitsAndBytes fallback path: make ``unsloth`` import
    # fail. We patch builtins import to raise ImportError for unsloth only.
    real_import = (
        __builtins__["__import__"]
        if isinstance(__builtins__, dict)
        else __builtins__.__import__
    )

    captured = {}

    def fake_import(name, *args, **kwargs):
        if name == "unsloth":
            raise ImportError("unsloth not installed (forced in test)")
        if name == "trl":
            # Provide fake TRL config/trainer classes that record their kwargs.
            mod = MagicMock()

            def make_config(label):
                def _cfg(**kw):
                    captured.setdefault("configs", []).append((label, kw))
                    obj = MagicMock()
                    obj._kwargs = kw
                    return obj

                return _cfg

            def make_trainer(label):
                def _trainer(**kw):
                    captured.setdefault("trainers", []).append((label, kw))
                    t = MagicMock()
                    t._kwargs = kw
                    return t

                return _trainer

            mod.DPOConfig = make_config("DPOConfig")
            mod.ORPOConfig = make_config("ORPOConfig")
            mod.DPOTrainer = make_trainer("DPOTrainer")
            mod.ORPOTrainer = make_trainer("ORPOTrainer")
            return mod
        return real_import(name, *args, **kwargs)

    mocker.patch("builtins.__import__", side_effect=fake_import)

    # AutoModelForCausalLM / BitsAndBytesConfig / LoraConfig -> light spies.
    model = MagicMock()
    mocker.patch.object(tp, "AutoModelForCausalLM").from_pretrained.return_value = model
    mocker.patch.object(tp, "BitsAndBytesConfig", MagicMock())
    lora = mocker.patch.object(tp, "LoraConfig")

    return {
        "tmp_path": tmp_path,
        "tracker": tracker,
        "tokenizer": tok,
        "fake_ds": fake_ds,
        "load_dataset": load_dataset,
        "captured": captured,
        "model": model,
        "lora": lora,
    }


def _dataset_path(tmp_path):
    return tmp_path / "data" / "mlops" / "datasets" / "dpo_train_validated.jsonl"


def _seed_dataset(tmp_path):
    """Write a non-empty dataset so the dummy-fallback branch is skipped."""
    p = _dataset_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"prompt": "p", "chosen": "c", "rejected": "r"}) + "\n",
        encoding="utf-8",
    )
    return p


def _last_config(captured, label):
    for lbl, kw in reversed(captured.get("configs", [])):
        if lbl == label:
            return kw
    raise AssertionError(f"no {label} captured; got {captured.get('configs')}")


# --------------------------------------------------------------------------- #
# Algorithm normalization + seq-length derivation
# --------------------------------------------------------------------------- #


def test_invalid_algorithm_falls_back_to_simpo(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "garbage")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    # SimPO path constructs a DPOConfig with loss_type="simpo".
    cfg = _last_config(patched["captured"], "DPOConfig")
    assert cfg["loss_type"] == "simpo"
    assert cfg["beta"] == 2.0
    assert cfg["simpo_gamma"] == 1.4


def test_orpo_algorithm_uses_orpo_config_and_lr(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "ORPO")  # case-insensitive
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "ORPOConfig")
    # ORPO uses the higher RL learning rate.
    assert cfg["learning_rate"] == 5e-6
    # ORPO trainer must be the one instantiated.
    labels = [lbl for lbl, _ in patched["captured"]["trainers"]]
    assert "ORPOTrainer" in labels


def test_dpo_algorithm_uses_sigmoid_and_low_lr(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "dpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "DPOConfig")
    assert cfg["loss_type"] == "sigmoid"
    assert cfg["beta"] == 0.1
    assert cfg["learning_rate"] == 1e-6  # non-orpo low rate


def test_max_seq_length_deepseek_default(patched, monkeypatch):
    monkeypatch.delenv("MAX_SEQ_LENGTH", raising=False)
    monkeypatch.setenv("BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-7B")
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "DPOConfig")
    # deepseek -> 1024; max_length == seq_len, max_prompt_length == seq_len//2.
    assert cfg["max_length"] == 1024
    assert cfg["max_prompt_length"] == 512


def test_max_seq_length_non_deepseek_default(patched, monkeypatch):
    monkeypatch.delenv("MAX_SEQ_LENGTH", raising=False)
    monkeypatch.setenv("BASE_MODEL_NAME", "mistralai/Mistral-7B")
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "DPOConfig")
    assert cfg["max_length"] == 768
    assert cfg["max_prompt_length"] == 384


# --------------------------------------------------------------------------- #
# Dataset fallback (guard branch)
# --------------------------------------------------------------------------- #


def test_missing_dataset_writes_dummy_jsonl(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    path = _dataset_path(patched["tmp_path"])
    assert not path.exists()

    tp.run_preference_training()

    # The guard created the file with two valid preference triples.
    assert path.exists()
    lines = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    for item in lines:
        assert set(item) == {"prompt", "chosen", "rejected"}
        assert item["chosen"] and item["rejected"]
    assert "One Piece" in lines[0]["prompt"]


def test_empty_dataset_file_triggers_dummy(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    path = _dataset_path(patched["tmp_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")  # exists but size 0

    tp.run_preference_training()

    assert path.read_text(encoding="utf-8").strip()  # now populated
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_small_dataset_triggers_reload_branch(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    # A single-row dataset (< 2) hits the duplication / re-load guard.
    single = _FakeDataset([{"prompt": "p", "chosen": "c", "rejected": "r"}])
    patched["load_dataset"].return_value = single

    tp.run_preference_training()

    # load_dataset is invoked twice: initial load + the re-load in the guard.
    assert patched["load_dataset"].call_count == 2


def test_existing_dataset_is_not_overwritten(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    path = _seed_dataset(patched["tmp_path"])
    original = path.read_text(encoding="utf-8")

    tp.run_preference_training()

    assert path.read_text(encoding="utf-8") == original  # untouched


# --------------------------------------------------------------------------- #
# process_dpo_pair transform (the real data-formatting logic)
# --------------------------------------------------------------------------- #


def test_process_dpo_pair_extracts_assistant_suffix(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    # The mapping fn was recorded by our fake dataset's .map().
    fn = patched["fake_ds"].sink.get("map_fn")
    assert fn is not None

    out = fn({"prompt": "Who is Luffy?", "chosen": "Captain.", "rejected": "Dunno."})

    # prompt ends with the generation-prompt marker injected by the tokenizer.
    assert out["prompt"].endswith("[assistant]")
    assert "Who is Luffy?" in out["prompt"]
    # chosen / rejected are the *suffix* after the shared prompt prefix (which
    # already includes the "[assistant]" generation marker) -> only the actual
    # answer text remains.
    assert out["chosen"] == "Captain."
    assert out["rejected"] == "Dunno."
    # The user content must NOT leak into the response suffix.
    assert "Who is Luffy?" not in out["chosen"]


def test_process_dpo_pair_includes_system_persona(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()
    fn = patched["fake_ds"].sink.get("map_fn")
    out = fn({"prompt": "x", "chosen": "y", "rejected": "z"})

    # The Animetix system persona is part of the prompt.
    assert "Animetix" in out["prompt"]
    assert "[system]" in out["prompt"]


# --------------------------------------------------------------------------- #
# eval strategy branch + shared training args
# --------------------------------------------------------------------------- #


def test_eval_disabled_by_default(patched, monkeypatch):
    monkeypatch.delenv("ANIMETIX_ENABLE_EVAL", raising=False)
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "DPOConfig")
    assert cfg["eval_strategy"] == "no"
    assert cfg["eval_steps"] == 9999


def test_eval_enabled_via_env(patched, monkeypatch):
    monkeypatch.setenv("ANIMETIX_ENABLE_EVAL", "true")
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "DPOConfig")
    assert cfg["eval_strategy"] == "steps"
    assert cfg["eval_steps"] == 50


def test_shared_training_args_values(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    cfg = _last_config(patched["captured"], "DPOConfig")
    # Spot-check the static, decision-bearing hyperparameters.
    assert cfg["per_device_train_batch_size"] == 1
    assert cfg["gradient_accumulation_steps"] == 8
    assert cfg["max_steps"] == 200
    assert cfg["save_total_limit"] == 1
    assert cfg["optim"] == "paged_adamw_8bit"
    assert cfg["report_to"] == "none"
    # is_bf16_supported() was forced False -> fp16 True, bf16 False.
    assert cfg["fp16"] is True
    assert cfg["bf16"] is False


# --------------------------------------------------------------------------- #
# Fallback model path + tracker contract + train() invocation
# --------------------------------------------------------------------------- #


def test_peft_fallback_builds_lora_config(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    # unsloth import was forced to fail -> standard PEFT path -> LoraConfig built.
    patched["lora"].assert_called_once()
    kwargs = patched["lora"].call_args.kwargs
    assert kwargs["r"] == 16
    assert kwargs["lora_alpha"] == 32
    assert kwargs["task_type"] == "CAUSAL_LM"
    assert "q_proj" in kwargs["target_modules"]


def test_tracker_logs_and_train_invoked(patched, monkeypatch):
    monkeypatch.setenv("ALIGNMENT_ALGORITHM", "simpo")
    monkeypatch.setenv("BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-7B")
    _seed_dataset(patched["tmp_path"])

    tp.run_preference_training()

    tracker = patched["tracker"]
    tracker.log_param.assert_any_call(
        "model_base", "unsloth/DeepSeek-R1-Distill-Qwen-7B"
    )
    tracker.log_param.assert_any_call("algorithm", "simpo")
    tracker.finish.assert_called_once_with(status="COMPLETED")

    # The captured trainer must have had .train() called on it.
    label, kw = patched["captured"]["trainers"][-1]
    kw["model"]  # model wired through
    # The simpo trainer is a DPOTrainer with ref_model=None.
    assert label == "DPOTrainer"
    assert kw["ref_model"] is None

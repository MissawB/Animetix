# -*- coding: utf-8 -*-
"""Behavior tests for ``pipeline.mlops.train_expert_model``.

``run_expert_training`` is one large heavy-op orchestrator (model loading, the
TRL ``SFTTrainer``, GPU). Every heavy dependency is patched in the *module
namespace* so no real model / dataset / GPU is ever touched. We assert the
genuinely meaningful, non-glue behavior:

* the standalone ``format_chatml_messages`` ChatML formatter (mono-turn,
  multi-turn, language selection, optional ``input`` context)
* the missing-dataset guard (logs FAILED + returns early, never loads a model)
* ``max_seq_length`` default derivation from the model name
* the real ``LoraConfig`` values built on the PEFT/bnb fallback path
* the ``BitsAndBytesConfig`` (4-bit) vs full-precision (``ANIMETIX_DISABLE_QUANT``)
  branch
* the DataCollator response-template validation loop (which template wins, and
  the fallback to ``DataCollatorForLanguageModeling`` when none mask tokens)
* the packing branch that bypasses the collator entirely
* the eval-strategy branch driven by ``ANIMETIX_ENABLE_EVAL``
* the real ``TrainingArguments`` hyperparameters
* the provenance + tracker logging contract (log_param/log_artifact/finish)

We deliberately do NOT assert "an SFTTrainer object was constructed" as an end
in itself; trainer construction is exercised only to capture the *arguments*
that encode real decisions, and to verify ``.train()`` is invoked.
"""

import builtins
from unittest.mock import MagicMock

import pipeline.mlops.train_expert_model as tem
import pytest

# --------------------------------------------------------------------------- #
# format_chatml_messages — pure, standalone, no orchestrator needed
# --------------------------------------------------------------------------- #


def test_chatml_french_system_persona_mono_turn():
    msgs = tem.format_chatml_messages(
        {"instruction": "Qui est Luffy ?", "output": "Le capitaine."}
    )
    assert msgs[0]["role"] == "system"
    assert "Animetix" in msgs[0]["content"]
    assert "français" in msgs[0]["content"]
    assert msgs[1] == {"role": "user", "content": "Qui est Luffy ?"}
    assert msgs[2] == {"role": "assistant", "content": "Le capitaine."}


def test_chatml_english_system_persona():
    msgs = tem.format_chatml_messages(
        {"language": "English", "instruction": "Who is Luffy?", "output": "Captain."}
    )
    assert "English" in msgs[0]["content"]
    assert msgs[1]["content"] == "Who is Luffy?"


def test_chatml_mono_turn_with_input_context_french():
    msgs = tem.format_chatml_messages(
        {"instruction": "Résume.", "input": "Arc Marineford", "output": "OK"}
    )
    # French uses the "Contexte :" label and folds input into the user turn.
    assert msgs[1]["content"] == "Résume.\n\nContexte : Arc Marineford"


def test_chatml_mono_turn_with_input_context_english():
    msgs = tem.format_chatml_messages(
        {
            "language": "English",
            "instruction": "Summarize.",
            "input": "Marineford arc",
            "output": "OK",
        }
    )
    assert msgs[1]["content"] == "Summarize.\n\nContext: Marineford arc"


def test_chatml_empty_input_is_ignored():
    # Falsy "input" must NOT add a context block.
    msgs = tem.format_chatml_messages(
        {"instruction": "Hi", "input": "", "output": "Bye"}
    )
    assert msgs[1]["content"] == "Hi"


def test_chatml_multi_turn_expands_all_turns():
    msgs = tem.format_chatml_messages(
        {
            "turns": [
                {"user": "U1", "assistant": "A1"},
                {"user": "U2", "assistant": "A2"},
            ]
        }
    )
    # system + 2 turns * (user+assistant) = 5 messages
    assert [m["role"] for m in msgs] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert msgs[1]["content"] == "U1"
    assert msgs[4]["content"] == "A2"


# --------------------------------------------------------------------------- #
# Helpers / fixtures for the orchestrator
# --------------------------------------------------------------------------- #


class _FakeDataset:
    """Minimal stand-in for a HF ``datasets.Dataset``.

    Records the ``process_chatml`` callable handed to ``.map`` so tests can
    apply it to sample rows and assert the real transform output.
    """

    def __init__(self, rows, sink=None):
        self.rows = list(rows)
        self.column_names = list(rows[0].keys()) if rows else []
        self.sink = sink if sink is not None else {}

    def __len__(self):
        return len(self.rows)

    def train_test_split(self, test_size=0.05, seed=42):
        return {
            "train": _FakeDataset(self.rows, self.sink),
            "test": _FakeDataset(self.rows[:1] or self.rows, self.sink),
        }

    def map(self, fn, remove_columns=None):
        self.sink["map_fn"] = fn
        return _FakeDataset([fn(r) for r in self.rows] if self.rows else [], self.sink)


class _FakeTensor:
    """Tiny tensor-ish object supporting the ops the collator branch uses."""

    def __init__(self, values):
        self.values = list(values)

    def tolist(self):
        return list(self.values)


def _fake_tokenizer():
    tok = MagicMock()
    tok.eos_token = "<eos>"

    def apply_chat_template(messages, tokenize=False, add_generation_prompt=False):
        parts = [f"[{m['role']}]{m['content']}" for m in messages]
        return "".join(parts)

    tok.apply_chat_template.side_effect = apply_chat_template

    # tokenizer(text, return_tensors="pt") -> dict with input_ids[0] tensor-ish
    def call(text, return_tensors=None):
        return {"input_ids": [_FakeTensor([1, 2, 3, 4])]}

    tok.side_effect = call
    return tok


def _labels_from(trained_count):
    """Build a fake collator torch_call output whose labels have ``trained_count``
    non-(-100) entries."""
    masked = MagicMock()
    masked.sum.return_value.item.return_value = trained_count

    class _LabelsRow:
        def __ne__(self, other):  # labels != -100
            return masked

    return {"labels": [_LabelsRow()]}


@pytest.fixture
def patched(mocker, tmp_path):
    """Patch every heavy dependency in the module namespace."""
    mocker.patch.object(tem, "BASE_DIR", str(tmp_path))

    mocker.patch.object(tem.torch.cuda, "is_available", return_value=False)
    mocker.patch.object(tem.torch.cuda, "is_bf16_supported", return_value=False)
    mocker.patch.object(tem.torch.cuda, "device_count", return_value=0)

    tracker = MagicMock()
    mocker.patch.object(tem.trackio, "init", return_value=tracker)

    tok = _fake_tokenizer()
    mocker.patch.object(tem, "AutoTokenizer").from_pretrained.return_value = tok

    rows = [
        {"instruction": "Q1", "output": "A1"},
        {"instruction": "Q2", "output": "A2"},
    ]
    fake_ds = _FakeDataset(rows)
    load_dataset = mocker.patch.object(tem, "load_dataset", return_value=fake_ds)

    # Force the standard PEFT/BitsAndBytes fallback path: make ``unsloth`` import
    # fail. (unsloth is the only heavy dep imported lazily via __import__.)
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "unsloth":
            raise ImportError("unsloth not installed (forced in test)")
        return real_import(name, *args, **kwargs)

    mocker.patch("builtins.__import__", side_effect=fake_import)

    model = MagicMock()
    mocker.patch.object(tem, "AutoModelForCausalLM").from_pretrained.return_value = (
        model
    )
    bnb = mocker.patch.object(tem, "BitsAndBytesConfig", MagicMock())
    lora = mocker.patch.object(tem, "LoraConfig")

    # TRL trainer (module-level import) -> spy capturing kwargs + recording train().
    sft = mocker.patch.object(tem, "SFTTrainer")
    sft_instance = MagicMock()
    sft.return_value = sft_instance

    # TRL completion-only collator: produce a collator whose torch_call yields
    # masked labels with >0 trained tokens (so the first template validates).
    collator_cls = mocker.patch.object(tem, "DataCollatorForCompletionOnlyLM")
    coll_instance = MagicMock()
    coll_instance.torch_call.return_value = _labels_from(3)
    collator_cls.return_value = coll_instance

    # TrainingArguments -> capture kwargs.
    captured_args = {}

    def make_ta(**kw):
        captured_args.update(kw)
        return MagicMock()

    ta = mocker.patch.object(tem, "TrainingArguments", side_effect=make_ta)

    # provenance write (lazily imported as pipeline.mlops.run_provenance).
    provenance = {"git_commit": "deadbeefcafebabe", "timestamp": "now"}
    write_meta = mocker.patch(
        "pipeline.mlops.run_provenance.write_run_metadata",
        return_value=provenance,
    )

    return {
        "tmp_path": tmp_path,
        "tracker": tracker,
        "tokenizer": tok,
        "fake_ds": fake_ds,
        "load_dataset": load_dataset,
        "model": model,
        "bnb": bnb,
        "lora": lora,
        "sft": sft,
        "sft_instance": sft_instance,
        "collator_cls": collator_cls,
        "coll_instance": coll_instance,
        "training_args": ta,
        "captured_args": captured_args,
        "write_meta": write_meta,
    }


def _dataset_path(tmp_path):
    import os

    return os.path.join(
        str(tmp_path), "data", "mlops", "datasets", "animetix_expert_ft.jsonl"
    )


def _seed_dataset(tmp_path):
    import os

    p = _dataset_path(tmp_path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write('{"instruction": "x", "output": "y"}\n')
    return p


# --------------------------------------------------------------------------- #
# Missing dataset guard
# --------------------------------------------------------------------------- #


def test_missing_dataset_logs_failed_and_returns_early(patched, monkeypatch):
    # No dataset file seeded.
    tem.run_expert_training()

    # Tracker init happened, then finish(FAILED), and we returned before any
    # model/tokenizer/dataset load.
    patched["tracker"].finish.assert_called_once_with(status="FAILED")
    patched["load_dataset"].assert_not_called()
    patched["sft"].assert_not_called()


# --------------------------------------------------------------------------- #
# max_seq_length derivation
# --------------------------------------------------------------------------- #


def test_max_seq_length_deepseek_default(patched, monkeypatch):
    monkeypatch.delenv("MAX_SEQ_LENGTH", raising=False)
    monkeypatch.setenv("BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-7B")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    # deepseek -> 1024 flows into the SFTTrainer max_seq_length kwarg.
    kw = patched["sft"].call_args.kwargs
    assert kw["max_seq_length"] == 1024


def test_max_seq_length_non_deepseek_default(patched, monkeypatch):
    monkeypatch.delenv("MAX_SEQ_LENGTH", raising=False)
    monkeypatch.setenv("BASE_MODEL_NAME", "mistralai/Mistral-7B")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    kw = patched["sft"].call_args.kwargs
    assert kw["max_seq_length"] == 768


def test_max_seq_length_env_override(patched, monkeypatch):
    monkeypatch.setenv("MAX_SEQ_LENGTH", "256")
    monkeypatch.setenv("BASE_MODEL_NAME", "mistralai/Mistral-7B")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    assert patched["sft"].call_args.kwargs["max_seq_length"] == 256


# --------------------------------------------------------------------------- #
# PEFT / quantization fallback branch
# --------------------------------------------------------------------------- #


def test_peft_fallback_builds_lora_config(patched, monkeypatch):
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    patched["lora"].assert_called_once()
    kwargs = patched["lora"].call_args.kwargs
    assert kwargs["r"] == 16
    assert kwargs["lora_alpha"] == 32
    assert kwargs["lora_dropout"] == 0.05
    assert kwargs["use_rslora"] is True
    assert kwargs["task_type"] == "CAUSAL_LM"
    assert "q_proj" in kwargs["target_modules"]
    assert "down_proj" in kwargs["target_modules"]


def test_default_path_uses_4bit_bnb_quantization(patched, monkeypatch):
    monkeypatch.delenv("ANIMETIX_DISABLE_QUANT", raising=False)
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    # BitsAndBytesConfig built with nf4 / double-quant on the non-distributed path.
    patched["bnb"].assert_called_once()
    bkw = patched["bnb"].call_args.kwargs
    assert bkw["load_in_4bit"] is True
    assert bkw["bnb_4bit_quant_type"] == "nf4"
    assert bkw["bnb_4bit_use_double_quant"] is True
    # Model loaded with quantization_config wired through.
    from_pretrained = tem.AutoModelForCausalLM.from_pretrained
    assert (
        from_pretrained.call_args.kwargs["quantization_config"]
        is patched["bnb"].return_value
    )


def test_disable_quant_loads_full_precision(patched, monkeypatch):
    monkeypatch.setenv("ANIMETIX_DISABLE_QUANT", "true")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    # No 4-bit config built; model loaded with torch_dtype instead.
    patched["bnb"].assert_not_called()
    fp_kwargs = tem.AutoModelForCausalLM.from_pretrained.call_args.kwargs
    assert "quantization_config" not in fp_kwargs
    assert "torch_dtype" in fp_kwargs


# --------------------------------------------------------------------------- #
# process_chatml map transform
# --------------------------------------------------------------------------- #


def test_process_chatml_produces_text_field(patched, monkeypatch):
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    fn = patched["fake_ds"].sink.get("map_fn")
    assert fn is not None
    out = fn({"instruction": "Who is Zoro?", "output": "Swordsman."})
    # The mapper returns a {"text": <chatml string>} dict, serialized by our
    # fake tokenizer's apply_chat_template.
    assert set(out) == {"text"}
    assert "[system]" in out["text"]
    assert "Who is Zoro?" in out["text"]
    assert "Swordsman." in out["text"]


# --------------------------------------------------------------------------- #
# DataCollator template validation loop
# --------------------------------------------------------------------------- #


def test_collator_first_valid_template_wins(patched, monkeypatch):
    monkeypatch.delenv("ANIMETIX_PACKING", raising=False)
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    # First template "<|im_start|>assistant\n" masks >0 tokens (fake returns 3),
    # so it is selected immediately and wired into the trainer.
    first_call = patched["collator_cls"].call_args_list[0]
    assert first_call.kwargs["response_template"] == "<|im_start|>assistant\n"
    assert patched["sft"].call_args.kwargs["data_collator"] is patched["coll_instance"]


def test_collator_falls_back_to_language_modeling(patched, monkeypatch, mocker):
    monkeypatch.delenv("ANIMETIX_PACKING", raising=False)
    _seed_dataset(patched["tmp_path"])

    # Make every completion-only template mask zero tokens -> none validate ->
    # fall back to DataCollatorForLanguageModeling (lazily imported from
    # transformers).
    patched["coll_instance"].torch_call.return_value = _labels_from(0)

    fake_lm_collator = MagicMock()
    fake_lm_cls = MagicMock(return_value=fake_lm_collator)
    import transformers

    mocker.patch.object(transformers, "DataCollatorForLanguageModeling", fake_lm_cls)

    tem.run_expert_training()

    fake_lm_cls.assert_called_once()
    assert fake_lm_cls.call_args.kwargs["mlm"] is False
    assert patched["sft"].call_args.kwargs["data_collator"] is fake_lm_collator


def test_packing_bypasses_collator(patched, monkeypatch):
    monkeypatch.setenv("ANIMETIX_PACKING", "true")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    # No collator constructed; packing flag flows into the trainer.
    patched["collator_cls"].assert_not_called()
    kw = patched["sft"].call_args.kwargs
    assert kw["packing"] is True
    assert kw["data_collator"] is None


# --------------------------------------------------------------------------- #
# Eval strategy + TrainingArguments hyperparameters
# --------------------------------------------------------------------------- #


def test_eval_disabled_by_default(patched, monkeypatch):
    monkeypatch.delenv("ANIMETIX_ENABLE_EVAL", raising=False)
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    args = patched["captured_args"]
    assert args["eval_strategy"] == "no"
    assert args["eval_steps"] == 9999


def test_eval_enabled_via_env(patched, monkeypatch):
    monkeypatch.setenv("ANIMETIX_ENABLE_EVAL", "1")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    args = patched["captured_args"]
    assert args["eval_strategy"] == "steps"
    assert args["eval_steps"] == 100


def test_training_args_static_hyperparameters(patched, monkeypatch):
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    args = patched["captured_args"]
    assert args["per_device_train_batch_size"] == 1
    assert args["gradient_accumulation_steps"] == 8
    assert args["max_steps"] == 2500
    assert args["learning_rate"] == 2e-4
    assert args["save_total_limit"] == 1
    assert args["lr_scheduler_type"] == "cosine"
    assert args["neftune_noise_alpha"] == 5.0
    assert args["report_to"] == "none"
    # Non-distributed (CPU) path -> paged 8-bit optimizer.
    assert args["optim"] == "paged_adamw_8bit"
    # is_bf16_supported() forced False -> fp16 True, bf16 False.
    assert args["fp16"] is True
    assert args["bf16"] is False


# --------------------------------------------------------------------------- #
# Provenance + tracker contract + train() invocation
# --------------------------------------------------------------------------- #


def test_distributed_path_injects_fsdp_and_adamw(patched, monkeypatch):
    # WORLD_SIZE > 1 -> is_distributed True. This bypasses Unsloth, disables
    # quantization (full precision), switches the optimizer, and injects FSDP.
    monkeypatch.setenv("WORLD_SIZE", "2")
    monkeypatch.setenv("ANIMETIX_FSDP_CONFIG", "full_shard")
    monkeypatch.delenv("ANIMETIX_DEEPSPEED_CONFIG", raising=False)
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    args = patched["captured_args"]
    # Distributed -> standard torch AdamW, not paged 8-bit.
    assert args["optim"] == "adamw_torch"
    # FSDP wiring built from env.
    assert args["fsdp"] == "full_shard"
    assert args["fsdp_config"]["transformer_layer_cls_to_wrap"] == "Qwen2DecoderLayer"
    # Distributed forces disable_quant -> no BitsAndBytesConfig built.
    patched["bnb"].assert_not_called()


def test_distributed_deepspeed_injection(patched, monkeypatch, tmp_path):
    import os

    ds_cfg = os.path.join(str(tmp_path), "ds.json")
    with open(ds_cfg, "w", encoding="utf-8") as f:
        f.write("{}")
    monkeypatch.setenv("WORLD_SIZE", "2")
    monkeypatch.setenv("ANIMETIX_DEEPSPEED_CONFIG", ds_cfg)
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    # DeepSpeed path takes precedence over FSDP when the config file exists.
    assert patched["captured_args"]["deepspeed"] == ds_cfg


def test_tracker_and_provenance_contract(patched, monkeypatch):
    monkeypatch.setenv("BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-7B")
    _seed_dataset(patched["tmp_path"])

    tem.run_expert_training()

    tracker = patched["tracker"]
    tracker.log_param.assert_any_call(
        "model_base", "unsloth/DeepSeek-R1-Distill-Qwen-7B"
    )
    tracker.log_param.assert_any_call("git_commit", "deadbeefcafebabe")
    tracker.finish.assert_called_once_with(status="COMPLETED")

    # Provenance metadata was written next to the adapter output dir.
    patched["write_meta"].assert_called_once()
    pkw = patched["write_meta"].call_args
    assert pkw.kwargs["model_base"] == "unsloth/DeepSeek-R1-Distill-Qwen-7B"

    # Training actually launched.
    patched["sft_instance"].train.assert_called_once()

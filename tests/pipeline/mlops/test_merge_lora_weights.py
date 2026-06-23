"""Behavior tests for the LoRA weight-merge MLOps step.

Covers the orchestration of `merge_lora()`: the missing-adapter early return,
the base-model + tokenizer load, the PeftModel adapter wiring, the
`merge_and_unload()` call, the CUDA->CPU OOM fallback, and that the merged
model *and* tokenizer are saved to the computed output path.

All heavy ops (model/tokenizer/adapter loads, CUDA, filesystem existence) are
mocked — no real model download, GPU, or disk writes.
"""

import os
from unittest.mock import MagicMock

import pipeline.mlops.merge_lora_weights as mlw


def _wire(mocker, *, adapter_exists=True, cuda=False, from_pretrained_side_effect=None):
    """Patch the module namespace and return the key mocks for assertions."""
    mocker.patch.object(mlw.os.path, "exists", return_value=adapter_exists)
    mocker.patch.object(mlw.torch.cuda, "is_available", return_value=cuda)

    base_model = MagicMock(name="base_model")
    auto_model = mocker.patch.object(mlw, "AutoModelForCausalLM")
    if from_pretrained_side_effect is not None:
        auto_model.from_pretrained.side_effect = from_pretrained_side_effect
    else:
        auto_model.from_pretrained.return_value = base_model

    tokenizer = MagicMock(name="tokenizer")
    auto_tok = mocker.patch.object(mlw, "AutoTokenizer")
    auto_tok.from_pretrained.return_value = tokenizer

    merged = MagicMock(name="merged_model")
    peft_model = MagicMock(name="peft_model")
    peft_model.merge_and_unload.return_value = merged
    peft = mocker.patch.object(mlw, "PeftModel")
    peft.from_pretrained.return_value = peft_model

    return {
        "auto_model": auto_model,
        "auto_tok": auto_tok,
        "peft": peft,
        "base_model": base_model,
        "peft_model": peft_model,
        "merged": merged,
        "tokenizer": tokenizer,
    }


def _expected_paths():
    adapter = os.path.join(
        mlw.BASE_DIR, "data", "models", "otaku-expert-adapter", "checkpoint-100"
    )
    output = os.path.join(mlw.BASE_DIR, "data", "models", "otaku-expert-final")
    return adapter, output


# --- missing-adapter branch ----------------------------------------------


def test_returns_early_when_adapter_missing(mocker):
    m = _wire(mocker, adapter_exists=False)
    assert mlw.merge_lora() is None
    # Nothing downstream should run when the adapter is absent.
    m["auto_model"].from_pretrained.assert_not_called()
    m["auto_tok"].from_pretrained.assert_not_called()
    m["peft"].from_pretrained.assert_not_called()


def test_missing_adapter_checks_expected_path(mocker):
    exists = mocker.patch.object(mlw.os.path, "exists", return_value=False)
    mocker.patch.object(mlw.torch.cuda, "is_available", return_value=False)
    mlw.merge_lora()
    adapter, _ = _expected_paths()
    exists.assert_called_once_with(adapter)


# --- success path ---------------------------------------------------------


def test_loads_base_model_from_env_name(mocker, monkeypatch):
    monkeypatch.setenv("BASE_MODEL_NAME", "my/custom-base")
    m = _wire(mocker)
    mlw.merge_lora()
    name = m["auto_model"].from_pretrained.call_args.args[0]
    assert name == "my/custom-base"


def test_defaults_base_model_name_when_env_absent(mocker, monkeypatch):
    monkeypatch.delenv("BASE_MODEL_NAME", raising=False)
    m = _wire(mocker)
    mlw.merge_lora()
    name = m["auto_model"].from_pretrained.call_args.args[0]
    assert name == "unsloth/DeepSeek-R1-Distill-Qwen-7B"


def test_device_map_cpu_when_no_cuda(mocker):
    m = _wire(mocker, cuda=False)
    mlw.merge_lora()
    assert m["auto_model"].from_pretrained.call_args.kwargs["device_map"] == "cpu"


def test_device_map_cuda_when_available(mocker):
    m = _wire(mocker, cuda=True)
    mlw.merge_lora()
    assert m["auto_model"].from_pretrained.call_args.kwargs["device_map"] == "cuda"


def test_peft_adapter_wired_to_base_and_adapter_path(mocker):
    m = _wire(mocker)
    mlw.merge_lora()
    adapter, _ = _expected_paths()
    args = m["peft"].from_pretrained.call_args.args
    # PeftModel.from_pretrained(base_model, adapter_path, ...)
    assert args[0] is m["base_model"]
    assert args[1] == adapter


def test_merge_and_unload_called_on_peft_model(mocker):
    m = _wire(mocker)
    mlw.merge_lora()
    m["peft_model"].merge_and_unload.assert_called_once_with()


def test_merged_model_and_tokenizer_saved_to_output(mocker):
    m = _wire(mocker)
    mlw.merge_lora()
    _, output = _expected_paths()
    m["merged"].save_pretrained.assert_called_once_with(output)
    m["tokenizer"].save_pretrained.assert_called_once_with(output)


def test_tokenizer_loaded_from_same_base_name(mocker, monkeypatch):
    monkeypatch.setenv("BASE_MODEL_NAME", "my/custom-base")
    m = _wire(mocker)
    mlw.merge_lora()
    assert m["auto_tok"].from_pretrained.call_args.args[0] == "my/custom-base"


# --- CUDA OOM fallback branch --------------------------------------------


def test_oom_on_gpu_falls_back_to_cpu(mocker):
    base_model = MagicMock(name="base_model")
    # First (cuda) load raises RuntimeError, second (cpu) load succeeds.
    m = _wire(
        mocker,
        cuda=True,
        from_pretrained_side_effect=[RuntimeError("CUDA OOM"), base_model],
    )
    empty_cache = mocker.patch.object(mlw.torch.cuda, "empty_cache")

    mlw.merge_lora()

    # Loaded twice: once on cuda, once retried on cpu.
    assert m["auto_model"].from_pretrained.call_count == 2
    first_device = (
        m["auto_model"].from_pretrained.call_args_list[0].kwargs["device_map"]
    )
    second_device = (
        m["auto_model"].from_pretrained.call_args_list[1].kwargs["device_map"]
    )
    assert first_device == "cuda"
    assert second_device == "cpu"
    empty_cache.assert_called_once_with()
    # The fallback base model is the one wired into PeftModel.
    assert m["peft"].from_pretrained.call_args.args[0] is base_model


def test_oom_on_cpu_reraises(mocker):
    # No CUDA -> device_map is cpu from the start; a RuntimeError must propagate.
    _wire(
        mocker,
        cuda=False,
        from_pretrained_side_effect=RuntimeError("disk full"),
    )
    import pytest

    with pytest.raises(RuntimeError, match="disk full"):
        mlw.merge_lora()

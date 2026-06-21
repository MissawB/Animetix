"""Real-behavior tests for ``adapters.inference.moondream_adapter.MoondreamAdapter``.

The adapter wraps a multimodal SmolVLM (vision-to-seq) model. All heavy ops are
mocked: the transformers model/processor loaders, torch's CUDA probe + dtypes,
and PIL image decoding. No real model load, GPU, or network access occurs.

Patching strategy: ``_load_model`` performs a parenthesized multi-name local
import (``from transformers import (AutoModelForVision2Seq, AutoProcessor)``).
transformers ships a PEP-562 lazy module whose machinery defeats *replacing* the
class objects via ``patch.object(transformers, "AutoModelForVision2Seq", ...)``
for this import form. We instead patch the ``from_pretrained`` classmethods on
the real classes (which the adapter calls) so the real class objects stay in
place but yield deterministic MagicMock model/processor instances. ``torch``
(CUDA probe + dtypes) and ``PIL.Image.open`` are patched directly on their real
modules, the names the adapter binds at call time.
"""

import io
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import PIL.Image
import pytest
import torch
import transformers
from adapters.inference.moondream_adapter import MoondreamAdapter
from core.domain.exceptions import InferenceError
from core.ports.inference_port import InferenceNotImplementedError

# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #


def _wire_loaders(mocker, cuda_available=False, decoded="A vivid anime scene."):
    """Patch the transformers loaders + torch + PIL used by the adapter.

    Returns a ``Loaders`` namespace exposing the model/processor MagicMocks and
    the patched ``from_pretrained`` mocks (so tests can inspect call args /
    configure side effects).
    """
    model = MagicMock(name="VLMModel")
    # ``self.model.device`` is passed to ``inputs.to(...)`` — give it something
    # concrete and assert it propagates.
    model.device = "cpu-device"
    model.generate.return_value = "GENERATED_IDS"

    processor = MagicMock(name="Processor")
    processor.apply_chat_template.return_value = "TEMPLATED_TEXT"
    # ``processor(...)`` returns an object with ``.to(device)`` -> the inputs.
    proc_inputs = MagicMock(name="Inputs")
    proc_inputs.to.return_value = {"input_ids": "X", "pixel_values": "Y"}
    processor.return_value = proc_inputs
    processor.batch_decode.return_value = [decoded]

    model_from_pretrained = mocker.patch.object(
        transformers.AutoModelForVision2Seq,
        "from_pretrained",
        return_value=model,
    )
    proc_from_pretrained = mocker.patch.object(
        transformers.AutoProcessor,
        "from_pretrained",
        return_value=processor,
    )

    mocker.patch.object(torch.cuda, "is_available", return_value=cuda_available)
    # Sentinel dtypes so we can assert which branch was taken without depending
    # on real torch dtype identity.
    mocker.patch.object(torch, "bfloat16", "BF16", create=True)
    mocker.patch.object(torch, "float32", "FP32", create=True)

    return SimpleNamespace(
        model=model,
        processor=processor,
        model_from_pretrained=model_from_pretrained,
        proc_from_pretrained=proc_from_pretrained,
    )


def _patch_image_open(mocker):
    """Patch PIL.Image.open so decoding returns a controllable image mock."""
    rgb_image = MagicMock(name="RGBImage")
    decoded = MagicMock(name="DecodedImage")
    decoded.convert.return_value = rgb_image
    mocker.patch.object(PIL.Image, "open", return_value=decoded)
    return decoded, rgb_image


# --------------------------------------------------------------------------- #
# Construction & unsupported text capabilities
# --------------------------------------------------------------------------- #


def test_init_defaults_and_custom_model_id():
    a = MoondreamAdapter()
    assert a.model_id == "HuggingFaceTB/SmolVLM-Instruct"
    assert a.model is None
    assert a.processor is None
    assert a.usage_port is None

    custom = MoondreamAdapter(model_id="some/other-vlm")
    assert custom.model_id == "some/other-vlm"


def test_generate_is_not_supported():
    with pytest.raises(InferenceNotImplementedError, match="Pure text generation"):
        MoondreamAdapter().generate("hi")


def test_stream_generate_is_not_supported():
    with pytest.raises(InferenceNotImplementedError, match="Streaming"):
        # Consume in case it were a generator; here it raises eagerly.
        MoondreamAdapter().stream_generate("hi")


def test_get_text_embedding_is_not_supported():
    with pytest.raises(InferenceNotImplementedError, match="Text embedding"):
        MoondreamAdapter().get_text_embedding("hi")


# --------------------------------------------------------------------------- #
# health_check reflects load state
# --------------------------------------------------------------------------- #


def test_health_check_offline_before_load():
    assert MoondreamAdapter().health_check() == {
        "status": "offline",
        "engine": "SmolVLM",
    }


def test_health_check_online_after_model_set():
    a = MoondreamAdapter()
    a.model = MagicMock()  # simulate a loaded model
    assert a.health_check() == {"status": "online", "engine": "SmolVLM"}


# --------------------------------------------------------------------------- #
# Lazy model loading: caching + device/dtype selection
# --------------------------------------------------------------------------- #


def test_load_model_cpu_selects_float32(mocker):
    ld = _wire_loaders(mocker, cuda_available=False)
    a = MoondreamAdapter(model_id="vlm/cpu")
    a._load_model()

    # Model + processor instances are cached on the adapter.
    assert a.model is ld.model
    assert a.processor is ld.processor

    _, kwargs = ld.model_from_pretrained.call_args
    assert kwargs["torch_dtype"] == "FP32"  # cpu branch -> float32 sentinel
    assert kwargs["device_map"] == "auto"
    assert kwargs["trust_remote_code"] is True
    # Positional model id is forwarded.
    assert ld.model_from_pretrained.call_args.args[0] == "vlm/cpu"


def test_load_model_cuda_selects_bfloat16(mocker):
    ld = _wire_loaders(mocker, cuda_available=True)
    a = MoondreamAdapter()
    a._load_model()
    _, kwargs = ld.model_from_pretrained.call_args
    assert kwargs["torch_dtype"] == "BF16"  # cuda branch -> bfloat16 sentinel


def test_load_model_is_cached_and_loads_once(mocker):
    ld = _wire_loaders(mocker)
    a = MoondreamAdapter()
    a._load_model()
    a._load_model()
    a._load_model()
    # Despite three calls, the heavy loaders ran exactly once (early return).
    assert ld.model_from_pretrained.call_count == 1
    assert ld.proc_from_pretrained.call_count == 1


def test_load_model_wraps_loader_failure_in_inference_error(mocker):
    ld = _wire_loaders(mocker)
    # Make the model loader explode.
    ld.model_from_pretrained.side_effect = RuntimeError("CUDA out of memory")
    a = MoondreamAdapter()
    with pytest.raises(
        InferenceError, match="SmolVLM loading failed: CUDA out of memory"
    ):
        a._load_model()
    # Model stays unset so a later call could retry.
    assert a.model is None


# --------------------------------------------------------------------------- #
# generate_image_description: the real multimodal happy path
# --------------------------------------------------------------------------- #


def test_generate_image_description_returns_decoded_text(mocker):
    ld = _wire_loaders(mocker, decoded="A lone samurai at dusk.")
    model, processor = ld.model, ld.processor
    decoded_img, rgb_image = _patch_image_open(mocker)

    a = MoondreamAdapter()
    result = a.generate_image_description(b"rawbytes", prompt="Describe.")

    assert result == "A lone samurai at dusk."

    # Image was decoded from the raw bytes and converted to RGB.
    args, _ = PIL.Image.open.call_args
    assert isinstance(args[0], io.BytesIO)
    decoded_img.convert.assert_called_once_with("RGB")

    # Chat template was built with one image + the prompt text.
    messages = processor.apply_chat_template.call_args.args[0]
    content = messages[0]["content"]
    assert {"type": "image"} in content
    assert {"type": "text", "text": "Describe."} in content

    # Processor received the templated text and the converted image, and the
    # tensors were moved to the model's device.
    _, pkwargs = processor.call_args
    assert pkwargs["text"] == "TEMPLATED_TEXT"
    assert pkwargs["images"] == [rgb_image]
    assert pkwargs["return_tensors"] == "pt"
    processor.return_value.to.assert_called_once_with("cpu-device")

    # generate() got the moved inputs + the max_new_tokens cap.
    _, gkwargs = model.generate.call_args
    assert gkwargs["max_new_tokens"] == 512
    assert gkwargs["input_ids"] == "X"
    # batch_decode skipped special tokens.
    _, dkwargs = processor.batch_decode.call_args
    assert dkwargs["skip_special_tokens"] is True


def test_generate_image_description_uses_default_prompt(mocker):
    ld = _wire_loaders(mocker)
    processor = ld.processor
    _patch_image_open(mocker)
    a = MoondreamAdapter()
    a.generate_image_description(b"img")
    content = processor.apply_chat_template.call_args.args[0][0]["content"]
    text_part = next(c for c in content if c.get("type") == "text")
    assert text_part["text"] == "Décris cette image d'anime de manière très détaillée."


def test_generate_image_description_strips_assistant_prefix(mocker):
    # batch_decode returns the full templated transcript; only the assistant
    # turn should be returned, trimmed.
    _wire_loaders(mocker, decoded="User: hi\nAssistant:   Final answer here.  ")
    _patch_image_open(mocker)
    a = MoondreamAdapter()
    out = a.generate_image_description(b"img")
    assert out == "Final answer here."


def test_generate_image_description_logs_usage_once(mocker):
    _wire_loaders(mocker)
    _patch_image_open(mocker)
    usage_port = MagicMock()
    a = MoondreamAdapter(usage_port=usage_port)
    a.generate_image_description(b"img")
    usage_port.log_usage.assert_called_once()
    # InferencePort._log_usage forwards as
    # log_usage(engine, input_tokens, output_tokens, units, allocated_budget=...).
    args, kwargs = usage_port.log_usage.call_args
    assert args[0] == "local:smolvlm"  # engine
    assert args[1] == 0 and args[2] == 0  # no token accounting
    assert args[3] == 1  # units == 1 (one image processed)


def test_generate_image_description_triggers_lazy_load(mocker):
    ld = _wire_loaders(mocker)
    _patch_image_open(mocker)
    a = MoondreamAdapter()
    assert a.model is None
    a.generate_image_description(b"img")
    # The lazy load happened as a side effect of description generation.
    assert ld.model_from_pretrained.call_count == 1
    assert a.model is ld.model


# --------------------------------------------------------------------------- #
# generate_image_description: error / edge branches
# --------------------------------------------------------------------------- #


def test_generate_image_description_invalid_image_raises_inference_error(mocker):
    _wire_loaders(mocker)
    # Simulate a corrupt/empty image: PIL.Image.open blows up during decode.
    mocker.patch.object(
        PIL.Image, "open", side_effect=OSError("cannot identify image file")
    )
    a = MoondreamAdapter()
    with pytest.raises(InferenceError, match="SmolVLM visual description failed"):
        a.generate_image_description(b"")


def test_generate_image_description_generate_oom_wrapped(mocker):
    ld = _wire_loaders(mocker)
    _patch_image_open(mocker)
    # GPU OOM at inference time -> wrapped, usage not logged.
    ld.model.generate.side_effect = RuntimeError("CUDA out of memory")
    usage_port = MagicMock()
    a = MoondreamAdapter(usage_port=usage_port)
    with pytest.raises(InferenceError, match="CUDA out of memory"):
        a.generate_image_description(b"img")
    usage_port.log_usage.assert_not_called()


def test_generate_image_description_load_failure_propagates(mocker):
    # If the lazy load itself fails, the InferenceError from _load_model
    # surfaces (re-wrapped by the outer except into a description error).
    ld = _wire_loaders(mocker)
    ld.model_from_pretrained.side_effect = RuntimeError("no weights")
    a = MoondreamAdapter()
    with pytest.raises(InferenceError):
        a.generate_image_description(b"img")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))

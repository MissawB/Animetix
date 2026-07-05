"""Behaviour tests raising line coverage of ``video_analysis.py``.

``VideoAnalysisMixin`` is meant to be mixed into ``VisionTransformersAdapter``
(which supplies ``use_4bit``, ``_log_usage`` and optionally ``_load_clip_model``
+ ``_clip_model``). To keep these tests isolated from the heavy adapter (and from
torch / transformers / imageio / PIL), we mix the class into a tiny local host
and patch every heavy boundary:

* ``_load_video_vlm`` is patched out (its own dedicated tests drive the real
  loader against mocked ``torch`` / ``transformers`` submodules).
* ``_sample_video_frames`` is patched / mocked so no real video decoding occurs.
* ``_video_processor`` / ``_video_vlm`` are ``MagicMock`` stand-ins.

Every assertion checks the real returned values, the recorded usage calls, the
JSON parsing of localization output, and the error fallbacks — no false green.
"""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from adapters.inference.video_analysis import (  # noqa: E402
    VideoAnalysisMixin,
)
from core.domain.exceptions import InferenceError
from PIL import Image

MODULE = "adapters.inference.video_analysis"


class _Host(VideoAnalysisMixin):
    """Minimal host exposing the attributes the mixin relies on."""

    def __init__(self, use_4bit=False):
        self.use_4bit = use_4bit
        self.usage_calls = []

    def _log_usage(self, **kwargs):
        self.usage_calls.append(kwargs)


@pytest.fixture
def host():
    return _Host()


def _frame():
    return Image.new("RGB", (8, 8))


def _wire_processor(host, decoded):
    """Attach a mock processor + vlm to *host* returning *decoded* text."""
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    host._video_processor.apply_chat_template.return_value = "PROMPT"
    # processor(...) returns an object whose .to(device) yields the kwargs dict
    host._video_processor.return_value.to.return_value = {"input_ids": [1]}
    host._video_vlm.generate.return_value = [10, 20, 30]
    host._video_processor.batch_decode.return_value = [decoded]
    return host


# --------------------------------------------------------------------------
# _load_video_vlm
# --------------------------------------------------------------------------


def _install_transformers(mock_transformers):
    """Patch ``transformers`` + ``torch`` in sys.modules for the loader."""
    return patch.dict(
        sys.modules,
        {"transformers": mock_transformers, "torch": _fake_torch()},
    )


def _fake_torch():
    t = MagicMock()
    t.float16 = "fp16"
    t.float32 = "fp32"
    t.cuda.is_available.return_value = False
    return t


def test_load_video_vlm_noop_when_already_loaded(host):
    """If ``_video_vlm`` already exists the loader returns immediately."""
    host._video_vlm = MagicMock()
    with patch.dict(sys.modules, {"transformers": MagicMock()}):
        # Should not raise and should not touch transformers.
        assert host._load_video_vlm() is None


def test_load_video_vlm_loads_without_quantization(host):
    """use_4bit=False -> processor/model loaded, no quant config passed."""
    fake_tf = MagicMock()
    fake_proc = MagicMock()
    fake_model = MagicMock()
    fake_tf.AutoProcessor.from_pretrained.return_value = fake_proc
    fake_tf.Qwen2VLForConditionalGeneration.from_pretrained.return_value = fake_model

    with _install_transformers(fake_tf):
        host._load_video_vlm()

    assert host._video_processor is fake_proc
    assert host._video_vlm is fake_model
    # No 4-bit -> BitsAndBytesConfig never constructed.
    fake_tf.BitsAndBytesConfig.assert_not_called()
    _, kwargs = fake_tf.Qwen2VLForConditionalGeneration.from_pretrained.call_args
    assert kwargs["quantization_config"] is None
    assert kwargs["torch_dtype"] == "fp32"  # cuda unavailable -> float32


def test_load_video_vlm_builds_quant_config_when_4bit():
    host = _Host(use_4bit=True)
    fake_tf = MagicMock()
    fake_tf.BitsAndBytesConfig.return_value = "QUANT"

    with _install_transformers(fake_tf):
        host._load_video_vlm()

    fake_tf.BitsAndBytesConfig.assert_called_once()
    _, kwargs = fake_tf.Qwen2VLForConditionalGeneration.from_pretrained.call_args
    assert kwargs["quantization_config"] == "QUANT"


def test_load_video_vlm_raises_inference_error_on_failure(host):
    fake_tf = MagicMock()
    fake_tf.AutoProcessor.from_pretrained.side_effect = RuntimeError("no model")

    with _install_transformers(fake_tf):
        with pytest.raises(InferenceError, match="Video VLM loading failed"):
            host._load_video_vlm()


# --------------------------------------------------------------------------
# _sample_video_frames
# --------------------------------------------------------------------------


def test_sample_video_frames_extracts_expected_count(host):
    mock_imageio = MagicMock()
    reader = MagicMock()
    reader.get_meta_data.return_value = {"fps": 1, "duration": 10}
    reader.__iter__.return_value = [
        np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(10)
    ]
    mock_imageio.get_reader.return_value = reader

    with patch.dict(sys.modules, {"imageio": mock_imageio}):
        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            mock_tmp.return_value.__enter__.return_value.name = "fake.mp4"
            with patch("os.unlink") as mock_unlink:
                frames = host._sample_video_frames(b"video", max_frames=5)

    assert len(frames) == 5
    assert all(isinstance(f, Image.Image) for f in frames)
    reader.close.assert_called_once()
    mock_unlink.assert_called_once_with("fake.mp4")


def test_sample_video_frames_returns_empty_on_exception(host):
    mock_imageio = MagicMock()
    mock_imageio.get_reader.side_effect = OSError("corrupt file")

    with patch.dict(sys.modules, {"imageio": mock_imageio}):
        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            mock_tmp.return_value.__enter__.return_value.name = "fake.mp4"
            frames = host._sample_video_frames(b"video", max_frames=5)

    assert frames == []


# --------------------------------------------------------------------------
# get_video_temporal_embeddings
# --------------------------------------------------------------------------


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_temporal_embeddings_success_without_clip(host):
    _wire_processor(host, "The hero unleashes Gear 5.")

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.get_video_temporal_embeddings(b"data")

    assert len(out) == 1
    seg = out[0]
    assert seg["summary"] == "The hero unleashes Gear 5."
    assert seg["start"] == 0 and seg["end"] == -1
    assert seg["confidence"] == 0.9
    assert seg["embedding"] == []  # no _load_clip_model on host
    assert host.usage_calls == [
        {"engine": "transformers:Qwen3-VL-8B:temporal", "units": 1}
    ]


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_temporal_embeddings_includes_clip_embedding(host):
    _wire_processor(host, "summary text")

    clip = MagicMock()
    clip.encode.return_value = np.array([0.1, 0.2, 0.3])
    host._load_clip_model = MagicMock()
    host._clip_model = clip

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.get_video_temporal_embeddings(b"data")

    host._load_clip_model.assert_called_once()
    clip.encode.assert_called_once_with("summary text")
    assert out[0]["embedding"] == [0.1, 0.2, 0.3]


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_temporal_embeddings_clip_error_is_swallowed(host):
    _wire_processor(host, "summary text")

    host._load_clip_model = MagicMock(side_effect=RuntimeError("clip boom"))

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.get_video_temporal_embeddings(b"data")

    # Embedding generation failed but the summary segment is still returned.
    assert out[0]["embedding"] == []
    assert out[0]["summary"] == "summary text"


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_temporal_embeddings_empty_frames_returns_empty(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    with patch.object(host, "_sample_video_frames", return_value=[]):
        out = host.get_video_temporal_embeddings(b"data")
    assert out == []
    assert host.usage_calls == []  # never reached usage logging


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_temporal_embeddings_wraps_errors_as_inference_error(host):
    _wire_processor(host, "x")
    host._video_vlm.generate.side_effect = RuntimeError("OOM")

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        with pytest.raises(InferenceError, match="Video reasoning failed"):
            host.get_video_temporal_embeddings(b"data")


# --------------------------------------------------------------------------
# localize_video_actions
# --------------------------------------------------------------------------


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_localize_actions_parses_json_per_query(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    host._video_processor.apply_chat_template.return_value = "P"
    host._video_processor.return_value.to.return_value = {}
    host._video_vlm.generate.return_value = [1]
    host._video_processor.batch_decode.side_effect = [
        ['noise [{"start": 1.5, "end": 3.2, "confidence": 0.85}] tail'],
        ['[{"start": 0.0, "end": 1.0, "confidence": 0.5}]'],
    ]

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.localize_video_actions(b"data", ["punch", "kick"])

    assert out == [
        {"start": 1.5, "end": 3.2, "confidence": 0.85, "action": "punch"},
        {"start": 0.0, "end": 1.0, "confidence": 0.5, "action": "kick"},
    ]
    assert len(host.usage_calls) == 2
    assert host.usage_calls[0]["engine"] == "transformers:Qwen3-VL-8B:localize"


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_localize_actions_skips_response_without_brackets(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    host._video_processor.apply_chat_template.return_value = "P"
    host._video_processor.return_value.to.return_value = {}
    host._video_vlm.generate.return_value = [1]
    host._video_processor.batch_decode.return_value = ["no list here"]

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.localize_video_actions(b"data", ["punch"])

    assert out == []  # no "[" "]" -> nothing parsed


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_localize_actions_invalid_json_is_logged_and_skipped(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    host._video_processor.apply_chat_template.return_value = "P"
    host._video_processor.return_value.to.return_value = {}
    host._video_vlm.generate.return_value = [1]
    # Brackets present but content is not valid JSON -> orjson raises, caught.
    host._video_processor.batch_decode.return_value = ["[not, valid, json]"]

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.localize_video_actions(b"data", ["punch"])

    assert out == []
    # Usage still logged before the parse attempt.
    assert host.usage_calls[0]["engine"] == "transformers:Qwen3-VL-8B:localize"


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_localize_actions_empty_frames_returns_empty(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    with patch.object(host, "_sample_video_frames", return_value=[]):
        out = host.localize_video_actions(b"data", ["punch"])
    assert out == []


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_localize_actions_wraps_errors_as_inference_error(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    host._video_processor.apply_chat_template.side_effect = RuntimeError("boom")

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        with pytest.raises(InferenceError, match="Video action localization failed"):
            host.localize_video_actions(b"data", ["punch"])


# --------------------------------------------------------------------------
# generate_video_description
# --------------------------------------------------------------------------


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_generate_description_success(host):
    _wire_processor(host, "An epic anime battle unfolds.")

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.generate_video_description(b"data", prompt="Describe it")

    assert out == "An epic anime battle unfolds."
    assert host.usage_calls == [
        {"engine": "transformers:Qwen3-VL-8B:video_description", "units": 1}
    ]
    # The custom prompt was forwarded into the chat template messages.
    messages = host._video_processor.apply_chat_template.call_args[0][0]
    text_part = messages[0]["content"][1]
    assert text_part["text"] == "Describe it"


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_generate_description_default_prompt(host):
    _wire_processor(host, "desc")
    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        host.generate_video_description(b"data")
    messages = host._video_processor.apply_chat_template.call_args[0][0]
    assert messages[0]["content"][1]["text"] == "Décris cette vidéo d'anime."


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_generate_description_no_frames_returns_message(host):
    host._video_processor = MagicMock()
    host._video_vlm = MagicMock()
    with patch.object(host, "_sample_video_frames", return_value=[]):
        out = host.generate_video_description(b"data")
    assert out == "Aucune frame extraite."


@patch(f"{MODULE}.VideoAnalysisMixin._load_video_vlm", MagicMock())
def test_generate_description_returns_error_string_on_failure(host):
    _wire_processor(host, "x")
    host._video_vlm.generate.side_effect = RuntimeError("decode fail")

    with patch.object(host, "_sample_video_frames", return_value=[_frame()]):
        out = host.generate_video_description(b"data")

    # Unlike the other two methods, this one swallows and returns an error string.
    assert out.startswith("Erreur Video-LLaVA:")
    assert "decode fail" in out

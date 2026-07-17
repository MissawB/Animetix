# Eagerly import torch + torch.overrides BEFORE any patch.dict("sys.modules")
# snapshot so teardown never evicts them (prevents "_has_torch_function already
# has a docstring"). See plan Global Constraints.
import torch  # noqa: F401, I001
import torch.overrides  # noqa: F401
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def mock_cuda_available():
    with patch("torch.cuda.is_available", return_value=True):
        yield


@pytest.fixture(autouse=True)
def mock_pydub():
    """Provide a mock `pydub` so audio_mixin's `from pydub import AudioSegment` works
    without the real package. Fresh mock per test to avoid state leakage."""
    pydub = MagicMock()
    global m_pydub_seg
    m_pydub_seg = pydub.AudioSegment
    with patch.dict("sys.modules", {"pydub": pydub}):
        yield


from adapters.inference.audio_transformers_adapter import (  # noqa: E402
    AudioTransformersAdapter,
)
from core.domain.exceptions import InferenceError  # noqa: E402


@pytest.fixture
def adapter():
    adp = AudioTransformersAdapter()
    adp._stt_processor = None
    adp._stt_model = None
    adp._tts_model = None
    return adp


class TestS2SLoaders:
    @patch(
        "adapters.inference.audio_mixin.get_verified_revision", return_value="deadbeef"
    )
    def test_load_stt_builds_processor_and_model(self, _rev, adapter):
        proc_cls = MagicMock()
        model_cls = MagicMock()
        fake_transformers = MagicMock()
        fake_transformers.KyutaiSpeechToTextProcessor = proc_cls
        fake_transformers.KyutaiSpeechToTextForConditionalGeneration = model_cls
        with patch.dict("sys.modules", {"transformers": fake_transformers}):
            adapter._load_stt()
        proc_cls.from_pretrained.assert_called_once()
        model_cls.from_pretrained.assert_called_once()
        assert adapter._stt_model is not None
        assert adapter._stt_processor is not None

    def test_load_stt_cuda_unavailable(self, adapter):
        with patch("torch.cuda.is_available", return_value=False):
            with pytest.raises(InferenceError, match="CUDA GPU is not available"):
                adapter._load_stt()


class TestTranscribe:
    def test_transcribe_decodes_stt_output(self, adapter):
        audio = MagicMock()
        m_pydub_seg.from_file.return_value = audio
        audio.set_frame_rate.return_value = audio
        audio.set_channels.return_value = audio
        audio.sample_width = 2
        audio.get_array_of_samples.return_value = np.zeros(2400, dtype=np.int16)

        proc = MagicMock()
        inputs = MagicMock()
        proc.return_value = inputs
        inputs.to.return_value = inputs
        proc.batch_decode.return_value = ["  bonjour  "]
        adapter._stt_processor = proc
        model = MagicMock()
        model.generate.return_value = "tokens"
        adapter._stt_model = model

        out = adapter._transcribe(b"audio")
        assert out == "bonjour"
        proc.assert_called_once()
        model.generate.assert_called_once()
        proc.batch_decode.assert_called_once_with("tokens", skip_special_tokens=True)

    def test_transcribe_normalizes_pcm_and_calls_processor_correctly(self, adapter):
        audio = MagicMock()
        m_pydub_seg.from_file.return_value = audio
        audio.set_frame_rate.return_value = audio
        audio.set_channels.return_value = audio
        audio.sample_width = 2
        audio.get_array_of_samples.return_value = np.array([16384], dtype=np.int16)

        proc = MagicMock()
        inputs = MagicMock()
        proc.return_value = inputs
        inputs.to.return_value = inputs
        proc.batch_decode.return_value = ["  bonjour  "]
        adapter._stt_processor = proc
        model = MagicMock()
        model.generate.return_value = "tokens"
        adapter._stt_model = model

        out = adapter._transcribe(b"audio")
        assert out == "bonjour"
        model.generate.assert_called_once()
        proc.batch_decode.assert_called_once_with("tokens", skip_special_tokens=True)

        assert np.allclose(proc.call_args.args[0], np.array([0.5], dtype=np.float32))
        assert proc.call_args.kwargs["sampling_rate"] == 24000
        assert proc.call_args.kwargs["return_tensors"] == "pt"


class TestSynthesize:
    def test_synthesize_returns_wav_bytes(self, adapter):
        adapter._load_xtts = MagicMock()
        tts = MagicMock()
        tts.tts.return_value = [0.0, 0.5, -0.5, 1.0]
        adapter._tts_model = tts

        out = adapter._synthesize("bonjour")
        assert isinstance(out, bytes) and len(out) > 44
        adapter._load_xtts.assert_called_once()
        _, kwargs = tts.tts.call_args
        assert kwargs["text"] == "bonjour"
        assert kwargs["language"] == "fr"
        assert kwargs["speaker"] == "Ana Florence"

    def test_synthesize_raises_when_tts_model_not_loaded(self, adapter):
        adapter._load_xtts = MagicMock()
        adapter._tts_model = None

        with pytest.raises(InferenceError, match="XTTS model not loaded"):
            adapter._synthesize("bonjour")


class TestSpeechToSpeech:
    def _wire(self, adapter, reply="salut"):
        adapter._load_stt = MagicMock()
        adapter._transcribe = MagicMock(return_value="bonjour")
        adapter._synthesize = MagicMock(return_value=b"WAVDATA")
        resp = MagicMock()
        resp.text = reply
        adapter.generate = MagicMock(return_value=resp)
        adapter._log_usage = MagicMock()

    def test_orchestration_happy_path(self, adapter):
        self._wire(adapter)
        out = adapter.speech_to_speech(b"audio", system_prompt="sois bref")
        assert out == b"WAVDATA"
        adapter._transcribe.assert_called_once_with(b"audio")
        _, kwargs = adapter.generate.call_args
        assert kwargs["prompt"] == "bonjour"
        assert kwargs["system_prompt"] == "sois bref"
        adapter._synthesize.assert_called_once_with("salut")
        adapter._log_usage.assert_called_once()

    def test_empty_input(self, adapter):
        with pytest.raises(InferenceError, match="Audio input is empty"):
            adapter.speech_to_speech(b"")

    def test_load_failure_propagates(self, adapter):
        adapter._load_stt = MagicMock(side_effect=InferenceError("STT load failed"))
        with pytest.raises(InferenceError, match="STT load failed"):
            adapter.speech_to_speech(b"audio")

    def test_missing_generate_host(self, adapter):
        from core.ports.inference_port import InferenceNotImplementedError

        adapter._load_stt = MagicMock()
        adapter._transcribe = MagicMock(return_value="bonjour")
        adapter.generate = MagicMock(side_effect=InferenceNotImplementedError("no llm"))
        with pytest.raises(InferenceError, match="LLM-capable host"):
            adapter.speech_to_speech(b"audio")

    def test_cuda_not_available(self, adapter):
        adapter._load_stt = MagicMock(
            side_effect=InferenceError("CUDA GPU is not available.")
        )
        with pytest.raises(InferenceError, match="CUDA GPU is not available"):
            adapter.speech_to_speech(b"audio")

    def test_stage_failure_wrapped(self, adapter):
        self._wire(adapter)
        adapter._synthesize = MagicMock(side_effect=RuntimeError("boom"))
        with pytest.raises(InferenceError, match="Native S2S failed"):
            adapter.speech_to_speech(b"audio")

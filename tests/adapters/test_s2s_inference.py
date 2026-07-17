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


class TestS2SInference:
    @pytest.fixture
    def adapter(self):
        adp = AudioTransformersAdapter()
        adp._moshi_model = None
        return adp

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.from_numpy")
    def test_speech_to_speech_success(self, mock_from_numpy, mock_cuda, adapter):
        # Setup Moshi mock
        mock_moshi_model = MagicMock()
        moshi_cls = mock_moshi_models.Moshi  # noqa: F821
        moshi_cls.from_pretrained.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"

        # Setup AudioSegment mock
        mock_audio = MagicMock()
        segment_cls = mock_pydub_segment  # noqa: F821
        segment_cls.from_file.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.sample_width = 2
        mock_audio.get_array_of_samples.return_value = np.zeros(24000, dtype=np.int16)

        # Mock torch.from_numpy chain
        mock_input_tensor = MagicMock()
        mock_from_numpy.return_value = mock_input_tensor
        mock_input_tensor.unsqueeze.return_value = mock_input_tensor
        mock_input_tensor.to.return_value = mock_input_tensor

        # Mock output audio tensor to return a real numpy array
        mock_output_audio = MagicMock()
        mock_output_audio.detach.return_value = mock_output_audio
        mock_output_audio.cpu.return_value = mock_output_audio
        mock_output_audio.numpy.return_value = np.zeros((1, 24000), dtype=np.float32)

        mock_moshi_model.generate.return_value = mock_output_audio

        result = adapter.speech_to_speech(b"fake audio")

        assert isinstance(result, bytes)
        mock_moshi_model.generate.assert_called_once()

    def test_speech_to_speech_empty_input(self, adapter):
        with pytest.raises(InferenceError, match="Audio input is empty"):
            adapter.speech_to_speech(b"")

    @patch(
        "adapters.inference.audio_transformers_adapter.AudioTransformersAdapter._load_moshi"
    )
    def test_speech_to_speech_load_failure(self, mock_load, adapter):
        mock_load.side_effect = InferenceError("Moshi engine loading failed")
        with pytest.raises(InferenceError, match="Moshi engine loading failed"):
            adapter.speech_to_speech(b"some audio")

    def test_speech_to_speech_general_failure(self, adapter):
        # Manually set a mock model to skip loading
        adapter._moshi_model = MagicMock()
        # Make pydub fail
        segment_cls = mock_pydub_segment  # noqa: F821
        segment_cls.from_file.side_effect = Exception("Pydub crash")

        with pytest.raises(InferenceError, match="Native S2S failed"):
            adapter.speech_to_speech(b"some audio")

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.from_numpy")
    def test_speech_to_speech_resampling_normalization(
        self, mock_from_numpy, mock_cuda, adapter
    ):
        # Setup Moshi mock
        mock_moshi_model = MagicMock()
        moshi_cls = mock_moshi_models.Moshi  # noqa: F821
        moshi_cls.from_pretrained.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"

        mock_audio = MagicMock()
        segment_cls = mock_pydub_segment  # noqa: F821
        segment_cls.from_file.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.sample_width = 2
        mock_audio.get_array_of_samples.return_value = np.array([16384], dtype=np.int16)

        captured_samples = None

        def mock_fn(samples):
            nonlocal captured_samples
            captured_samples = samples
            m = MagicMock()
            m.unsqueeze.return_value = m
            m.to.return_value = m
            return m

        mock_from_numpy.side_effect = mock_fn

        mock_output_audio = MagicMock()
        mock_output_audio.detach.return_value = mock_output_audio
        mock_output_audio.cpu.return_value = mock_output_audio
        mock_output_audio.numpy.return_value = np.zeros((1, 100), dtype=np.float32)
        mock_moshi_model.generate.return_value = mock_output_audio

        adapter.speech_to_speech(b"audio")
        assert np.allclose(captured_samples, np.array([0.5], dtype=np.float32))

    def test_speech_to_speech_import_error(self, adapter):
        # We need to simulate a failure to import by shadowing the mocked sys.modules
        # but the adapter does 'from moshi.models import Moshi' which will see None and raise ImportError
        with patch.dict("sys.modules", {"moshi.models": None}):
            with pytest.raises(InferenceError, match="Moshi model not loaded"):
                adapter.speech_to_speech(b"audio")

    def test_speech_to_speech_cuda_not_available(self, adapter):
        with patch("torch.cuda.is_available", return_value=False):
            with pytest.raises(InferenceError, match="CUDA GPU is not available"):
                adapter.speech_to_speech(b"fake audio")


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

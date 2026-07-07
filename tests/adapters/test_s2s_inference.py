from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def mock_cuda_available():
    with patch("torch.cuda.is_available", return_value=True):
        yield


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Inject fresh mocks into sys.modules for moshi/pydub on every test.

    Creating new MagicMock objects per test avoids cross-test state leakage
    (e.g. side_effect set in one test persisting into the next).
    """
    _moshi = MagicMock()
    _moshi_models = MagicMock()
    _pydub = MagicMock()
    _pydub_segment = MagicMock()

    _pydub.AudioSegment = _pydub_segment
    _moshi_models.Moshi = MagicMock()

    # Expose on module globals so tests can reference them
    global mock_moshi, mock_moshi_models, mock_pydub, mock_pydub_segment
    mock_moshi = _moshi
    mock_moshi_models = _moshi_models
    mock_pydub = _pydub
    mock_pydub_segment = _pydub_segment

    with patch.dict(
        "sys.modules",
        {"moshi": _moshi, "moshi.models": _moshi_models, "pydub": _pydub},
    ):
        yield


from adapters.inference.audio_transformers_adapter import (  # noqa: E402
    AudioTransformersAdapter,
)  # noqa: E402
from core.domain.exceptions import InferenceError  # noqa: E402


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
        mock_moshi_models.Moshi.from_pretrained.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"

        # Setup AudioSegment mock
        mock_audio = MagicMock()
        mock_pydub_segment.from_file.return_value = mock_audio
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
        mock_pydub_segment.from_file.side_effect = Exception("Pydub crash")

        with pytest.raises(InferenceError, match="Native S2S failed"):
            adapter.speech_to_speech(b"some audio")

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.from_numpy")
    def test_speech_to_speech_resampling_normalization(
        self, mock_from_numpy, mock_cuda, adapter
    ):
        # Setup Moshi mock
        mock_moshi_model = MagicMock()
        mock_moshi_models.Moshi.from_pretrained.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"

        mock_audio = MagicMock()
        mock_pydub_segment.from_file.return_value = mock_audio
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

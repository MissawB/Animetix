import pytest
import io
import numpy as np
import torch
import sys
from unittest.mock import MagicMock, patch

# COMPLETELY Mock modules before any test execution
mock_moshi_model = MagicMock()
mock_audio = MagicMock()

from src.adapters.inference.transformers_adapter import TransformersAdapter
from core.domain.exceptions import InferenceError

class TestS2SInference:
    @pytest.fixture
    def adapter(self):
        adp = TransformersAdapter()
        if hasattr(adp, '_moshi_model'):
            del adp._moshi_model
        return adp

    @patch('moshi.models.Moshi.from_pretrained')
    @patch('pydub.AudioSegment.from_file')
    @patch('torch.cuda.is_available', return_value=False)
    @patch('torch.from_numpy')
    def test_speech_to_speech_success(self, mock_from_numpy, mock_cuda, mock_from_file, mock_moshi_fp, adapter):
        # Setup Moshi mock
        mock_moshi_fp.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"

        # Setup AudioSegment mock
        mock_from_file.return_value = mock_audio
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

    @patch('src.adapters.inference.transformers_adapter.TransformersAdapter._load_moshi_engine')
    def test_speech_to_speech_load_failure(self, mock_load, adapter):
        mock_load.side_effect = InferenceError("Moshi engine loading failed")
        with pytest.raises(InferenceError, match="Moshi engine loading failed"):
            adapter.speech_to_speech(b"some audio")

    @patch('pydub.AudioSegment.from_file')
    @patch('torch.cuda.is_available', return_value=False)
    def test_speech_to_speech_general_failure(self, mock_cuda, mock_from_file, adapter):
        adapter._moshi_model = MagicMock()
        mock_from_file.side_effect = Exception("Pydub crash")
        with pytest.raises(InferenceError, match="Native S2S failed"):
            adapter.speech_to_speech(b"some audio")

    @patch('moshi.models.Moshi.from_pretrained')
    @patch('pydub.AudioSegment.from_file')
    @patch('torch.cuda.is_available', return_value=False)
    @patch('torch.from_numpy')
    def test_speech_to_speech_resampling_normalization(self, mock_from_numpy, mock_cuda, mock_from_file, mock_moshi_fp, adapter):
        # Setup Moshi mock
        mock_moshi_fp.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"

        mock_from_file.return_value = mock_audio
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
        with patch.dict('sys.modules', {'moshi': None, 'moshi.models': None, 'pydub': None}):
            # This test might fail if pydub was already loaded, but it's a separate test
            with pytest.raises(InferenceError):
                adapter.speech_to_speech(b"audio")

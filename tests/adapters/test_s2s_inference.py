import pytest
import io
import numpy as np
import torch
import sys
from unittest.mock import MagicMock, patch

# Mock moshi before it's ever imported or used
mock_moshi_class = MagicMock()
mock_moshi_module = MagicMock()
mock_moshi_models_module = MagicMock()

# Inject into sys.modules
sys.modules['moshi'] = mock_moshi_module
sys.modules['moshi.models'] = mock_moshi_models_module
mock_moshi_models_module.Moshi = mock_moshi_class

from src.adapters.inference.transformers_adapter import TransformersAdapter
from core.domain.exceptions import InferenceError

class TestS2SInference:
    @pytest.fixture
    def adapter(self):
        # Create a fresh adapter and ensure any cached models are cleared
        adp = TransformersAdapter()
        if hasattr(adp, '_moshi_model'):
            del adp._moshi_model
        return adp

    @patch('pydub.AudioSegment.from_file')
    @patch('torch.cuda.is_available', return_value=False)
    def test_speech_to_speech_success(self, mock_cuda, mock_audio_from_file, adapter):
        # Setup AudioSegment mock
        mock_audio = MagicMock()
        mock_audio_from_file.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.sample_width = 2
        mock_audio.get_array_of_samples.return_value = np.zeros(24000, dtype=np.int16)
        
        # Setup Moshi mock
        mock_moshi_model = MagicMock()
        mock_moshi_class.from_pretrained.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"
        
        # Mock torch.from_numpy chain
        mock_input_tensor = MagicMock()
        torch.from_numpy.return_value = mock_input_tensor
        mock_input_tensor.unsqueeze.return_value = mock_input_tensor
        mock_input_tensor.to.return_value = mock_input_tensor
        
        # Mock output tensor chain to return real numpy array
        mock_output_tensor = MagicMock()
        mock_output_tensor.detach.return_value = mock_output_tensor
        mock_output_tensor.cpu.return_value = mock_output_tensor
        mock_output_tensor.numpy.return_value = np.zeros((1, 24000), dtype=np.float32)
        
        mock_moshi_model.generate.return_value = mock_output_tensor
        
        dummy_audio = b"dummy audio content"
        result = adapter.speech_to_speech(dummy_audio)
        
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify preprocessing
        mock_audio.set_frame_rate.assert_called_once_with(24000)
        mock_audio.set_channels.assert_called_once_with(1)
        
        # Verify Moshi call
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
        # Manually set the model to skip loading
        adapter._moshi_model = MagicMock()
        mock_from_file.side_effect = Exception("Pydub crash")
        
        with pytest.raises(InferenceError, match="Native S2S failed"):
            adapter.speech_to_speech(b"some audio")

    @patch('pydub.AudioSegment.from_file')
    @patch('torch.cuda.is_available', return_value=False)
    def test_speech_to_speech_resampling_normalization(self, mock_cuda, mock_audio_from_file, adapter):
        # Setup AudioSegment mock
        mock_audio = MagicMock()
        mock_audio_from_file.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.sample_width = 2 # 16-bit
        # 16384 is half of 32768, should normalize to 0.5
        mock_audio.get_array_of_samples.return_value = np.array([16384], dtype=np.int16)
        
        mock_moshi_model = MagicMock()
        mock_moshi_class.from_pretrained.return_value = mock_moshi_model
        mock_moshi_model.device = "cpu"
        
        # Capture input samples to from_numpy
        captured_samples = None
        def mock_from_numpy(samples):
            nonlocal captured_samples
            captured_samples = samples
            m = MagicMock()
            m.unsqueeze.return_value = m
            m.to.return_value = m
            return m
        
        torch.from_numpy.side_effect = mock_from_numpy
        
        # Mock output tensor chain to return real numpy array
        mock_output_tensor = MagicMock()
        mock_output_tensor.detach.return_value = mock_output_tensor
        mock_output_tensor.cpu.return_value = mock_output_tensor
        mock_output_tensor.numpy.return_value = np.zeros((1, 100), dtype=np.float32)
        mock_moshi_model.generate.return_value = mock_output_tensor
        
        adapter.speech_to_speech(b"audio")
        
        # Check normalization using numpy
        assert captured_samples is not None
        assert np.allclose(captured_samples, np.array([0.5], dtype=np.float32))

    def test_speech_to_speech_import_error(self, adapter):
        # Hide moshi to trigger ImportError
        with patch.dict('sys.modules', {'moshi': None, 'moshi.models': None}):
            with pytest.raises(InferenceError, match="Library 'moshi' or dependencies missing"):
                adapter.speech_to_speech(b"audio")

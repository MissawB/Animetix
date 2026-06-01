import pytest
from unittest.mock import MagicMock, patch
from pipeline.mlops.trl_ops import trl_ready_dataset, DPOConfig

def test_trl_ready_dataset_op():
    # Mock context for standard execution
    context = MagicMock()
    
    # Mocking the internal DPOFeedbackLoop to avoid DB/filesystem logic
    with patch("pipeline.mlops.trl_ops.DPOFeedbackLoop") as mock_loop_cls:
        mock_loop = mock_loop_cls.return_value
        
        # Simulate successful export
        config = DPOConfig(min_samples=10, export_filename="test_dpo.jsonl")
        
        # We need to mock os.path.exists to return True for the expected path
        with patch("os.path.exists", return_value=True):
             res = trl_ready_dataset(context, config=config)
             
        assert "test_dpo.jsonl" in res
        mock_loop.export_preference_dataset.assert_called_once()

import pytest
from unittest.mock import MagicMock, patch
from dagster import build_op_context
from pipeline.mlops.trl_ops import trl_ready_dataset, DPOConfig

def test_trl_ready_dataset_op():
    # Use build_op_context for Dagster ops
    context = build_op_context()
    
    # Mocking the internal DPOFeedbackLoop to avoid DB/filesystem logic
    with patch("pipeline.mlops.trl_ops.DPOFeedbackLoop") as mock_loop_cls:
        mock_loop = mock_loop_cls.return_value
        
        # Simulate successful export
        config = DPOConfig(min_samples=10, export_filename="test_dpo.jsonl")
        
        # We need to mock os.path.exists to return True for the expected path
        with patch("os.path.exists", return_value=True):
             # When using Pythonic Config, we don't pass it as an argument but via context/config if needed
             # or simply as a keyword argument if the op is called directly.
             # In Dagster 1.7+, direct calls with Pythonic Config work like this:
             res = trl_ready_dataset(context, config=config)
             
        assert "test_dpo.jsonl" in res
        mock_loop.export_preference_dataset.assert_called_once()

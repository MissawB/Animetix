from unittest.mock import MagicMock, patch

from pipeline.mlops.trl_ops import DPOConfig, trl_ready_dataset


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
        # The pipeline DPOFeedbackLoop exposes `process_and_export(raw_data_path,
        # output_path)` — NOT `export_preference_dataset` (that's the core service).
        mock_loop.process_and_export.assert_called_once()
        _, kwargs = mock_loop.process_and_export.call_args
        assert kwargs["output_path"].endswith("test_dpo.jsonl")

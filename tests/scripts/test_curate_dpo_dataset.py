from unittest.mock import MagicMock, patch

from scripts.curation.curate_dpo_dataset import curate_dpo_dataset


@patch("scripts.curation.curate_dpo_dataset.AIFeedback")
@patch("scripts.curation.curate_dpo_dataset.get_container")
@patch("scripts.curation.curate_dpo_dataset.DPOFeedbackLoop")
@patch("builtins.open", new_callable=MagicMock)
def test_curate_dpo_dataset_flow(
    mock_open, mock_loop_class, mock_get_container, mock_feedback
):
    # Setup mocks
    mock_fb = MagicMock(spec=["input_context", "output_text", "is_positive", "id"])
    mock_fb.input_context = "test query"
    mock_fb.output_text = "bad answer"
    mock_fb.is_positive = False
    mock_fb.id = 1

    mock_queryset = MagicMock()
    mock_queryset.__iter__.return_value = [mock_fb]
    mock_queryset.exists.return_value = True

    mock_feedback.objects.filter.return_value = mock_queryset

    mock_container = MagicMock()
    mock_get_container.return_value = mock_container
    mock_rag = mock_container.agentic_rag.return_value
    mock_rag.plan_and_solve.return_value = "perfect answer"

    mock_loop = mock_loop_class.return_value
    mock_loop.validate_feedback.return_value = True
    mock_loop.create_dpo_pair.return_value = {
        "prompt": "...",
        "chosen": "perfect answer",
        "rejected": "bad answer",
    }

    # Run curation
    curate_dpo_dataset()

    # Verify calls
    mock_rag.plan_and_solve.assert_called_with("test query", "Anime")
    mock_loop.validate_feedback.assert_called()
    mock_loop.create_dpo_pair.assert_called_with(
        {"context": "test query", "output": "bad answer", "is_positive": False},
        chosen_override="perfect answer",
    )
    assert mock_open.called

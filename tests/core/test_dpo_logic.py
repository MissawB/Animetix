import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop

@patch("animetix.models.AIFeedback")
@patch("animetix.models.GoldDatasetEntry")
def test_curate_feedback_success(mock_gold, mock_feedback):
    feedback_port = MagicMock()
    # Mock finding feedback
    feedback_port.get_recent_feedback.return_value = [{"id": 123, "input_context": "q", "output_text": "bad"}]
    
    # Mock AIFeedback.objects.get
    mock_fb = MagicMock()
    mock_fb.input_context = "q"
    mock_feedback.objects.get.return_value = mock_fb
    
    loop = DPOFeedbackLoop(feedback_port=feedback_port)
    
    result = loop.curate_feedback(feedback_id=123, chosen_text="perfect response")
    
    assert result is True
    mock_feedback.objects.get.assert_called_once_with(id=123)
    mock_gold.objects.update_or_create.assert_called_once()

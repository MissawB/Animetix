import pytest
from django.urls import reverse
from animetix.models import AIFeedback
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_submit_ai_feedback_with_input_context(client):
    """Test that the view extracts input_context and output_text correctly."""
    url = reverse('submit_ai_feedback')
    data = {
        'type': 'test',
        'input_context': 'full truth path',
        'output_text': 'the generated answer',
        'is_positive': 'true'
    }
    response = client.post(url, data)
    assert response.status_code == 200
    
    feedback = AIFeedback.objects.last()
    assert feedback.input_context == 'full truth path'
    assert feedback.output_text == 'the generated answer'

@pytest.mark.django_db
def test_submit_ai_feedback_fallback_to_context(client):
    """Test that the view falls back to 'context' and 'output' if preferred names are missing."""
    url = reverse('submit_ai_feedback')
    data = {
        'type': 'test',
        'context': 'legacy context',
        'output': 'legacy output',
        'is_positive': 'false'
    }
    response = client.post(url, data)
    assert response.status_code == 200
    
    feedback = AIFeedback.objects.last()
    assert feedback.input_context == 'legacy context'
    assert feedback.output_text == 'legacy output'

@pytest.mark.django_db
def test_submit_ai_feedback_fallback_to_query(client):
    """Test that the view falls back to 'query' if 'context' is also missing."""
    url = reverse('submit_ai_feedback')
    data = {
        'type': 'test',
        'query': 'user query',
        'output': 'answer',
        'is_positive': 'true'
    }
    response = client.post(url, data)
    assert response.status_code == 200
    
    feedback = AIFeedback.objects.last()
    assert feedback.input_context == 'user query'

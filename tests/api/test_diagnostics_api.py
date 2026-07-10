from unittest.mock import MagicMock, patch

import pytest
from animetix.containers import get_container
from core.domain.entities.ai_schemas import (
    InferenceMetadata,
    InferenceResponse,
    TokenLogProb,
)
from rest_framework.test import APIClient

# The requests traverse the full middleware stack (session/profile lookups),
# which needs DB access even with the container and billing mocked out.
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


def test_neural_diagnostics_api_success(api_client):
    url = "/api/v1/labs/diagnostics/"
    payload = {"prompt": "Why is Naruto a ninja?"}
    # GPU feature → login required + consumes Berrix (mocked so no wallet needed).
    api_client.force_authenticate(user=MagicMock(id=1))

    mock_inference = MagicMock()
    mock_xai = MagicMock()

    # Mock Inference Response
    mock_response = InferenceResponse(
        text="Naruto trained hard.",
        metadata=InferenceMetadata(
            logprobs=[TokenLogProb(token="Naruto", logprob=-0.1)]
        ),
    )
    mock_inference.generate.return_value = mock_response

    # Mock XAI Report
    mock_report = {
        "avg_entropy": 0.5,
        "confidence_score": 0.9,
        "per_token_diagnostics": [],
        "logit_lens_trajectory": [],
    }
    mock_xai.get_diagnostics_report.return_value = mock_report

    container = get_container()
    container.inference.inference_engine.override(mock_inference)
    container.core.xai_service.override(mock_xai)
    try:
        with patch("animetix.api.labs.singularity.deduct_berrix"):
            # We use the string URL because the name might not be registered yet
            response = api_client.post(url, payload, format="json")
    finally:
        container.inference.inference_engine.reset_last_overriding()
        container.core.xai_service.reset_last_overriding()

    assert response.status_code == 200
    assert "avg_entropy" in response.data
    assert response.data["avg_entropy"] == 0.5

    # Verify calls
    mock_inference.generate.assert_called_once()
    _, kwargs = mock_inference.generate.call_args
    assert kwargs.get("include_logprobs") is True
    mock_xai.get_diagnostics_report.assert_called_once_with(
        payload["prompt"], mock_response
    )


def test_neural_diagnostics_api_missing_prompt(api_client):
    url = "/api/v1/labs/diagnostics/"
    api_client.force_authenticate(user=MagicMock(id=1))  # login required (GPU feature)
    response = api_client.post(url, {}, format="json")
    assert response.status_code == 400
    assert "error" in response.data

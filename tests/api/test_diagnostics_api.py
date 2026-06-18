import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from core.domain.entities.ai_schemas import (
    InferenceResponse,
    InferenceMetadata,
    TokenLogProb,
)


@pytest.fixture
def api_client():
    return APIClient()


def test_neural_diagnostics_api_success(api_client):
    url = "/api/v1/labs/diagnostics/"
    payload = {"prompt": "Why is Naruto a ninja?"}

    with patch("animetix.api.labs.get_container") as mock_get_container:
        mock_container = MagicMock()
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

        mock_container.inference.inference_engine.return_value = mock_inference
        mock_container.core.xai_service.return_value = mock_xai
        mock_get_container.return_value = mock_container

        # We use the string URL because the name might not be registered yet
        response = api_client.post(url, payload, format="json")

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
    response = api_client.post(url, {}, format="json")
    assert response.status_code == 400
    assert "error" in response.data

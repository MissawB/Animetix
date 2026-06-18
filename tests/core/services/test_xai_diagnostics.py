from unittest.mock import MagicMock
from core.domain.services.xai_service import XaiDiagnosticService
from core.domain.entities.ai_schemas import (
    InferenceResponse,
    InferenceMetadata,
    TokenLogProb,
)


def test_get_diagnostics_report_structure():
    # Setup
    inference_port = MagicMock()
    service = XaiDiagnosticService(inference_engine=inference_port)

    # Mock Response with logprobs
    logprobs = [
        TokenLogProb(token="Hello", logprob=-0.1),
        TokenLogProb(token="World", logprob=-0.5),
    ]
    response = InferenceResponse(
        text="Hello World", metadata=InferenceMetadata(logprobs=logprobs)
    )

    # Execution
    report = service.get_diagnostics_report("Hello", response)

    # Assertions
    assert "avg_entropy" in report
    assert isinstance(report["avg_entropy"], float)

    assert "confidence_score" in report
    assert isinstance(report["confidence_score"], float)

    assert "per_token_diagnostics" in report
    assert isinstance(report["per_token_diagnostics"], list)
    assert len(report["per_token_diagnostics"]) == 2
    assert "token" in report["per_token_diagnostics"][0]
    assert "entropy" in report["per_token_diagnostics"][0]
    assert "logprob" in report["per_token_diagnostics"][0]

    assert "logit_lens_trajectory" in report
    assert isinstance(report["logit_lens_trajectory"], list)
    assert len(report["logit_lens_trajectory"]) == 32
    assert "layer" in report["logit_lens_trajectory"][0]
    assert "top_tokens" in report["logit_lens_trajectory"][0]
    assert "internal_probabilities" in report["logit_lens_trajectory"][0]

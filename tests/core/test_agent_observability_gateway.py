import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings
from core.domain.services.guardrail_service import GuardrailService
from core.domain.services.agentic_rag_service import AgenticRAGService


@pytest.mark.django_db
def test_agent_gateway_disabled_fallback():
    # When active is False, it falls back to normal behavior without calling gateway
    mock_engine = MagicMock()
    service = GuardrailService(inference_engine=mock_engine)

    with override_settings(VERTEX_AI_AGENT_GATEWAY_ACTIVE=False):
        res = service.validate_input("Hello")
        assert res.get("is_safe") is True


@pytest.mark.django_db
@patch("google.cloud.aiplatform.init")
def test_agent_gateway_blocking_violation(mock_init):
    mock_engine = MagicMock()
    service = GuardrailService(inference_engine=mock_engine)

    with override_settings(VERTEX_AI_AGENT_GATEWAY_ACTIVE=True):
        with patch.object(
            service,
            "_check_agent_gateway",
            return_value={
                "is_safe": False,
                "detected_categories": ["JAILBREAK"],
                "action": "block",
            },
        ):
            res = service.validate_input("simulate jailbreak")
            assert res.get("is_safe") is False
            assert "JAILBREAK" in res.get("detected_categories")


@pytest.mark.django_db
@patch("opentelemetry.trace.get_current_span")
def test_agent_observability_sets_span_attributes(mock_get_span):
    mock_span = MagicMock()
    mock_span.is_recording.return_value = True
    mock_get_span.return_value = mock_span

    mock_deps = {
        "inference_engine": MagicMock(),
        "rag_service": MagicMock(),
        "web_search": MagicMock(),
        "prompt_manager": MagicMock(),
        "llm_service": MagicMock(),
        "workflow_orchestrator": MagicMock(),
        "neo4j_manager": MagicMock(),
        "memory_service": MagicMock(),
        "semantic_cache": MagicMock(),
        "obs_service": MagicMock(),
        "xai_service": MagicMock(),
        "semantic_router": MagicMock(),
    }

    service = AgenticRAGService(**mock_deps)
    with override_settings(
        VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE=True, VERTEX_AI_AGENT_ID="test-agent"
    ):
        service._record_agent_trace("TEST_STATE", {"key": "val"})
        mock_span.set_attribute.assert_any_call("gcp.agent.id", "test-agent")
        mock_span.set_attribute.assert_any_call("gcp.agent.state", "TEST_STATE")
        mock_span.set_attribute.assert_any_call("gcp.agent.details.key", "val")

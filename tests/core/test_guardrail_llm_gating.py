from unittest.mock import MagicMock


def _svc():
    from core.domain.services.guardrail_service import GuardrailService

    safety = MagicMock()
    # Force le chemin "stub" qui déclencherait normalement le fallback LLM
    safety.moderate_content.return_value = {"is_safe": True, "detected_categories": []}
    svc = GuardrailService(
        safety_engine=safety, prompt_manager=None, inference_engine=MagicMock()
    )
    svc._llm_moderate = MagicMock(
        return_value={"is_safe": True, "detected_categories": ["X"]}
    )
    svc._check_agent_gateway = MagicMock(return_value=None)
    svc._is_potential_jailbreak = MagicMock(return_value=False)
    return svc


def test_allow_llm_false_skips_llm_moderation():
    svc = _svc()
    svc.validate_input("some query", allow_llm=False)
    svc._llm_moderate.assert_not_called()


def test_allow_llm_true_uses_llm_fallback():
    svc = _svc()
    svc.validate_input("some query", allow_llm=True)
    svc._llm_moderate.assert_called_once()

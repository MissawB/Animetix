"""Tests du registre ConfigPort (isolation des settings Django hors du core)."""

import core.config as core_config
from core.ports.config_port import ConfigPort, EnvConfig


def test_envconfig_reads_environment(monkeypatch):
    monkeypatch.setenv("ANIMETIX_TEST_KEY", "value42")
    cfg = EnvConfig()
    assert cfg.get("ANIMETIX_TEST_KEY") == "value42"
    assert cfg.get("ANIMETIX_ABSENT", "fallback") == "fallback"


def test_registry_configure_and_restore():
    original = core_config.get_config()
    try:

        class _Fake(ConfigPort):
            def get(self, key, default=None):
                return {"FLAG": True}.get(key, default)

        core_config.configure(_Fake())
        assert core_config.get_config().get("FLAG") is True
        assert core_config.get_config().get("MISSING", 7) == 7
    finally:
        core_config.configure(original)


def test_guardrail_uses_injected_config():
    """GuardrailService lit ses flags via le ConfigPort injecté, sans Django."""
    from unittest.mock import MagicMock

    from core.domain.services.guardrail_service import GuardrailService

    class _Cfg(ConfigPort):
        def get(self, key, default=None):
            return True if key == "VERTEX_AI_AGENT_GATEWAY_ACTIVE" else default

    svc = GuardrailService(inference_engine=MagicMock(), config_port=_Cfg())
    # Gateway actif -> la passerelle est consultée et retourne None (aucune violation simulée)
    assert svc._check_agent_gateway("texte", mode="input") is None

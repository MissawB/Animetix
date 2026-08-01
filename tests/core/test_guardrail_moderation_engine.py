"""La modération tourne sur son propre moteur, avec repli sur le principal.

Le prompt taillé (`output_moderator`) ne bouge pas : seul le moteur qui l'exécute
change. Et si le petit modèle manque -- typiquement quand le web est déployé mais
que l'image brain n'a pas été reconstruite -- on retombe sur le moteur principal,
jamais en fail-open silencieux.
"""

import json
from unittest.mock import MagicMock

from core.domain.services.guardrail_service import GuardrailService


def _engine(text):
    engine = MagicMock()
    engine.generate.return_value = MagicMock(text=text)
    return engine


SAFE = json.dumps({"is_safe": True, "detected_categories": [], "reasoning": "ok"})


def test_moderation_defaults_to_the_main_engine():
    main = _engine(SAFE)
    svc = GuardrailService(inference_engine=main)
    svc._llm_moderate("texte", ["SPOILER"])
    main.generate.assert_called_once()


def test_moderation_uses_the_dedicated_engine_when_provided():
    main, moderator = _engine(SAFE), _engine(SAFE)
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)
    result = svc._llm_moderate("texte", ["SPOILER"])
    moderator.generate.assert_called_once()
    main.generate.assert_not_called()
    assert result["is_safe"] is True


def test_moderation_falls_back_to_the_main_engine_when_the_moderator_fails():
    main = _engine(SAFE)
    moderator = MagicMock()
    moderator.generate.side_effect = RuntimeError("model not served")
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)
    result = svc._llm_moderate("texte", ["SPOILER"])
    main.generate.assert_called_once()
    assert result["is_safe"] is True

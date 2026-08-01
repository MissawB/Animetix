"""La modération tourne sur son propre moteur, avec repli sur le principal.

Le prompt taillé (`output_moderator`) ne bouge pas : seul le moteur qui l'exécute
change. Et si le petit modèle ne rend pas de verdict exploitable -- soit qu'il
manque (le web déployé sans reconstruction de l'image brain), soit qu'il réponde
en prose -- on retombe sur le moteur principal, jamais en fail-open silencieux.

Les tests qui passent par `validate_input` / `validate_output` ne sont pas des
doublons de ceux qui appellent `_llm_moderate` : la posture d'échec (fail-open
par défaut, marqué `degraded`) vit dans les premiers, et c'est là qu'une
modération sautée peut se déguiser en modération passée.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from core.domain.exceptions import ContentModerationError
from core.domain.services.guardrail_service import GuardrailService
from core.ports.inference_port import (
    MODERATION_SOURCE_KEYWORDS,
    MODERATION_SOURCE_MODEL,
)


def _engine(text):
    engine = MagicMock()
    engine.generate.return_value = MagicMock(text=text)
    return engine


SAFE = json.dumps({"is_safe": True, "detected_categories": [], "reasoning": "ok"})
SPOILER = json.dumps(
    {"is_safe": False, "detected_categories": ["SPOILER"], "reasoning": "fin révélée"}
)
# Ce que rend un petit modèle non contraint une fois sur N : une réponse, pas un
# verdict. `json.loads` la refuse, et sans repli l'appelant la traiterait comme
# une panne moteur -- donc comme un « rien à signaler ».
PROSE = "Le texte semble sûr."


def _config(flags):
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: flags.get(key, default)
    return config


# --- Choix du moteur ---------------------------------------------------------


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


def test_moderation_asks_for_constrained_json():
    """Sans `json_mode`, l'adaptateur génère à 0.7 sans `response_format` : c'est
    précisément ce qui fabrique les réponses en prose que le repli doit rattraper."""
    moderator = _engine(SAFE)
    GuardrailService(
        inference_engine=_engine(SAFE), moderation_engine=moderator
    )._llm_moderate("texte", ["SPOILER"])
    assert moderator.generate.call_args.kwargs["json_mode"] is True


# --- Repli : appel en échec ET réponse illisible ------------------------------


def test_moderation_falls_back_to_the_main_engine_when_the_moderator_fails():
    main = _engine(SAFE)
    moderator = MagicMock()
    moderator.generate.side_effect = RuntimeError("model not served")
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)
    result = svc._llm_moderate("texte", ["SPOILER"])
    main.generate.assert_called_once()
    assert result["is_safe"] is True


def test_moderation_falls_back_when_the_moderator_answers_prose():
    main, moderator = _engine(SPOILER), _engine(PROSE)
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)

    result = svc._llm_moderate("texte", ["SPOILER"])

    main.generate.assert_called_once()
    assert result["is_safe"] is False
    assert "SPOILER" in result["detected_categories"]


def test_moderation_falls_back_when_the_moderator_answers_truncated_json():
    main, moderator = _engine(SAFE), _engine('{"is_safe": tru')
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)
    assert svc._llm_moderate("texte", ["SPOILER"])["is_safe"] is True
    main.generate.assert_called_once()


def test_without_a_dedicated_engine_unreadable_output_still_raises():
    """Posture inchangée là où il n'y a rien à quoi se replier."""
    svc = GuardrailService(inference_engine=_engine(PROSE))
    with pytest.raises(ContentModerationError):
        svc._llm_moderate("texte", ["SPOILER"])


# --- Chemin assemblé : validate_output ----------------------------------------


def test_validate_output_runs_on_the_dedicated_engine():
    main, moderator = _engine(SAFE), _engine(SPOILER)
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)

    result = svc.validate_output("Le héros meurt à la fin.")

    moderator.generate.assert_called_once()
    main.generate.assert_not_called()
    assert result["action"] == "mask"


def test_validate_output_prose_from_the_moderator_is_not_a_silent_pass():
    """Le cas qui motive tout : un modérateur qui répond en prose ne doit pas
    ressortir en `is_safe: True` sans que le repli ait été tenté."""
    main, moderator = _engine(SPOILER), _engine(PROSE)
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)

    result = svc.validate_output("Le héros meurt à la fin.")

    main.generate.assert_called_once()  # le repli a bien eu lieu
    assert result["is_safe"] is False
    assert result["action"] == "mask"
    assert not result.get("degraded")


def test_validate_output_both_engines_unreadable_flags_degraded():
    # Repli tenté et lui aussi illisible : fail-open par défaut, mais marqué --
    # « contrôle sauté » doit rester distinguable de « contrôle passé ».
    main, moderator = _engine(PROSE), _engine(PROSE)
    svc = GuardrailService(inference_engine=main, moderation_engine=moderator)

    result = svc.validate_output("réponse quelconque")

    main.generate.assert_called_once()
    assert result["is_safe"] is True
    assert result["degraded"] is True


def test_validate_output_both_engines_unreadable_blocks_when_fail_closed():
    main, moderator = _engine(PROSE), _engine(PROSE)
    svc = GuardrailService(
        inference_engine=main,
        moderation_engine=moderator,
        config_port=_config({"GUARDRAIL_FAIL_CLOSED": "true"}),
    )

    result = svc.validate_output("réponse quelconque")

    assert result["is_safe"] is False
    assert result["action"] == "block"
    assert result["degraded"] is True


# --- Chemin assemblé : validate_input -----------------------------------------


def _safety(verdict):
    safety = MagicMock()
    safety.moderate_content.return_value = verdict
    return safety


def _input_svc(verdict, moderator_text=SAFE):
    moderator = _engine(moderator_text)
    svc = GuardrailService(
        inference_engine=_engine(SAFE),
        moderation_engine=moderator,
        safety_engine=_safety(verdict),
    )
    return svc, moderator


def test_a_real_first_stage_verdict_costs_a_single_moderation_call():
    """Le premier étage modère pour de bon depuis qu'il parle au brain : son
    verdict fait autorité, au lieu de payer une seconde passe identique."""
    svc, moderator = _input_svc(
        {
            "is_safe": True,
            "detected_categories": [],
            "action": "allow",
            "source": MODERATION_SOURCE_MODEL,
        }
    )

    result = svc.validate_input("quel est le meilleur anime de 2026 ?")

    moderator.generate.assert_not_called()
    assert result["is_safe"] is True


def test_an_unsafe_first_stage_verdict_still_blocks():
    svc, moderator = _input_svc(
        {
            "is_safe": False,
            "detected_categories": ["HATE_SPEECH"],
            "action": "block",
            "source": MODERATION_SOURCE_MODEL,
        }
    )

    result = svc.validate_input("texte haineux")

    assert result["is_safe"] is False
    assert result["action"] == "block"
    assert "HATE_SPEECH" in result["detected_categories"]
    moderator.generate.assert_not_called()


def test_a_keyword_fallback_verdict_is_not_trusted():
    """`is_safe: True` d'un repli par mots-clés ne veut dire que « aucun mot de la
    liste » : le contrôle sémantique reste à faire."""
    svc, moderator = _input_svc(
        {
            "is_safe": True,
            "detected_categories": [],
            "action": "allow",
            "source": MODERATION_SOURCE_KEYWORDS,
            "degraded": True,
        },
        moderator_text=SPOILER,
    )

    result = svc.validate_input("une question")

    moderator.generate.assert_called_once()
    assert result["is_safe"] is False


def test_a_verdict_without_provenance_is_not_trusted():
    # Adaptateur ou image brain d'une version antérieure : preuve manquante, pas
    # bonne nouvelle -- on repasse par la modération fine, comme avant.
    svc, moderator = _input_svc(
        {"is_safe": True, "detected_categories": []}, moderator_text=SPOILER
    )

    result = svc.validate_input("une question")

    moderator.generate.assert_called_once()
    assert result["is_safe"] is False


def test_a_missing_first_stage_result_is_not_trusted():
    svc, moderator = _input_svc(None, moderator_text=SPOILER)

    result = svc.validate_input("une question")

    moderator.generate.assert_called_once()
    assert result["is_safe"] is False


def test_a_first_stage_verdict_missing_the_is_safe_key_is_not_trusted():
    """Reproduit le vrai bug, pas une version rejouée à la main : le
    `safety_engine` est un véritable `InferencePort` dont `moderate_content`
    construit lui-même le verdict, à partir d'un JSON bien formé qui omet
    `is_safe` (plausible venant d'un modèle 1.5B). `res.get("is_safe", True)`
    ne doit pas se voir marqué `source: model` -- sinon un contrôle sauté a
    l'allure d'un contrôle passé et la seconde passe (`_llm_moderate`) est
    sautée à tort."""
    safety = UnifiedInferenceAdapter(
        api_base="http://fake-url", model_name="fake-model"
    )
    moderator = _engine(SPOILER)
    svc = GuardrailService(
        inference_engine=_engine(SAFE),
        moderation_engine=moderator,
        safety_engine=safety,
    )

    with patch.object(
        safety,
        "generate",
        return_value='{"detected_categories": [], "reason": "pas de verdict"}',
    ):
        result = svc.validate_input("une question")

    moderator.generate.assert_called_once()
    assert result["is_safe"] is False

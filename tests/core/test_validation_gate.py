"""Behavior tests for SyntheticValidationService, the universal HITL gate
(was 0% covered while staging every synthetic gold-dataset entry)."""

import json
from unittest.mock import MagicMock

import pytest
from core.domain.services.validation_gate import SyntheticValidationService


@pytest.fixture
def engine():
    eng = MagicMock()
    eng.generate.return_value.text = json.dumps(
        {"critique": "Réponse fidèle au contexte.", "score": 0.85}
    )
    return eng


@pytest.fixture
def gold_port():
    port = MagicMock()
    port.save_synthetic_entry.return_value = 123
    return port


@pytest.fixture
def guardrail():
    g = MagicMock()
    g.validate_output.return_value = {"is_safe": True}
    return g


@pytest.fixture
def xai():
    x = MagicMock()
    x.measure_confidence.return_value = {"confidence_score": 0.9}
    return x


@pytest.fixture
def gate(engine, gold_port, guardrail, xai):
    return SyntheticValidationService(
        inference_engine=engine,
        gold_dataset_port=gold_port,
        guardrail_service=guardrail,
        xai_service=xai,
    )


def _staged_kwargs(gold_port):
    return gold_port.save_synthetic_entry.call_args.kwargs


def test_safe_entry_staged_with_critique_score(gate, gold_port):
    entry_id = gate.validate_and_stage(
        entry_type="qa",
        context="One Piece est un manga d'Eiichiro Oda.",
        instruction="Qui a écrit One Piece ?",
        response="Eiichiro Oda.",
    )

    assert entry_id == 123
    kwargs = _staged_kwargs(gold_port)
    assert kwargs["entry_type"] == "qa"
    assert kwargs["ai_validation_score"] == 0.85
    assert kwargs["confidence_score"] == 0.9
    assert kwargs["is_safe"] is True
    assert "fidèle" in kwargs["ai_critique"]


def test_unsafe_entry_caps_score_and_prefixes_critique(gate, guardrail, gold_port):
    guardrail.validate_output.return_value = {
        "is_safe": False,
        "reason": "Spoiler majeur détecté.",
    }

    gate.validate_and_stage(
        entry_type="qa", context="ctx", instruction="q", response="r"
    )

    kwargs = _staged_kwargs(gold_port)
    assert kwargs["is_safe"] is False
    assert kwargs["ai_validation_score"] <= 0.2
    assert kwargs["ai_critique"].startswith("🚨 SAFETY RISK: Spoiler majeur détecté.")


def test_critique_engine_failure_falls_back_to_neutral_score(gate, engine, gold_port):
    engine.generate.side_effect = RuntimeError("LLM down")

    gate.validate_and_stage(
        entry_type="qa", context="ctx", instruction="q", response="r"
    )

    kwargs = _staged_kwargs(gold_port)
    assert kwargs["ai_validation_score"] == 0.5
    assert "Critique engine failure" in kwargs["ai_critique"]


def test_fenced_json_critique_is_parsed(gate, engine, gold_port):
    engine.generate.return_value.text = (
        'Voici mon analyse :\n```json\n{"critique": "OK", "score": 0.7}\n```'
    )

    gate.validate_and_stage(
        entry_type="qa", context="ctx", instruction="q", response="r"
    )

    assert _staged_kwargs(gold_port)["ai_validation_score"] == 0.7


def test_prose_wrapped_json_is_extracted(gate, engine, gold_port):
    engine.generate.return_value.text = (
        'Analyse : {"critique": "Bien.", "score": 0.6} — fin.'
    )

    gate.validate_and_stage(
        entry_type="qa", context="ctx", instruction="q", response="r"
    )

    assert _staged_kwargs(gold_port)["ai_validation_score"] == 0.6


def test_missing_confidence_defaults_to_zero(gate, xai, gold_port):
    xai.measure_confidence.return_value = {}

    gate.validate_and_stage(
        entry_type="qa", context="ctx", instruction="q", response="r"
    )

    assert _staged_kwargs(gold_port)["confidence_score"] == 0.0


def test_guardrail_receives_full_triplet(gate, guardrail):
    gate.validate_and_stage(
        entry_type="qa",
        context="le contexte",
        instruction="la question",
        response="la réponse",
    )

    guardrail.validate_output.assert_called_once_with(
        "la réponse", context="le contexte", query="la question"
    )

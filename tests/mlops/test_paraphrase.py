# -*- coding: utf-8 -*-
"""Tests hermétiques de ft_dataset/paraphrase.py (46 % → reliquat audit 2026-07-19).

Aucun appel réseau : le « client » Gemini est un faux objet ; le cache disque
est redirigé vers tmp_path ; time.sleep est neutralisé.
"""

import json
import os
import sys
from unittest.mock import MagicMock

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "pipeline", "mlops"))

from pipeline.mlops.ft_dataset import paraphrase  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_cache_and_no_sleep(tmp_path, monkeypatch):
    """Cache vidé + fichier cache en tmp + sleeps neutralisés pour chaque test."""
    monkeypatch.setattr(paraphrase, "CACHE_FILE", str(tmp_path / "cache.json"))
    monkeypatch.setattr(paraphrase, "PARAPHRASE_CACHE", {})
    monkeypatch.setattr(paraphrase.time, "sleep", lambda _s: None)


def _fake_client(reply_text):
    """Client Gemini factice dont generate_content renvoie reply_text."""
    client = MagicMock(name="genai_client")
    response = MagicMock()
    response.text = reply_text
    client.models.generate_content.return_value = response
    return client


# --- paraphrase_text_via_gemini ---------------------------------------------


def test_paraphrase_passthrough_without_client_or_text():
    assert paraphrase.paraphrase_text_via_gemini("", None) == ""
    assert paraphrase.paraphrase_text_via_gemini("Goku est un Saiyan.", None) == (
        "Goku est un Saiyan."
    )


def test_paraphrase_cache_hit_short_circuits_client():
    client = _fake_client("ne doit jamais être appelé")
    paraphrase.PARAPHRASE_CACHE["Goku est un Saiyan.||naturel"] = "cached!"

    out = paraphrase.paraphrase_text_via_gemini("Goku est un Saiyan.", client)

    assert out == "cached!"
    client.models.generate_content.assert_not_called()


def test_paraphrase_success_is_validated_then_cached(monkeypatch):
    monkeypatch.setattr(
        paraphrase, "validate_factual_alignment", lambda *_a, **_k: True
    )
    client = _fake_client("  Goku appartient au peuple Saiyan.  ")

    out = paraphrase.paraphrase_text_via_gemini("Goku est un Saiyan.", client)

    assert out == "Goku appartient au peuple Saiyan."
    # Mise en cache : le second appel ne re-consulte pas le client.
    out2 = paraphrase.paraphrase_text_via_gemini("Goku est un Saiyan.", client)
    assert out2 == out
    assert client.models.generate_content.call_count == 1


def test_paraphrase_misaligned_result_falls_back_to_original(monkeypatch):
    monkeypatch.setattr(
        paraphrase, "validate_factual_alignment", lambda *_a, **_k: False
    )
    client = _fake_client("Goku est un Namek.")  # hallucination

    out = paraphrase.paraphrase_text_via_gemini("Goku est un Saiyan.", client)

    assert out == "Goku est un Saiyan."
    assert "Goku est un Saiyan.||naturel" not in paraphrase.PARAPHRASE_CACHE


def test_paraphrase_rate_limit_retries_three_times_then_returns_original(monkeypatch):
    sleeps = []
    monkeypatch.setattr(paraphrase.time, "sleep", sleeps.append)
    client = MagicMock(name="genai_client")
    client.models.generate_content.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED")

    out = paraphrase.paraphrase_text_via_gemini("Goku est un Saiyan.", client)

    assert out == "Goku est un Saiyan."
    assert client.models.generate_content.call_count == 3
    # Backoff rate-limit : 15s puis 30s (puis 45s pour la dernière tentative).
    assert sleeps == [15.0, 30.0, 45.0]


# --- translate_to_english_via_gemini -----------------------------------------


def test_translate_passthrough_and_validated_success(monkeypatch):
    assert paraphrase.translate_to_english_via_gemini("", None) == ""
    assert paraphrase.translate_to_english_via_gemini("Bonjour", None) == "Bonjour"

    monkeypatch.setattr(
        paraphrase, "validate_factual_alignment", lambda *_a, **_k: True
    )
    client = _fake_client("Goku is a Saiyan.")
    assert (
        paraphrase.translate_to_english_via_gemini("Goku est un Saiyan.", client)
        == "Goku is a Saiyan."
    )


def test_translate_misaligned_returns_original(monkeypatch):
    monkeypatch.setattr(
        paraphrase, "validate_factual_alignment", lambda *_a, **_k: False
    )
    client = _fake_client("Goku is a Namekian.")
    assert (
        paraphrase.translate_to_english_via_gemini("Goku est un Saiyan.", client)
        == "Goku est un Saiyan."
    )


# --- validate_factual_alignment ----------------------------------------------


def test_validate_defaults():
    assert paraphrase.validate_factual_alignment("", "généré", None) is False
    assert paraphrase.validate_factual_alignment("original", "", None) is False
    # Sans client : on valide par défaut.
    assert paraphrase.validate_factual_alignment("original", "généré", None) is True


def test_validate_parses_fenced_json_verdict():
    client = _fake_client(
        '```json\n{"aligned": false, "reason": "studio inventé"}\n```'
    )
    assert paraphrase.validate_factual_alignment("a", "b", client) is False

    client = _fake_client('{"aligned": true, "reason": ""}')
    assert paraphrase.validate_factual_alignment("a", "b", client) is True


def test_validate_trusts_by_default_when_judge_is_broken():
    client = _fake_client("pas du JSON")
    assert paraphrase.validate_factual_alignment("a", "b", client) is True
    assert client.models.generate_content.call_count == 2  # 2 tentatives


# --- cache disque -------------------------------------------------------------


def test_cache_roundtrip_on_disk(tmp_path):
    paraphrase.PARAPHRASE_CACHE["clef||naturel"] = "valeur"
    paraphrase.save_paraphrase_cache()

    saved = json.loads(
        open(paraphrase.CACHE_FILE, encoding="utf-8").read()  # noqa: SIM115
    )
    assert saved == {"clef||naturel": "valeur"}

    paraphrase.PARAPHRASE_CACHE.clear()
    paraphrase.load_paraphrase_cache()
    assert paraphrase.PARAPHRASE_CACHE == {"clef||naturel": "valeur"}


def test_load_cache_survives_corrupt_file():
    with open(paraphrase.CACHE_FILE, "w", encoding="utf-8") as f:
        f.write("{pas du json")
    paraphrase.load_paraphrase_cache()
    assert paraphrase.PARAPHRASE_CACHE == {}

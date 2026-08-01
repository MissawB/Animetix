"""Le brain sert le modèle demandé, et seulement s'il le sert vraiment.

Un client qui choisit un modèle arbitraire pourrait faire télécharger n'importe
quoi à un service GPU ; un tag non registré, lui, part en 404 Ollama que rien ne
distingue d'une panne. Les deux se règlent en n'acceptant que les tags présents
dans /api/tags.
"""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

# brain_service.py appelle sys.exit(1) à l'import si BRAIN_API_KEY manque.
# `setdefault` n'écrase pas une vraie clé venue de l'environnement / des secrets CI.
# (Même préambule que tests/adapters/test_brain_service_routes.py.)
os.environ.setdefault("BRAIN_API_KEY", "test-env-key-12345")

import adapters.inference.brain_service as bs  # noqa: E402


@pytest.fixture
def svc():
    # Le cache et le registre d'engines sont des états de module : les remettre à
    # zéro entre les tests, sinon l'ordre d'exécution décide du résultat.
    bs._served_models_cache = None
    bs._engines = {bs.model_name: bs.brain_engine}
    return bs


def _health(models):
    return {"status": "online", "engine": "Ollama/Unified", "models": models}


def test_engine_for_none_returns_the_default_engine(svc):
    assert svc.engine_for(None) is svc.brain_engine


def test_engine_for_the_configured_model_returns_the_default_engine(svc):
    assert svc.engine_for(svc.model_name) is svc.brain_engine


def test_engine_for_a_served_model_builds_and_caches_one_engine(svc):
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": svc.model_name}, {"name": "small:1.5b"}]),
    ):
        first = svc.engine_for("small:1.5b")
        second = svc.engine_for("small:1.5b")
    assert first.model_name == "small:1.5b"
    assert first is second  # cached, not rebuilt per request


def test_engine_for_an_unserved_model_is_rejected_with_400(svc):
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": svc.model_name}]),
    ):
        with pytest.raises(HTTPException) as exc:
            svc.engine_for("not-baked:9b")
    assert exc.value.status_code == 400
    assert "not-baked:9b" in str(exc.value.detail)


def test_engine_for_accepts_the_tagless_alias_ollama_resolves(svc):
    """Ollama registre `mistral` sous `mistral:latest`. `_downgrade_if_model_unserved`
    accepte déjà cet alias : si le brain, lui, le refusait, un modèle que le health
    check déclare sain partirait en 400 à la première requête."""
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": "mistral:latest"}]),
    ):
        assert svc.engine_for("mistral").model_name == "mistral"


def test_an_unreadable_model_list_is_not_cached(svc):
    # Ollama not up yet at first call: the empty answer must not poison the cache
    # for the life of the process.
    with patch.object(svc.brain_engine, "health_check", return_value=_health([])):
        with pytest.raises(HTTPException):
            svc.engine_for("small:1.5b")
    with patch.object(
        svc.brain_engine,
        "health_check",
        return_value=_health([{"name": "small:1.5b"}]),
    ):
        assert svc.engine_for("small:1.5b").model_name == "small:1.5b"

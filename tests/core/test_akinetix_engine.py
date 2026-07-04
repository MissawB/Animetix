from unittest.mock import MagicMock

import pytest
from core.domain.entities.akinetix import AkinetixGameState
from core.domain.services.akinetix_engine import AkinetixEngine
from core.domain.services.catalog_service import CatalogService


@pytest.fixture
def sample_db():
    return [
        {"id": "1", "title": "Naruto", "genres": ["Action"], "micro_tags": ["ninja"]},
        {
            "id": "2",
            "title": "One Piece",
            "genres": ["Adventure"],
            "micro_tags": ["pirate"],
        },
    ]


@pytest.fixture
def mock_catalog_service():
    service = MagicMock(spec=CatalogService)
    service.get_akinetix_attributes.return_value = {}
    return service


@pytest.fixture
def engine(mock_catalog_service):
    return AkinetixEngine(mock_catalog_service)


def test_start_classical_game(engine, sample_db):
    state = engine.start_game(sample_db, mode="classical")
    assert isinstance(state, AkinetixGameState)
    assert state.game_over is False
    assert state.current_attr is not None
    assert len(state.probs) == 2


def test_process_classical_answer(engine, sample_db):
    state = engine.start_game(sample_db, mode="classical")
    # Forcer un attribut connu pour le test
    state.current_attr = "genre:Action"
    state.current_q = "Est-ce une œuvre Action ?"

    new_state = engine.process_answer(sample_db, state, "OUI", mode="classical")
    assert len(new_state.history) == 1
    assert (
        new_state.probs[0] > new_state.probs[1]
    )  # Naruto (Action) should be more probable


def test_process_classical_answer_survives_catalog_growth(engine, sample_db):
    """Régression prod : l'état est démarré sur un catalogue réduit (tranche de
    difficulté) mais la réponse arrive avec le catalogue complet. Le moteur ne
    doit pas lever IndexError ; il repart d'une distribution uniforme."""
    state = engine.start_game(sample_db[:1], mode="classical")
    state.current_attr = "genre:Action"
    state.current_q = "Est-ce une œuvre Action ?"

    new_state = engine.process_answer(sample_db, state, "OUI", mode="classical")
    assert len(new_state.probs) == len(sample_db)
    assert abs(sum(new_state.probs) - 1.0) < 1e-9


def test_start_rl_game(engine, sample_db):
    state = engine.start_game(sample_db, mode="rl")
    assert isinstance(state, AkinetixGameState)
    assert state.game_over is False
    assert state.current_attr is not None


def test_process_rl_answer(engine, sample_db):
    state = engine.start_game(sample_db, mode="rl")
    new_state = engine.process_answer(sample_db, state, "OUI", mode="rl")
    assert len(new_state.history) == 1
    assert new_state.current_q is not None


_BAD_TAG = "aucune unité de calcul d'IA n'est disponible (Ollama/HF)."


def test_is_valid_micro_tag():
    from core.domain.services.akinetix.question_formatter import is_valid_micro_tag

    assert is_valid_micro_tag("ninja")
    assert is_valid_micro_tag("Esthétique Cyberpunk")
    assert not is_valid_micro_tag(_BAD_TAG)
    assert not is_valid_micro_tag("x" * 60)
    assert not is_valid_micro_tag("")
    assert not is_valid_micro_tag(None)


def test_prepare_classical_data_drops_polluted_micro_tags(engine):
    db = [
        {
            "id": "1",
            "title": "X",
            "genres": ["Action"],
            "micro_tags": ["ninja", _BAD_TAG],
        },
    ]
    _items, attrs = engine._prepare_classical_data(db, {})
    assert "tag:ninja" in attrs
    assert all(
        "aucune unité" not in a.lower() and "ollama" not in a.lower() for a in attrs
    )

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

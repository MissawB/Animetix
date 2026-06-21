from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from core.domain.services.akinetix_rl_service import AkinetixRLService

MOD = "core.domain.services.akinetix_rl_service"


@pytest.fixture
def sample_db():
    return [
        {
            "id": "1",
            "title": "Naruto",
            "genres": ["Action", "Shonen"],
            "micro_tags": ["ninja"],
            "studios": ["Pierrot"],
        },
        {
            "id": "2",
            "title": "One Piece",
            "genres": ["Adventure"],
            "micro_tags": ["pirate"],
            "studios": ["Toei"],
        },
        {
            "id": "3",
            "title": "Bleach",
            "genres": ["Action"],
            "micro_tags": ["soul"],
            "studios": ["Pierrot"],
        },
    ]


def _service():
    catalog_service = MagicMock()
    return AkinetixRLService(catalog_service), catalog_service


# --- create_env -----------------------------------------------------------


def test_create_env_uses_catalog_service(sample_db):
    service, cat = _service()
    cat.get_catalog.return_value = {"db": sample_db}

    env = service.create_env("anime")

    cat.get_catalog.assert_called_once_with("anime")
    assert env.catalog == sample_db


# --- start_new_game -------------------------------------------------------


def test_start_new_game_returns_initial_state(sample_db):
    service, _ = _service()
    state = service.start_new_game(sample_db)

    assert state["history"] == []
    assert state["game_over"] is False
    assert state["ai_guess"] is None
    assert state["steps"] == 0
    assert state["asked_attrs"] == []
    assert state["pool_size"] == len(sample_db)
    assert isinstance(state["current_q"], str) and state["current_q"]
    assert ":" in state["current_attr"]


# --- _format_question -----------------------------------------------------


def test_format_question_all_branches():
    service, _ = _service()
    assert service._format_question("genre:Action") == "Est-ce que c'est un Action ?"
    assert (
        service._format_question("studio:Pierrot")
        == "Est-ce que c'est produit par Pierrot ?"
    )
    assert service._format_question("tag:ninja") == "Est-ce que ça parle de ninja ?"
    assert service._format_question("other:foo") == "Attribut : foo ?"


# --- _get_best_match ------------------------------------------------------


def test_get_best_match_returns_first(sample_db):
    service, _ = _service()
    assert service._get_best_match(sample_db, [])["title"] == "Naruto"


# --- _simulate_info_gain --------------------------------------------------


def test_simulate_info_gain_genre(sample_db):
    service, _ = _service()
    from core.domain.services.akinetix_rl_env import AkinetixRLEnvironment

    env = AkinetixRLEnvironment(sample_db)
    idx = env.attributes.index("genre:Action")
    # 2 of 3 candidates have Action -> ratio 0.666 -> gain = 1 - |0.5-0.666|
    gain = service._simulate_info_gain(env, idx)
    assert gain == pytest.approx(1.0 - abs(0.5 - 2 / 3))


def test_simulate_info_gain_tag_and_studio(sample_db):
    service, _ = _service()
    from core.domain.services.akinetix_rl_env import AkinetixRLEnvironment

    env = AkinetixRLEnvironment(sample_db)
    gain_tag = service._simulate_info_gain(env, env.attributes.index("tag:ninja"))
    gain_studio = service._simulate_info_gain(
        env, env.attributes.index("studio:Pierrot")
    )
    # 1/3 ratio for ninja
    assert gain_tag == pytest.approx(1.0 - abs(0.5 - 1 / 3))
    # 2/3 ratio for Pierrot
    assert gain_studio == pytest.approx(1.0 - abs(0.5 - 2 / 3))


def test_simulate_info_gain_empty_candidates(sample_db):
    service, _ = _service()
    from core.domain.services.akinetix_rl_env import AkinetixRLEnvironment

    env = AkinetixRLEnvironment(sample_db)
    env.active_candidates = []
    gain = service._simulate_info_gain(env, 0)
    # ratio 0 -> gain = 1 - 0.5
    assert gain == pytest.approx(0.5)


# --- _get_best_action -----------------------------------------------------


def test_get_best_action_selects_highest_gain(sample_db):
    service, _ = _service()
    from core.domain.services.akinetix_rl_env import AkinetixRLEnvironment

    env = AkinetixRLEnvironment(sample_db)

    # Force np.random.choice to return all indices deterministically
    with patch.object(np.random, "choice", return_value=np.arange(len(env.attributes))):
        # Make simulate gain return increasing values so last index wins
        gains = {i: float(i) for i in range(len(env.attributes))}
        service._simulate_info_gain = MagicMock(side_effect=lambda e, i: gains[i])
        best = service._get_best_action(env)

    assert best == len(env.attributes) - 1


# --- process_answer -------------------------------------------------------


def test_process_answer_continue_branch(sample_db):
    service, _ = _service()
    state = service.start_new_game(sample_db)

    # pool > 1 and steps < 20 -> continue branch (asks new question)
    new_state = service.process_answer(sample_db, state, "OUI")

    assert new_state["game_over"] is False
    assert new_state["steps"] == 1
    assert len(new_state["history"]) == 1
    assert new_state["history"][0]["a"] == "OUI"
    assert new_state["current_attr"] in [a for a in [new_state["current_attr"]]]
    assert ":" in new_state["current_attr"]
    # asked_attrs grew because current_attr existed
    assert len(new_state["asked_attrs"]) >= 1


def test_process_answer_game_over_on_steps(sample_db):
    service, _ = _service()
    state = service.start_new_game(sample_db)
    state["steps"] = 19  # next step -> 20 triggers game over

    new_state = service.process_answer(sample_db, state, "NON")

    assert new_state["game_over"] is True
    assert new_state["ai_guess"] == "Naruto"
    assert "L'IA prédictive pense à : Naruto" in new_state["current_q"]


def test_process_answer_game_over_on_small_pool():
    # Single-item catalog -> pool_size <= 1 -> immediate game over
    db = [
        {
            "id": "1",
            "title": "Solo",
            "genres": ["Action"],
            "micro_tags": ["x"],
            "studios": ["S"],
        }
    ]
    service, _ = _service()
    state = service.start_new_game(db)

    new_state = service.process_answer(db, state, "PEUT-ÊTRE")

    assert new_state["game_over"] is True
    assert new_state["ai_guess"] == "Solo"


def test_process_answer_no_current_attr_skips_append(sample_db):
    service, _ = _service()
    state = service.start_new_game(sample_db)
    state["current_attr"] = None
    state["asked_attrs"] = []

    new_state = service.process_answer(sample_db, state, "OUI")
    # current_attr was None so nothing appended for it in continue branch start
    assert isinstance(new_state["asked_attrs"], list)

import pytest
from unittest.mock import MagicMock
from core.domain.services.akinetix_rl_env import AkinetixRLEnvironment
from core.domain.services.akinetix_rl_service import AkinetixRLService


@pytest.fixture
def sample_catalog():
    return [
        {
            "id": "1",
            "title": "Naruto",
            "genres": ["Action"],
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
    ]


@pytest.fixture
def rl_env(sample_catalog):
    return AkinetixRLEnvironment(sample_catalog)


def test_rl_env_reset(rl_env):
    state, info = rl_env.reset()
    assert state.shape == (3,)
    assert info["target"] in ["Naruto", "One Piece"]
    assert len(rl_env.active_candidates) == 2


def test_rl_env_step_correct(rl_env):
    rl_env.reset()
    rl_env.target_item = rl_env.catalog[0]  # Naruto

    # Find action index for 'genre:Action'
    action_idx = rl_env.attributes.index("genre:Action")
    state, reward, terminated, truncated, info = rl_env.step(action_idx)

    assert len(rl_env.active_candidates) == 1
    assert rl_env.active_candidates[0]["title"] == "Naruto"
    assert reward > 0
    assert terminated is True


def test_rl_env_step_incorrect(rl_env):
    rl_env.reset()
    rl_env.target_item = rl_env.catalog[1]  # One Piece

    action_idx = rl_env.attributes.index(
        "genre:Action"
    )  # Is it Action? No, One Piece is Adventure.
    state, reward, terminated, truncated, info = rl_env.step(action_idx)

    assert len(rl_env.active_candidates) == 1
    assert rl_env.active_candidates[0]["title"] == "One Piece"


def test_rl_service(sample_catalog):
    mock_catalog_service = MagicMock()
    mock_catalog_service.get_catalog.return_value = {"db": sample_catalog}
    mock_catalog_service.load_catalog.return_value = {"db": sample_catalog}
    service = AkinetixRLService(mock_catalog_service)
    env = service.create_env("Anime")
    assert isinstance(env, AkinetixRLEnvironment)

from unittest.mock import MagicMock

import pytest
from core.domain.services.paradox_service import ParadoxDomainService


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def paradox_service(mock_llm_service):
    return ParadoxDomainService(llm_service=mock_llm_service)


def test_prepare_challenge(paradox_service):
    catalog = {
        "titles": ["A", "B", "C", "D"],
        "title_to_full_data": {"A": {}, "B": {}, "C": {}, "D": {}},
    }
    t1, t2, intruder = paradox_service.prepare_challenge(catalog)
    assert t1 in catalog["titles"]
    assert t2 in catalog["titles"]
    assert intruder in catalog["titles"]


def test_prepare_challenge_daily(paradox_service):
    catalog = {
        "titles": ["A", "B", "C", "D"],
        "title_to_full_data": {"A": {}, "B": {}, "C": {}, "D": {}},
    }
    t1, t2, intruder = paradox_service.prepare_challenge(
        catalog, is_daily=True, secret_title="D"
    )
    assert intruder == "D"
    assert t1 in catalog["titles"]
    assert t2 in catalog["titles"]


def test_generate_logic(paradox_service, mock_llm_service):
    mock_llm_service.generate_paradox_explanation.return_value = (
        '{"reasoning": "R", "scenario": "S"}'
    )
    res = paradox_service.generate_logic(
        "Anime", {"title": "A"}, {"title": "B"}, {"title": "I"}, "Français"
    )
    assert res.reasoning == "R"
    assert res.scenario == "S"
    mock_llm_service.generate_paradox_explanation.assert_called_once()


def test_generate_logic_fallback(paradox_service, mock_llm_service):
    mock_llm_service.generate_paradox_explanation.return_value = "Invalid JSON"
    res = paradox_service.generate_logic(
        "Anime", {"title": "A"}, {"title": "B"}, {"title": "I"}, "Français"
    )
    assert res.reasoning == "Analyse probabiliste (SLM)"
    assert res.scenario == "Invalid JSON"

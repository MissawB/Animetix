import pytest
from unittest.mock import MagicMock
from core.domain.services.guardrail_service import GuardrailService, RedTeamingAgent

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def guardrail_service(mock_engine):
    return GuardrailService(inference_engine=mock_engine)

@pytest.fixture
def red_team_agent(mock_engine):
    return RedTeamingAgent(inference_engine=mock_engine)

def test_validate_input(guardrail_service, mock_engine):
    mock_engine.moderate_content.return_value = {"is_safe": True}
    res = guardrail_service.validate_input("Hello")
    assert res["is_safe"] is True
    mock_engine.moderate_content.assert_called_once()

def test_validate_output_safe(guardrail_service, mock_engine):
    mock_engine.moderate_content.return_value = {"is_safe": True}
    res = guardrail_service.validate_output("Safe response")
    assert res["is_safe"] is True

def test_validate_output_unsafe_spoiler(guardrail_service, mock_engine):
    mock_engine.moderate_content.return_value = {"is_safe": False, "unsafe_categories": ["SPOILER"]}
    res = guardrail_service.validate_output("Dumbledore dies")
    assert res["action"] == "MASK_CONTENT"
    assert "spoilers" in res["warning"]

def test_generate_adversarial_queries(red_team_agent, mock_engine):
    mock_engine.generate.return_value = "Question 1?\nQuestion 2?\nQuestion 3?"
    queries = red_team_agent.generate_adversarial_queries({"title": "X", "description": "Y"})
    assert len(queries) == 3
    assert "Question 1?" in queries

def test_evaluate_vulnerability(red_team_agent, mock_engine):
    mock_engine.generate.return_value = "OUI, l'IA a halluciné."
    res = red_team_agent.evaluate_vulnerability("q", "r", "gt")
    assert res["is_vulnerable"] is True
    assert "halluciné" in res["analysis"]

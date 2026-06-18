from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.cove_oracle_service import CoveOracleService


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_neo4j():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("prompt", "system")
    return pm


@pytest.fixture
def cove_service(mock_engine, mock_neo4j, mock_prompt_manager):
    return CoveOracleService(
        inference_engine=mock_engine,
        neo4j_manager=mock_neo4j,
        prompt_manager=mock_prompt_manager,
    )


def test_answer_with_verification_no_questions(cove_service, mock_engine):
    mock_engine.generate.side_effect = [
        InferenceResponse(text="Baseline answer"),
        InferenceResponse(text="{}"),  # No questions
    ]
    res = cove_service.answer_with_verification("Question", "Anime")
    assert res == "Baseline answer"


def test_answer_with_verification_full_path(cove_service, mock_engine, mock_neo4j):
    mock_engine.generate.side_effect = [
        InferenceResponse(text="Naruto is a pirate."),  # Baseline (False)
        InferenceResponse(
            text='{"verification_questions": ["Is Naruto a pirate?"]}'
        ),  # Plan
        InferenceResponse(text="Naruto"),  # Entities extraction
        InferenceResponse(text="No, Naruto is a ninja."),  # Fact check
        InferenceResponse(text="Naruto is a ninja."),  # Final corrected
    ]
    mock_neo4j.get_creator_network_context.return_value = "Naruto: Shinobi of Konoha."

    res = cove_service.answer_with_verification("Who is Naruto?", "Anime")
    assert "ninja" in res
    mock_neo4j.get_creator_network_context.assert_called()

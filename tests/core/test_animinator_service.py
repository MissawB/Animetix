from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.animinator_service import AniminatorDomainService


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def animinator_service(mock_llm_service):
    return AniminatorDomainService(llm_service=mock_llm_service)


def test_select_secret(animinator_service):
    catalog = {"title_to_full_data": {"A": {"title": "A"}, "B": {"title": "B"}}}
    secret = animinator_service.select_secret(catalog)
    assert secret in ["A", "B"]


def test_select_secret_empty(animinator_service):
    catalog = {"titles": []}
    assert animinator_service.select_secret(catalog) is None


def test_ask_oracle(animinator_service, mock_llm_service):
    mock_llm_service.ask_oracle.return_value = "Yes"
    res = animinator_service.ask_oracle("Anime", "Naruto", {}, "Is it a ninja?")
    assert res == "Yes"
    mock_llm_service.ask_oracle.assert_called_once_with(
        "Anime", "Naruto", "Is it a ninja?"
    )


def test_check_guess(animinator_service):
    assert animinator_service.check_guess(" Naruto ", "naruto") is True
    assert animinator_service.check_guess("Bleach", "Naruto") is False


@pytest.mark.asyncio
async def test_aask_oracle_stream_no_facts(animinator_service, mock_llm_service):
    animinator_service.neo4j = None  # _fetch_graph_facts -> "" (no facts)

    captured = {}

    async def fake(media_type, title, question):
        captured["q"] = question
        yield InferenceResponse(text="A")
        yield InferenceResponse(text="B")

    mock_llm_service.aask_oracle_stream = fake

    chunks = [
        c.text
        async for c in animinator_service.aask_oracle_stream("Anime", "Naruto", "Q?")
    ]
    assert chunks == ["A", "B"]
    assert captured["q"] == "Q?"  # question unchanged when no facts


@pytest.mark.asyncio
async def test_aask_oracle_stream_injects_facts(animinator_service, mock_llm_service):
    animinator_service._fetch_graph_facts = MagicMock(return_value="FACTLINE")

    captured = {}

    async def fake(media_type, title, question):
        captured["q"] = question
        yield InferenceResponse(text="X")

    mock_llm_service.aask_oracle_stream = fake

    chunks = [
        c.text
        async for c in animinator_service.aask_oracle_stream("Anime", "Naruto", "Who?")
    ]
    assert chunks == ["X"]
    assert "FACTLINE" in captured["q"] and "Who?" in captured["q"]

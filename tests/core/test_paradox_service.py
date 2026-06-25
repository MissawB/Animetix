from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.paradox_service import ParadoxDomainService


@pytest.mark.asyncio
async def test_agenerate_logic_stream_consumes_inferenceresponse(
    paradox_service, mock_llm_service
):
    mock_llm_service.prompt_manager.get_prompt.return_value = ("p", "s")

    async def _astream(prompt, system_prompt=None, use_slm=False):
        yield InferenceResponse(text='{"reasoning": "R", "scenario": "S"}')

    mock_llm_service.astream_generate.side_effect = _astream

    events = [
        e
        async for e in paradox_service.agenerate_logic_stream(
            "Anime", {"title": "A"}, {"title": "B"}, {"title": "I"}, "Français"
        )
    ]
    result = [e for e in events if e["type"] == "result"]
    assert result
    assert result[0]["content"].reasoning == "R"
    assert result[0]["content"].scenario == "S"


def test_generate_logic_stream_consumes_inferenceresponse(
    paradox_service, mock_llm_service
):
    mock_llm_service.prompt_manager.get_prompt.return_value = ("p", "s")
    mock_llm_service.stream_generate.return_value = iter(
        [InferenceResponse(text='{"reasoning": "R", "scenario": "S"}')]
    )
    events = list(
        paradox_service.generate_logic_stream(
            "Anime", {"title": "A"}, {"title": "B"}, {"title": "I"}, "Français"
        )
    )
    result = [e for e in events if e["type"] == "result"]
    assert result
    assert result[0]["content"].reasoning == "R"
    assert result[0]["content"].scenario == "S"


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

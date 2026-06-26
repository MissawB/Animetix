"""Unit tests for TreeOfThoughtsSearchService.solve_with_tree_of_thoughts_stream.

Ported from feature/vertex-pipelines, adapted to main's inference contract:
InferenceEngine.generate() returns an InferenceResponse exposing `.text`
(the branch returned a bare string).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService


def _resp(text):
    # main's generate() returns an object with a .text attribute
    return SimpleNamespace(text=text)


def test_solve_with_tree_of_thoughts_stream_success():
    mock_engine = MagicMock()

    def mock_generate(prompt, system_prompt=None):
        if "Génère l'étape suivante" in prompt:
            return _resp("Next thought step")
        if "Attribue une note de pertinence" in prompt:
            return _resp("0.8")
        if "Rédige la réponse finale" in prompt:
            return _resp("Final synthetic answer")
        return _resp("Default")

    mock_engine.generate.side_effect = mock_generate

    service = TreeOfThoughtsSearchService(
        inference_engine=mock_engine, prompt_manager=MagicMock()
    )

    events = list(
        service.solve_with_tree_of_thoughts_stream(
            query="test query", breadth=1, depth=1
        )
    )

    # Event 0: root
    assert events[0]["type"] == "node_created"
    assert events[0]["data"]["id"] == "root"
    assert events[0]["data"]["parent_id"] is None

    # Event 1: first thought
    assert events[1]["type"] == "node_created"
    assert events[1]["data"]["id"] == "node_1_1"
    assert events[1]["data"]["text"] == "Next thought step"
    assert events[1]["data"]["is_pruned"] is False

    # Last event: final answer
    assert events[-1]["type"] == "final_answer"
    assert events[-1]["data"]["text"] == "Final synthetic answer"


def test_solve_with_tree_of_thoughts_stream_pruning():
    mock_engine = MagicMock()

    def mock_generate_low_score(prompt, system_prompt=None):
        if "Génère l'étape suivante" in prompt:
            return _resp("Unimportant thought")
        if "Attribue une note de pertinence" in prompt:
            return _resp("0.2")  # Low score -> pruned
        if "Rédige la réponse finale" in prompt:
            return _resp("Fallback answer")
        return _resp("Default")

    mock_engine.generate.side_effect = mock_generate_low_score

    service = TreeOfThoughtsSearchService(
        inference_engine=mock_engine, prompt_manager=MagicMock()
    )

    events = list(
        service.solve_with_tree_of_thoughts_stream(
            query="test query", breadth=1, depth=1
        )
    )

    assert any(
        e["type"] == "node_created" and e["data"]["is_pruned"] is True for e in events
    )
    assert events[-1]["type"] == "final_answer"
    assert events[-1]["data"]["text"] == "Fallback answer"


def test_tot_stream_route_and_view_wired():
    """Smoke test: the SSE route resolves and the view + service provider load."""
    from animetix.api.streams import ToTStreamView  # noqa: F401
    from animetix.containers import get_container
    from django.urls import reverse

    assert reverse("api_tot_stream").endswith("/stream/tot/")
    # The ToT service provider is registered (the view builds it lazily per request).
    assert callable(get_container().core.tree_of_thoughts_service)


@pytest.mark.asyncio
async def test_aevaluate_thought_node_parses_score():
    mock_engine = MagicMock()

    async def mock_agenerate(prompt, system_prompt=None):
        return _resp("0.85")

    mock_engine.agenerate = mock_agenerate
    service = TreeOfThoughtsSearchService(
        inference_engine=mock_engine, prompt_manager=MagicMock()
    )
    score = await service._aevaluate_thought_node("q", [], "thought")
    assert score == 0.85


@pytest.mark.asyncio
async def test_aevaluate_thought_node_fallback_on_unparsable():
    mock_engine = MagicMock()

    async def mock_agenerate(prompt, system_prompt=None):
        return _resp("not a number")

    mock_engine.agenerate = mock_agenerate
    service = TreeOfThoughtsSearchService(
        inference_engine=mock_engine, prompt_manager=MagicMock()
    )
    score = await service._aevaluate_thought_node("q", [], "thought")
    assert score == 0.8

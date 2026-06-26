from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import StreamStep

from tests.helpers.agentic_rag_factory import build_test_agentic_rag_service


def _build_service(**overrides):
    deps = dict(
        inference_engine=MagicMock(),
        rag_service=MagicMock(),
        web_search=MagicMock(),
        prompt_manager=MagicMock(),
        llm_service=MagicMock(),
        workflow_orchestrator=MagicMock(),
        neo4j_manager=None,
        memory_service=None,
        semantic_cache=None,
        obs_service=None,
        xai_service=MagicMock(),
        semantic_router=MagicMock(),
        guardrail_service=None,
    )
    deps.update(overrides)
    service = build_test_agentic_rag_service(**deps)
    service.orchestrator = MagicMock()
    service.orchestrator.processors = {}
    service.semantic_router.classify = MagicMock(return_value="COMPLEX")
    service._assess_complexity = MagicMock(return_value=(0, 1))
    return service


def _aworkflow_writing(answer):
    async def _run(ctx, xai_collector=None):
        ctx.full_answer = answer
        yield StreamStep(type="token", content="hi ").model_dump()

    return _run


@pytest.mark.asyncio
async def test_aplan_and_solve_stream_complex_delegates():
    service = _build_service()
    service.orchestrator.arun_workflow.side_effect = _aworkflow_writing("answer")
    events = [e async for e in service.aplan_and_solve_stream("q", "Anime")]
    assert any(e["type"] == "token" for e in events)


@pytest.mark.asyncio
async def test_aplan_and_solve_stream_simple_routes_fallback():
    service = _build_service()
    service.semantic_router.classify = MagicMock(return_value="SIMPLE")
    service.orchestrator.arun_workflow.side_effect = _aworkflow_writing("simple")
    events = [e async for e in service.aplan_and_solve_stream("q", "Anime")]
    assert any(
        e["type"] == "thought" and "Semantic Router" in e["content"] for e in events
    )


@pytest.mark.asyncio
async def test_aplan_and_solve_stream_guardrail_blocks():
    service = _build_service(guardrail_service=MagicMock())
    service.guardrail_service.validate_input = MagicMock(
        return_value={"is_safe": False, "reason": "blocked"}
    )
    events = [e async for e in service.aplan_and_solve_stream("q", "Anime")]
    assert any(e["type"] == "thought" and "Guardrail" in e["content"] for e in events)

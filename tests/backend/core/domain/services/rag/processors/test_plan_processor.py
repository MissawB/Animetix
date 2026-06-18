from unittest.mock import MagicMock
from backend.core.domain.services.rag.processors.plan_processor import PlanProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState


def consume_generator(gen):
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


def test_plan_processor_delegates_to_planner():
    mock_planner = MagicMock()
    mock_plan = MagicMock()
    mock_plan.requires_saga = False
    mock_plan.requires_graph = False
    mock_planner.plan.return_value = mock_plan

    processor = PlanProcessor(mock_planner)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test query"
    ctx.memories = []
    ctx.thinking_budget = 100
    ctx.thinking_mode = "fast"

    next_state = consume_generator(processor.process(ctx))

    assert next_state == RAGState.RESEARCH
    mock_planner.plan.assert_called_once()
    assert ctx.plan == mock_plan


def test_plan_processor_transitions_to_saga():
    mock_planner = MagicMock()
    mock_plan = MagicMock()
    mock_plan.requires_saga = True
    mock_planner.plan.return_value = mock_plan

    processor = PlanProcessor(mock_planner)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test query"
    ctx.memories = []
    ctx.thinking_budget = 100
    ctx.thinking_mode = "fast"

    next_state = consume_generator(processor.process(ctx))

    assert next_state == RAGState.SAGA_LOOKUP


def test_plan_processor_transitions_to_graph():
    mock_planner = MagicMock()
    mock_plan = MagicMock()
    mock_plan.requires_saga = False
    mock_plan.requires_graph = True
    mock_planner.plan.return_value = mock_plan

    processor = PlanProcessor(mock_planner)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test query"
    ctx.memories = []
    ctx.thinking_budget = 100
    ctx.thinking_mode = "fast"

    next_state = consume_generator(processor.process(ctx))

    assert next_state == RAGState.GRAPH_EXPLORE

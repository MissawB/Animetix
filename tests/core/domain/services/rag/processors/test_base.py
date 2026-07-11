from unittest.mock import MagicMock

import pytest
from core.domain.entities.ai_schemas import RAGContext, RAGState
from core.domain.services.rag.processors.base import StateProcessor

from tests.helpers.async_stream import consume_aprocess


def test_state_processor_is_abstract():
    # It should not be possible to instantiate StateProcessor directly
    with pytest.raises(TypeError):
        StateProcessor()


def test_state_processor_enforces_aprocess_method():
    # A concrete subclass must implement aprocess (async generator that sets
    # ctx.next_state — the sync `process` contract is retired).
    class ConcreteProcessor(StateProcessor):
        async def aprocess(self, ctx: RAGContext, xai_collector=None):
            ctx.next_state = RAGState.FINALIZE
            for _ in []:
                yield _

    processor = ConcreteProcessor()
    assert isinstance(processor, StateProcessor)

    ctx = MagicMock(spec=RAGContext)
    next_state, steps = consume_aprocess(processor, ctx)
    assert next_state == RAGState.FINALIZE
    assert steps == []

from unittest.mock import MagicMock

import pytest

from backend.core.domain.entities.ai_schemas import RAGContext, RAGState
from backend.core.domain.services.rag.processors.base import StateProcessor


def test_state_processor_is_abstract():
    # It should not be possible to instantiate StateProcessor directly
    with pytest.raises(TypeError):
        StateProcessor()


def test_state_processor_enforces_process_method():
    # A concrete subclass must implement process
    class ConcreteProcessor(StateProcessor):
        def process(self, ctx: RAGContext) -> RAGState:
            return RAGState.FINALIZE

    processor = ConcreteProcessor()
    assert isinstance(processor, StateProcessor)

    # Check if process is implemented
    ctx = MagicMock(spec=RAGContext)
    assert processor.process(ctx) == RAGState.FINALIZE

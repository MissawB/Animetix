from unittest.mock import MagicMock

from backend.core.domain.entities.ai_schemas import RAGContext, RAGState
from backend.core.domain.services.rag.processors.speculate_processor import (
    SpeculateProcessor,
)


def consume_generator(gen):
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


def test_speculate_processor_generates_hypothesis():
    mock_forge = MagicMock()
    mock_res = MagicMock()
    mock_res.hypothesis = "test hypothesis"
    mock_res.rationale = "test rationale"
    mock_forge.generate_hypothesis.return_value = mock_res

    processor = SpeculateProcessor(mock_forge)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test query"
    ctx.truth_path = "initial truth"

    next_state = consume_generator(processor.process(ctx))

    assert next_state == RAGState.SYNTHESIZE
    assert "### HYPOTHÈSE LOGIQUE (DÉDUCTION) ###" in ctx.truth_path
    assert "DÉDUCTION : test hypothesis" in ctx.truth_path
    mock_forge.generate_hypothesis.assert_called_once_with(
        "test query", "initial truth"
    )


def test_speculate_processor_handles_no_hypothesis():
    mock_forge = MagicMock()
    mock_forge.generate_hypothesis.return_value = None

    processor = SpeculateProcessor(mock_forge)
    ctx = MagicMock(spec=RAGContext)
    ctx.query = "test query"
    ctx.truth_path = "initial truth"

    next_state = consume_generator(processor.process(ctx))

    assert next_state == RAGState.SYNTHESIZE
    assert ctx.truth_path == "initial truth"

import pytest
from core.domain.entities.ai_schemas import RAGContext, RAGState
from core.domain.services.rag.processors.base import StateProcessor


class _FakeProcessor(StateProcessor):
    def process(self, ctx, xai_collector=None):
        yield {"type": "thought", "content": "a"}
        yield {"type": "token", "content": "b"}
        return RAGState.FINALIZE


class _BoomProcessor(StateProcessor):
    def process(self, ctx, xai_collector=None):
        yield {"type": "thought", "content": "x"}
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_aprocess_default_bridges_sync_and_sets_next_state():
    ctx = RAGContext(query="q", media_type="Anime")
    events = [e async for e in _FakeProcessor().aprocess(ctx)]
    assert events == [
        {"type": "thought", "content": "a"},
        {"type": "token", "content": "b"},
    ]
    assert ctx.next_state == RAGState.FINALIZE


@pytest.mark.asyncio
async def test_aprocess_default_propagates_exception():
    ctx = RAGContext(query="q", media_type="Anime")
    with pytest.raises(RuntimeError, match="boom"):
        [e async for e in _BoomProcessor().aprocess(ctx)]

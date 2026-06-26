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


@pytest.mark.asyncio
async def test_arun_workflow_drives_states_to_finalize():
    from core.domain.services.rag_orchestrator import RAGOrchestrator

    class _P(StateProcessor):
        def __init__(self, next_state, label):
            self._next = next_state
            self._label = label

        def process(self, ctx, xai_collector=None):
            yield {"type": "thought", "content": self._label}
            return self._next

    procs = {
        RAGState.PLAN: _P(RAGState.SYNTHESIZE, "plan"),
        RAGState.SYNTHESIZE: _P(RAGState.FINALIZE, "synth"),
    }
    orch = RAGOrchestrator(procs)
    ctx = RAGContext(query="q", media_type="Anime", current_state=RAGState.PLAN)

    events = [e async for e in orch.arun_workflow(ctx)]
    contents = [e["content"] for e in events]

    assert "plan" in contents
    assert "synth" in contents
    assert ctx.current_state == RAGState.FINALIZE

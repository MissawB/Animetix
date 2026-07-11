import pytest
from core.domain.entities.ai_schemas import RAGContext, RAGState
from core.domain.services.rag.processors.base import StateProcessor
from core.domain.services.rag_orchestrator import RAGOrchestrator


class _FakeProcessor(StateProcessor):
    async def aprocess(self, ctx, xai_collector=None):
        yield {"type": "thought", "content": "a"}
        yield {"type": "token", "content": "b"}
        ctx.next_state = RAGState.FINALIZE


class _BoomProcessor(StateProcessor):
    async def aprocess(self, ctx, xai_collector=None):
        yield {"type": "thought", "content": "x"}
        raise RuntimeError("boom")


def test_state_processor_is_async_only():
    # The sync `process` contract is retired: StateProcessor exposes aprocess
    # alone, and subclasses that only define `process` cannot instantiate.
    assert not hasattr(StateProcessor, "process")

    class _SyncOnly(StateProcessor):
        def process(self, ctx, xai_collector=None):
            yield {}

    with pytest.raises(TypeError):
        _SyncOnly()


@pytest.mark.asyncio
async def test_aprocess_yields_events_and_sets_next_state():
    ctx = RAGContext(query="q", media_type="Anime")
    events = [e async for e in _FakeProcessor().aprocess(ctx)]
    assert events == [
        {"type": "thought", "content": "a"},
        {"type": "token", "content": "b"},
    ]
    assert ctx.next_state == RAGState.FINALIZE


@pytest.mark.asyncio
async def test_aprocess_propagates_exception():
    ctx = RAGContext(query="q", media_type="Anime")
    with pytest.raises(RuntimeError, match="boom"):
        [e async for e in _BoomProcessor().aprocess(ctx)]


class _P(StateProcessor):
    def __init__(self, next_state, label):
        self._next = next_state
        self._label = label

    async def aprocess(self, ctx, xai_collector=None):
        yield {"type": "thought", "content": self._label}
        ctx.next_state = self._next


@pytest.mark.asyncio
async def test_arun_workflow_drives_states_to_finalize():
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


class _Forgetful(StateProcessor):
    async def aprocess(self, ctx, xai_collector=None):
        yield {"type": "thought", "content": "oops"}
        # never sets ctx.next_state


@pytest.mark.asyncio
async def test_arun_workflow_resets_next_state_between_hops():
    # A processor that forgets to set ctx.next_state must fall back to
    # FINALIZE, not silently replay the previous processor's transition.
    procs = {
        RAGState.PLAN: _P(RAGState.SYNTHESIZE, "plan"),
        RAGState.SYNTHESIZE: _Forgetful(),
    }
    orch = RAGOrchestrator(procs)
    ctx = RAGContext(query="q", media_type="Anime", current_state=RAGState.PLAN)

    [e async for e in orch.arun_workflow(ctx)]
    assert ctx.current_state == RAGState.FINALIZE

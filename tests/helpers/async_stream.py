"""Sync-side helpers for exercising the async-only RAG pipeline from
plain (non-async) tests."""

import asyncio


def collect_async(agen):
    """Drain an async generator into a list from sync test code."""

    async def _run():
        return [event async for event in agen]

    return asyncio.run(_run())


def as_async_iter(items):
    """Factory for an async-generator function yielding ``items``.

    Use as a Mock side_effect so call tracking is preserved:
    ``mock.asynthesize_stream.side_effect = as_async_iter([chunk1, chunk2])``.
    """

    async def _gen(*args, **kwargs):
        for item in items:
            yield item

    return _gen


def consume_aprocess(processor, ctx, xai_collector=None):
    """Run a processor's aprocess to completion.

    Returns ``(ctx.next_state, steps)`` — the async replacement for the old
    ``consume_generator(processor.process(ctx))`` helper (async generators
    cannot return a value; processors communicate via ``ctx.next_state``).
    """

    async def _run():
        return [
            event
            async for event in processor.aprocess(ctx, xai_collector=xai_collector)
        ]

    steps = asyncio.run(_run())
    return ctx.next_state, steps

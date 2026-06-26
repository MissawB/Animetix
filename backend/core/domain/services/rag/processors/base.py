from abc import ABC, abstractmethod
from typing import Generator

from core.domain.entities.ai_schemas import RAGContext, RAGState


class StateProcessor(ABC):
    @abstractmethod
    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        """Yields serialized StreamStep dicts (``StreamStep(...).model_dump()``) and
        returns the next ``RAGState``.

        The stream is dict-based end-to-end: processors emit ``model_dump()`` dicts,
        the orchestrator re-yields them via ``yield from``, and the transport layer
        (``streams.py``) serializes each event with ``json.dumps``.
        """
        pass

    async def aprocess(self, ctx: RAGContext, xai_collector=None):
        """Variante async par défaut : ponte le ``process`` sync dans un thread,
        re-yield ses events, et pose la valeur de retour (RAGState) sur
        ``ctx.next_state`` (un générateur async ne peut pas ``return`` de valeur)."""
        import asyncio  # noqa: E402

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        done = object()

        def producer():
            try:
                gen = self.process(ctx, xai_collector=xai_collector)
                while True:
                    try:
                        item = next(gen)
                    except StopIteration as stop:
                        ctx.next_state = stop.value
                        break
                    loop.call_soon_threadsafe(queue.put_nowait, item)
            except Exception as e:  # noqa: BLE001
                loop.call_soon_threadsafe(queue.put_nowait, e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        loop.run_in_executor(None, producer)
        while True:
            item = await queue.get()
            if item is done:
                break
            if isinstance(item, Exception):
                raise item
            yield item

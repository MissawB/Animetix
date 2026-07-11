from abc import ABC, abstractmethod

from core.domain.entities.ai_schemas import RAGContext


class StateProcessor(ABC):
    @abstractmethod
    def aprocess(self, ctx: RAGContext, xai_collector=None):
        """Async generator: yields serialized StreamStep dicts
        (``StreamStep(...).model_dump()``) and communicates the next
        ``RAGState`` via ``ctx.next_state`` (an async generator cannot
        ``return`` a value).

        The stream is dict-based end-to-end: processors emit ``model_dump()``
        dicts, the orchestrator re-yields them, and the transport layer
        (``streams.py``) serializes each event with ``json.dumps``. One-shot
        blocking collaborator calls belong in ``await asyncio.to_thread(...)``
        so the event loop is never blocked.
        """

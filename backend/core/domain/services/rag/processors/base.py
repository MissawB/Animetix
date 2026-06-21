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

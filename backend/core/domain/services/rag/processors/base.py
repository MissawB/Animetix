from abc import ABC, abstractmethod
from typing import Generator

from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep


class StateProcessor(ABC):
    @abstractmethod
    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[StreamStep, None, RAGState]:
        """Processes the state and yields StreamSteps, returning the next RAGState."""
        pass

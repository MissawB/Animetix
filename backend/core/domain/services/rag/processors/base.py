from abc import ABC, abstractmethod
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState

class StateProcessor(ABC):
    @abstractmethod
    def process(self, ctx: RAGContext) -> RAGState:
        """Processes the state and returns the next RAGState."""
        pass

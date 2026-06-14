from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from typing import Optional, Generator
import logging

logger = logging.getLogger('animetix.rag_workflow')

class AcquireKnowledgeProcessor(StateProcessor):
    def __init__(self, librarian):
        self.librarian = librarian

    def process(self, ctx: RAGContext, xai_collector=None) -> Generator[dict, None, RAGState]:
        yield StreamStep(type="thought", content="[Librarian] Identification des lacunes de connaissances...").model_dump()
        
        gap = self.librarian.identify_gap(ctx.query, ctx.truth_path)
        
        if gap and gap.get("query"):
            source_type = gap.get("source_type", "").upper()
            yield StreamStep(type="thought", content=f"[Librarian] Recherche active sur {source_type} : {gap.get('query')}").model_dump()
            fresh_data = self.librarian.fetch_data(gap)
            
            if fresh_data:
                ctx.truth_path += f"\n\n### FRESH WEB/JIKAN DATA ###\n{fresh_data}\n"
                ctx.knowledge_acquired = True
                return RAGState.SYNTHESIZE
            else:
                yield StreamStep(type="thought", content="[Librarian] Aucune donnée supplémentaire trouvée. Passage en mode spéculation...").model_dump()
                return RAGState.SPECULATE
        else:
            return RAGState.SYNTHESIZE

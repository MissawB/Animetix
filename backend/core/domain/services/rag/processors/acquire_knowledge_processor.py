import asyncio
import logging

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.services.rag.processors.base import StateProcessor

logger = logging.getLogger("animetix.rag_workflow")


class AcquireKnowledgeProcessor(StateProcessor):
    def __init__(self, librarian):
        self.librarian = librarian

    async def aprocess(self, ctx: RAGContext, xai_collector=None):
        yield StreamStep(
            type="thought",
            content="[Librarian] Identification des lacunes de connaissances...",
        ).model_dump()

        gap = await asyncio.to_thread(
            self.librarian.identify_gap, ctx.query, ctx.truth_path
        )

        if gap and gap.get("query"):
            source_type = gap.get("source_type", "").upper()
            yield StreamStep(
                type="thought",
                content=f"[Librarian] Recherche active sur {source_type} : {gap.get('query')}",
            ).model_dump()
            fresh_data = await asyncio.to_thread(self.librarian.fetch_data, gap)

            if fresh_data:
                ctx.truth_path += f"\n\n### FRESH WEB/JIKAN DATA ###\n{fresh_data}\n"
                ctx.knowledge_acquired = True
                ctx.next_state = RAGState.SYNTHESIZE
            else:
                yield StreamStep(
                    type="thought",
                    content="[Librarian] Aucune donnée supplémentaire trouvée. Passage en mode spéculation...",
                ).model_dump()
                ctx.next_state = RAGState.SPECULATE
        else:
            ctx.next_state = RAGState.SYNTHESIZE

from typing import Dict

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.services.rag.processors.base import StateProcessor


class RAGOrchestrator:
    def __init__(self, processors: Dict[RAGState, StateProcessor]):
        self.processors = processors

    @property
    def community_partitioner(self):
        return (
            self.processors[RAGState.GRAPH_EXPLORE].community_partitioner
            if RAGState.GRAPH_EXPLORE in self.processors
            else None
        )

    @community_partitioner.setter
    def community_partitioner(self, value):
        if RAGState.GRAPH_EXPLORE in self.processors:
            self.processors[RAGState.GRAPH_EXPLORE].community_partitioner = value

    def run_workflow(self, ctx: RAGContext, xai_collector=None):
        while (
            ctx.current_state not in [RAGState.FINALIZE, RAGState.FAILED]
            and ctx.iteration < ctx.max_iterations
        ):
            ctx.iteration += 1

            # Yield state transition for observability/UX
            yield StreamStep(
                type="thought", content=f"[State Machine] État: {ctx.current_state}"
            ).model_dump()

            processor = self.processors.get(ctx.current_state)
            if not processor:
                ctx.current_state = RAGState.FINALIZE
                break
            # Every processor is a generator: it yields StreamStep dicts and
            # returns the next RAGState (delivered as the value of `yield from`).
            try:
                res = processor.process(ctx, xai_collector=xai_collector)
                ctx.current_state = yield from res
            except Exception as e:
                if ctx.current_state == RAGState.FALLBACK_RAG:
                    ctx.current_state = RAGState.FAILED
                    yield StreamStep(
                        type="thought",
                        content=f"[Recovery] Échec critique du fallback : {str(e)}",
                    ).model_dump()
                else:
                    yield StreamStep(
                        type="thought",
                        content=f"[Recovery] Erreur détectée dans l'état {ctx.current_state} : {str(e)}. Basculement en mode Fallback...",
                    ).model_dump()
                    ctx.current_state = RAGState.FALLBACK_RAG

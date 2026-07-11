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

    async def arun_workflow(self, ctx: RAGContext, xai_collector=None):
        """Drive the state machine (async generator over each processor's aprocess)."""
        while (
            ctx.current_state not in [RAGState.FINALIZE, RAGState.FAILED]
            and ctx.iteration < ctx.max_iterations
        ):
            ctx.iteration += 1
            yield StreamStep(
                type="thought", content=f"[State Machine] État: {ctx.current_state}"
            ).model_dump()

            processor = self.processors.get(ctx.current_state)
            if not processor:
                ctx.current_state = RAGState.FINALIZE
                break
            # Reset before each hop so a processor that forgets to set
            # ctx.next_state falls back to FINALIZE instead of silently
            # replaying the previous processor's transition.
            ctx.next_state = None
            try:
                async for event in processor.aprocess(ctx, xai_collector=xai_collector):
                    yield event
                # Processors communicate the next state via ctx.next_state (async
                # generators cannot return a value). It is set on every normal exit
                # path; fall back to FINALIZE defensively if a processor left it unset.
                if ctx.next_state is None:
                    ctx.current_state = RAGState.FINALIZE
                else:
                    ctx.current_state = ctx.next_state
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

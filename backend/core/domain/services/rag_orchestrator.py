from typing import Dict
from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState

class RAGOrchestrator:
    def __init__(self, processors: Dict[RAGState, StateProcessor]):
        self.processors = processors

    def run_workflow(self, ctx: RAGContext, xai_collector=None):
        while ctx.current_state not in [RAGState.FINALIZE, RAGState.FAILED] and ctx.iteration < ctx.max_iterations:
            ctx.iteration += 1
            processor = self.processors.get(ctx.current_state)
            if not processor:
                ctx.current_state = RAGState.FINALIZE
                break
            # Delegate to processor and yield its steps
            ctx.current_state = yield from processor.process(ctx)

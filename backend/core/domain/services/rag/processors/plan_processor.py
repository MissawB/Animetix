from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from typing import Generator
import time
import logging

logger = logging.getLogger('animetix.rag_workflow')

class PlanProcessor(StateProcessor):
    def __init__(self, planner, xai_collector=None):
        self.planner = planner
        self.xai_collector = xai_collector

    def process(self, ctx: RAGContext) -> Generator[StreamStep, None, RAGState]:
        yield StreamStep(type="thought", content="[Planner] Établissement du plan de recherche...").model_dump()
        start = time.time()
        plan = self.planner.plan(
            ctx.query, 
            ctx.memories, 
            thinking_budget=ctx.thinking_budget // 2, 
            thinking_mode=ctx.thinking_mode
        )
        ctx.plan = plan
        if self.xai_collector:
            self.xai_collector.log_intent(ctx.plan.reasoning)
            
        logger.info(f'PERF: Planner took {(time.time() - start)*1000:.2f}ms')
        
        if plan.requires_saga:
            return RAGState.SAGA_LOOKUP
        elif plan.requires_graph:
            return RAGState.GRAPH_EXPLORE
        else:
            return RAGState.RESEARCH

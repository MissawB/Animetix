from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from typing import Generator
import time
import logging

logger = logging.getLogger("animetix.rag_workflow")


class PlanProcessor(StateProcessor):
    def __init__(self, planner):
        self.planner = planner

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        yield StreamStep(
            type="thought", content="[Planner] Établissement du plan de recherche..."
        ).model_dump()
        start = time.time()
        plan = self.planner.plan(
            ctx.query,
            ctx.memories,
            thinking_budget=ctx.thinking_budget // 2,
            thinking_mode=ctx.thinking_mode,
        )
        ctx.plan = plan
        if xai_collector:
            xai_collector.log_intent(ctx.plan.reasoning)

        logger.info(f"PERF: Planner took {(time.time() - start) * 1000:.2f}ms")

        if plan.requires_saga:
            return RAGState.SAGA_LOOKUP
        elif plan.requires_graph:
            return RAGState.GRAPH_EXPLORE
        else:
            return RAGState.RESEARCH

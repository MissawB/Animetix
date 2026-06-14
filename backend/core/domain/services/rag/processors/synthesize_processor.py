from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from typing import Generator
import logging
import time

logger = logging.getLogger('animetix.rag_workflow')

class SynthesizeProcessor(StateProcessor):
    def __init__(self, synthesizer, xai_service):
        self.synthesizer = synthesizer
        self.xai_service = xai_service

    def process(self, ctx: RAGContext, xai_collector=None) -> Generator[dict, None, RAGState]:
        if ctx.correction_feedback:
            yield StreamStep(type="thought", content="[Synthesizer] Tentative d'auto-correction...").model_dump()
        else:
            yield StreamStep(type="thought", content="[Synthesizer] Rédaction de la réponse expert...").model_dump()
        
        ctx.full_answer = ""
        in_thought = False
        token_count = 0

        for token in self.synthesizer.synthesize_stream(
            ctx.query, 
            ctx.truth_path, 
            thinking_budget=ctx.thinking_budget, 
            thinking_mode=ctx.thinking_mode,
            correction_feedback=ctx.correction_feedback,
            language=ctx.language,
            xai_collector=xai_collector
        ):
            token_count += 1
            if "<thought>" in token and not in_thought:
                in_thought = True
                parts = token.split("<thought>", 1)
                if parts[0]:
                    ctx.full_answer += parts[0]
                    yield StreamStep(type="token", content=parts[0]).model_dump()
                if parts[1]:
                    yield StreamStep(type="thought", content=parts[1]).model_dump()
                continue
            if "</thought>" in token and in_thought:
                in_thought = False
                parts = token.split("</thought>", 1)
                if parts[0]:
                    yield StreamStep(type="thought", content=parts[0]).model_dump()
                if parts[1]:
                    ctx.full_answer += parts[1]
                    yield StreamStep(type="token", content=parts[1]).model_dump()
                continue
            if in_thought:
                if ctx.thinking_budget > 0 and token_count > ctx.thinking_budget:
                    continue
                yield StreamStep(type="thought", content=token).model_dump()
            else:
                ctx.full_answer += token
                yield StreamStep(type="token", content=token).model_dump()
        
        if not ctx.knowledge_acquired:
            res = self.xai_service.measure_confidence(ctx.query, ctx.full_answer)
            confidence = res.get("confidence_score", 1.0) if isinstance(res, dict) else float(res)
            if confidence < 0.6:
                yield StreamStep(type="thought", content=f"[Uncertainty] Basse confiance détectée ({confidence:.2f}). Déclenchement du Librarian...").model_dump()
                ctx.knowledge_acquired = True
                return RAGState.ACQUIRE_KNOWLEDGE

        return RAGState.JUDGE

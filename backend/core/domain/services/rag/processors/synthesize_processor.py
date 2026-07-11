import asyncio
import logging

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.services.rag.processors.base import StateProcessor

logger = logging.getLogger("animetix.rag_workflow")


class SynthesizeProcessor(StateProcessor):
    def __init__(self, synthesizer, xai_service):
        self.synthesizer = synthesizer
        self.xai_service = xai_service

    async def aprocess(self, ctx: RAGContext, xai_collector=None):
        """Synthèse streaming native + mesure de confiance off-loop."""

        if ctx.correction_feedback:
            yield StreamStep(
                type="thought", content="[Synthesizer] Tentative d'auto-correction..."
            ).model_dump()
        else:
            yield StreamStep(
                type="thought",
                content="[Synthesizer] Rédaction de la réponse expert...",
            ).model_dump()

        ctx.full_answer = ""
        in_thought = False
        token_count = 0

        async for token in self.synthesizer.asynthesize_stream(
            ctx.query,
            ctx.truth_path,
            thinking_budget=ctx.thinking_budget,
            thinking_mode=ctx.thinking_mode,
            use_slm=ctx.use_slm,
            correction_feedback=ctx.correction_feedback,
            language=ctx.language,
            xai_collector=xai_collector,
        ):
            token_count += 1
            token_text = token.text
            if "<thought>" in token_text and not in_thought:
                in_thought = True
                parts = token_text.split("<thought>", 1)
                if parts[0]:
                    ctx.full_answer += parts[0]
                    yield StreamStep(type="token", content=parts[0]).model_dump()
                if parts[1]:
                    yield StreamStep(type="thought", content=parts[1]).model_dump()
                continue
            if "</thought>" in token_text and in_thought:
                in_thought = False
                parts = token_text.split("</thought>", 1)
                if parts[0]:
                    yield StreamStep(type="thought", content=parts[0]).model_dump()
                if parts[1]:
                    ctx.full_answer += parts[1]
                    yield StreamStep(type="token", content=parts[1]).model_dump()
                continue
            if in_thought:
                if ctx.thinking_budget > 0 and token_count > ctx.thinking_budget:
                    continue
                yield StreamStep(type="thought", content=token_text).model_dump()
            else:
                ctx.full_answer += token_text
                yield StreamStep(type="token", content=token_text).model_dump()

        if not ctx.knowledge_acquired:
            res = await asyncio.to_thread(
                self.xai_service.measure_confidence, ctx.query, ctx.full_answer
            )
            confidence = (
                res.get("confidence_score", 1.0)
                if isinstance(res, dict)
                else float(res)
            )
            if confidence < 0.6:
                yield StreamStep(
                    type="thought",
                    content=f"[Uncertainty] Basse confiance détectée ({confidence:.2f}). Déclenchement du Librarian...",
                ).model_dump()
                ctx.knowledge_acquired = True
                ctx.next_state = RAGState.ACQUIRE_KNOWLEDGE
                return

        ctx.next_state = RAGState.JUDGE

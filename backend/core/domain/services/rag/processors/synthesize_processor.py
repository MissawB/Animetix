from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState
import logging
import time

logger = logging.getLogger('animetix.rag_workflow')

class SynthesizeProcessor(StateProcessor):
    def __init__(self, synthesizer, xai_service, rag_service):
        self.synthesizer = synthesizer
        self.xai_service = xai_service
        self.rag_service = rag_service

    def process(self, ctx: RAGContext) -> RAGState:
        # Based on RAGWorkflowManager._handle_synthesize
        # Note: Streaming logic needs to be handled outside or via callback?
        # For now, let's just do the core logic.
        
        ctx.full_answer = ""
        
        # Simplified synthesis: no streaming for now to fit in StateProcessor.process
        # In a real scenario, this should be refactored to support streaming.
        # Maybe ctx should have a callback for token updates?
        
        # For now, let's call the synthesizer.
        # The synthesizer.synthesize_stream is a generator.
        
        for token in self.synthesizer.synthesize_stream(
            ctx.query, 
            ctx.truth_path, 
            thinking_budget=ctx.thinking_budget, 
            thinking_mode=ctx.thinking_mode,
            correction_feedback=ctx.correction_feedback
        ):
            # This is tricky because we can't yield.
            # I will just concatenate it for now, ignoring the complex <thought> splitting.
            # This is suboptimal but necessary to fit the interface.
            
            # Better: if SynthesizeProcessor needs streaming, the architecture might need to change.
            # Let's assume the SynthesizeProcessor is responsible for populating ctx.full_answer.
            if "<thought>" in token or "</thought>" in token:
                continue
            ctx.full_answer += token
        
        if not ctx.knowledge_acquired:
            res = self.xai_service.measure_confidence(ctx.query, ctx.full_answer)
            confidence = res.get("confidence_score", 1.0) if isinstance(res, dict) else float(res)
            if confidence < 0.6:
                ctx.knowledge_acquired = True
                return RAGState.ACQUIRE_KNOWLEDGE

        return RAGState.JUDGE

from backend.core.domain.services.rag.processors.base import StateProcessor
from backend.core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from backend.core.domain.exceptions import InferenceError, InfrastructureError
from typing import Generator
import logging

logger = logging.getLogger("animetix.rag_workflow")


class VlmRerankProcessor(StateProcessor):
    def __init__(self, prompt_manager, inference_engine):
        self.prompt_manager = prompt_manager
        self.inference_engine = inference_engine

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        yield StreamStep(
            type="thought",
            content="[VLM-Reranker] Analyse visuelle des images candidates...",
        ).model_dump()
        image_urls = []
        valid_candidates = []
        for c in ctx.candidates:
            url = (
                c.get("image")
                or c.get("image_url")
                or c.get("cover_url")
                or c.get("poster_path")
            )
            if url:
                image_urls.append(url)
                valid_candidates.append(c)

        if not image_urls:
            yield StreamStep(
                type="thought",
                content="[VLM-Reranker] Aucune image exploitable trouvée pour le reranking.",
            ).model_dump()
            return RAGState.SYNTHESIZE

        try:
            prompt_text, system_prompt = self.prompt_manager.get_prompt(
                "vlm_reranker", query=ctx.query, num_images=len(image_urls)
            )
            reranked = self.inference_engine.visual_rerank(
                prompt_text, image_urls, system_prompt=system_prompt
            )
            for item in reranked:
                idx = item.get("index")
                if idx is not None and idx < len(valid_candidates):
                    valid_candidates[idx]["visual_score"] = item.get("score", 0.0)
            valid_candidates.sort(
                key=lambda x: x.get("visual_score", 0.0), reverse=True
            )
            top_5 = valid_candidates[:5]
            vlm_context = "\n### VÉRIFICATION VISUELLE (RERANKING) ###\n"
            for i, c in enumerate(top_5):
                vlm_context += f"{i + 1}. {c.get('title')} (Score Visuel: {c.get('visual_score', 0.0):.2f})\n"
                vlm_context += (
                    f"   - Description: {c.get('description', '')[:300]}...\n"
                )
            ctx.truth_path += f"\n{vlm_context}"
            if xai_collector:
                xai_collector.log_agent_thought(
                    "VLMReranker",
                    "Analyse visuelle terminée pour le reranking des candidats",
                )
            yield StreamStep(
                type="thought",
                content=f"[VLM-Reranker] Classement visuel terminé. Top match : {top_5[0].get('title')}",
            ).model_dump()
        except InferenceError as e:
            logger.error(f"VLM Rerank error: {e}")
            yield StreamStep(
                type="thought",
                content=f"[VLM-Reranker] Échec de l'analyse visuelle : {str(e)}",
            ).model_dump()
        except (InferenceError, InfrastructureError, RuntimeError) as e:
            logger.error(f"Unexpected error in VLM Reranker: {e}")
            yield StreamStep(
                type="thought",
                content="[VLM-Reranker] Une erreur inattendue est survenue.",
            ).model_dump()

        return RAGState.SYNTHESIZE

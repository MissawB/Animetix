import logging
from typing import Generator

from core.domain.entities.ai_schemas import RAGContext, RAGState, StreamStep
from core.domain.services.rag.processors.base import StateProcessor

logger = logging.getLogger("animetix.rag_workflow")


class FallbackRagProcessor(StateProcessor):
    def __init__(self, rag_service, inference_engine, expert_facts):
        self.rag_service = rag_service
        self.inference_engine = inference_engine
        self.expert_facts = expert_facts

    def process(
        self, ctx: RAGContext, xai_collector=None
    ) -> Generator[dict, None, RAGState]:
        yield StreamStep(
            type="thought",
            content="[Fallback] Exécution d'une recherche hybride standard...",
        ).model_dump()

        expert_injections = self._get_expert_injections(ctx.query)
        results = self.rag_service.hybrid_search(ctx.query, ctx.media_type)

        local_ctx_list = [
            f"- {r.get('title')}: {r.get('description', '')[:2000]}" for r in results
        ]
        if expert_injections:
            fallback_context = "\n".join(
                [f"- Fait de Repli: {f}" for f in expert_injections] + local_ctx_list
            )
        else:
            fallback_context = "\n".join(local_ctx_list)

        yield StreamStep(
            type="thought", content="[Fallback] Synthèse de la réponse de secours..."
        ).model_dump()

        if ctx.language == "English":
            prompt = f"Answer the following question using ONLY the context provided.\nQUESTION: {ctx.query}\nCONTEXT:\n{fallback_context}"
            system = (
                "You are an expert assistant. Be concise and factual. Reply in English."
            )
        else:
            prompt = f"Réponds à la question suivante en utilisant UNIQUEMENT le contexte fourni.\nQUESTION: {ctx.query}\nCONTEXTE:\n{fallback_context}"
            system = "Tu es un assistant expert. Sois concis et factuel. Réponds en Français."

        ctx.full_answer = ""
        for token in self.inference_engine.stream_generate(prompt, system):
            ctx.full_answer += token.text
            yield StreamStep(type="token", content=token.text).model_dump()

        return RAGState.FINALIZE

    def _get_expert_injections(self, query: str) -> list[str]:
        expert_injections = []
        q_lower = query.lower()

        for rule in self.expert_facts:
            primary_keywords = rule.get("primary_keywords", [])
            secondary_keywords = rule.get("secondary_keywords", [])
            fact = rule.get("fact")

            primary_match = any(pk in q_lower for pk in primary_keywords)

            if primary_match:
                if not secondary_keywords or any(
                    sk in q_lower for sk in secondary_keywords
                ):
                    expert_injections.append(fact)

        return expert_injections

import logging
from typing import List
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.long_context")


class LongContextDiscoveryService:
    """
    Service de gestion de contextes massifs (Sagas entières).
    Implémente le résumé hiérarchique et la compression sémantique.
    """

    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.chunk_size = 4000  # Taille des morceaux en caractères (~1000 tokens)

    def summarize_long_saga(self, full_text: str) -> str:
        """
        Génère un résumé global d'un texte très long via une approche récursive.
        """
        if len(full_text) < self.chunk_size * 1.5:
            return self._summarize_chunk(full_text)

        # 1. Découpage en morceaux
        chunks = [
            full_text[i : i + self.chunk_size]
            for i in range(0, len(full_text), self.chunk_size)
        ]

        # 2. Résumé de chaque morceau
        intermediate_summaries = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"📜 Summarizing chunk {i + 1}/{len(chunks)}...")
            summary = self._summarize_chunk(chunk)
            intermediate_summaries.append(f"Segment {i + 1}: {summary}")

        # 3. Récursion ou synthèse finale
        combined_summaries = "\n\n".join(intermediate_summaries)

        if len(combined_summaries) > self.chunk_size * 2:
            return self.summarize_long_saga(combined_summaries)

        return self._synthesize_final(combined_summaries)

    def extract_key_lore_points(self, long_text: str) -> List[str]:
        """Extrait les éléments de lore importants d'une longue saga."""
        summary = self.summarize_long_saga(long_text)
        prompt, system = self.prompt_manager.get_prompt(
            "lore_extraction", context=summary
        )
        response = self.inference_engine.generate(prompt, system_prompt=system)
        return [p.strip() for p in response.split("\n") if len(p.strip()) > 5]

    def _summarize_chunk(self, text: str) -> str:
        prompt, system = self.prompt_manager.get_prompt(
            "hierarchical_summary_chunk", text=text
        )
        return self.inference_engine.generate(prompt, system_prompt=system)

    def _synthesize_final(self, summaries: str) -> str:
        prompt, system = self.prompt_manager.get_prompt(
            "hierarchical_summary_final", context=summaries
        )
        return self.inference_engine.generate(prompt, system_prompt=system)

    def create_haystack(self, filler: str, needle: str, size: int, depth: float) -> str:
        words = [filler] * size
        insert_idx = int(size * depth)
        words.insert(insert_idx, needle)
        return " ".join(words)

    def run_needle_test(
        self, needle: str, question: str, size: int, depth: float
    ) -> dict:
        haystack = self.create_haystack("filler", needle, size, depth)
        prompt = f"Context: {haystack}\nQuestion: {question}"
        response = self.inference_engine.generate(prompt)
        success = needle in response
        return {"success": success, "context_size": size, "depth": depth}

    def benchmark_model_limits(self, sizes: list) -> list:
        results = []
        for size in sizes:
            for depth in [0.1, 0.5, 0.9]:
                res = self.run_needle_test("1234", "What is the secret?", size, depth)
                results.append(res)
        return results

# -*- coding: utf-8 -*-
"""
DSPy Prompt Optimizer for Animetix.
Automates prompt engineering by mutating templates and selecting the version with the highest evaluation scores.
"""

import logging  # noqa: E402
from typing import Dict, List, Tuple  # noqa: E402

from core.ports.inference_port import InferencePort  # noqa: E402

logger = logging.getLogger("animetix.meta.dspy")


class DSPyPromptOptimizer:
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def mutate_template(
        self, original_template: str, num_mutations: int = 3
    ) -> List[str]:
        """
        Génère des mutations linguistiques d'un prompt d'origine via LLM.
        """
        logger.info(
            f"🧬 DSPy: Mutating original template (Options: {num_mutations})..."
        )
        mutations = [original_template]

        mutation_prompt = (
            f"Tu es un ingénieur de prompts d'élite.\n"
            f"Voici un prompt d'origine :\n"
            f'"""{original_template}"""\n\n'
            f"Génère une variante sémantiquement équivalente mais reformulée de manière à optimiser le raisonnement du LLM. "
            f"Sois précis, direct et professionnel. Ne renvoie QUE la variante, sans introduction."
        )

        for idx in range(num_mutations - 1):
            try:
                mutated = self.inference_engine.generate(
                    prompt=mutation_prompt,
                    system_prompt="Tu es l'Optimiseur de Prompts DSPy.",
                ).strip()
                if mutated:
                    mutations.append(mutated)
            except Exception as e:
                logger.error(f"Failed to generate prompt mutation: {e}")
                mutations.append(f"{original_template} (Mutation variant {idx + 1})")

        return mutations

    def evaluate_and_select_best(
        self, original_template: str, test_dataset: List[Dict[str, str]]
    ) -> Tuple[str, float]:
        """
        Évalue toutes les mutations sur un jeu de données de test et retourne le meilleur prompt
        avec sa note moyenne de pertinence.
        """
        mutations = self.mutate_template(original_template, num_mutations=3)
        best_template = original_template
        best_score = -1.0

        for idx, template in enumerate(mutations):
            logger.info(f"🔬 DSPy: Evaluating mutation variant #{idx + 1}...")
            scores = []

            for item in test_dataset:
                query = item.get("query", "")
                expected = item.get("expected", "")

                # Formatage du prompt d'évaluation
                formatted_prompt = template.replace("{query}", query)
                try:
                    generated = self.inference_engine.generate(
                        prompt=formatted_prompt,
                        system_prompt="Tu es le Répondeur Animetix.",
                    )
                    score = self._evaluate_accuracy(generated, expected)
                    scores.append(score)
                except Exception:
                    logger.warning(
                        "⚠️ DSPy variant evaluation step failed. Appending fallback score 0.5.",
                        exc_info=True,
                    )
                    scores.append(0.5)

            avg_score = sum(scores) / len(scores) if scores else 0.0
            logger.info(
                f"📊 Variant #{idx + 1} average evaluation score: {avg_score:.2f}"
            )

            if avg_score > best_score:
                best_score = avg_score
                best_template = template

        logger.info(f"🏆 DSPy Optimization complete. Best score: {best_score:.2f}")
        return best_template, best_score

    def _evaluate_accuracy(self, response: str, expected: str) -> float:
        """
        Critique simple mesurant l'adéquation sémantique (LLM-as-a-Judge).
        """
        judge_prompt = (
            f'Réponse générée : "{response}"\n'
            f'Résultat attendu : "{expected}"\n\n'
            f"Donne une note de pertinence stricte sous forme de flottant entre 0.0 et 1.0 (ex: 0.9). "
            f"Réponds UNIQUEMENT avec le nombre."
        )
        try:
            score_text = self.inference_engine.generate(
                prompt=judge_prompt, system_prompt="Tu es le Juge d'évaluation."
            ).strip()
            import re  # noqa: E402

            match = re.search(r"\d+\.\d+", score_text)
            if match:
                return float(match.group(0))
            return 0.8
        except Exception:
            logger.warning(
                "⚠️ DSPy Judge evaluation failed. Falling back to default score 0.7.",
                exc_info=True,
            )
            return 0.7

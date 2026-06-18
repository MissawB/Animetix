import json
import logging
import os
from typing import Any, Dict, List, Optional

from core.ports.feedback_port import FeedbackRepositoryPort

from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")


class DPOFeedbackLoop:
    """
    Automates the collection and validation of user feedback for DPO fine-tuning.
    Ensures high-quality chosen/rejected pairs.
    Uses FeedbackRepositoryPort for persistence abstraction.
    """

    DEFAULT_REJECTED_RESPONSE = (
        "Désolé, je ne peux pas traiter cette demande pour le moment."
    )

    def __init__(
        self,
        data_dir: str = "data/mlops/datasets",
        prompt_manager: Optional[PromptManager] = None,
        feedback_port: Optional[FeedbackRepositoryPort] = None,
        llm_service: Any = None,
    ):
        self.data_dir = data_dir
        self.prompt_manager = prompt_manager
        self.feedback_port = feedback_port
        self.llm_service = llm_service
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create DPO data directory {data_dir}: {e}")

    def optimize_prompt_from_feedback(
        self, prompt_key: str, limit: int = 50
    ) -> Optional[str]:
        """
        Analyses chosen/rejected pairs and suggests a new system prompt via LLM.
        """
        if not self.llm_service or not self.prompt_manager or not self.feedback_port:
            logger.error("Missing dependencies for prompt optimization.")
            return None

        feedbacks = self.feedback_port.get_recent_feedback(
            limit=limit, feedback_type=prompt_key
        )
        chosen_examples = []
        rejected_examples = []

        for fb in feedbacks:
            if not self.validate_feedback(fb):
                continue

            context = fb.get("context") or fb.get("input_context")
            output = fb.get("output") or fb.get("output_text")

            if fb.get("is_positive"):
                chosen_examples.append(f"Context: {context}\nResponse: {output}")
            else:
                rejected_examples.append(f"Context: {context}\nResponse: {output}")

        if not chosen_examples or not rejected_examples:
            logger.warning(f"Not enough diverse feedback to optimize '{prompt_key}'.")
            return None

        # 2. Obtenir le prompt actuel
        _, current_system = self.prompt_manager.get_prompt(
            prompt_key, context="{context}"
        )

        # 3. Demander au LLM une amélioration
        optimization_prompt = f"""
Tu es un ingénieur de prompt expert. Ta mission est d'améliorer le 'System Prompt' d'un agent IA en analysant ses succès (Chosen) et ses échecs (Rejected).

PROMPT ACTUEL (System) :
{current_system}

EXEMPLES RÉUSSIS (Chosen) :
{chr(10).join(chosen_examples[:5])}

EXEMPLES ÉCHOUÉS (Rejected) :
{chr(10).join(rejected_examples[:5])}

ANALYSE :
- Identifie ce qui manque dans le System Prompt actuel pour éviter les échecs constatés.
- Identifie les qualités des réponses réussies à renforcer.

TACHE :
Rédige un NOUVEAU 'System Prompt' plus performant, précis et direct.
Réponds UNIQUEMENT avec le nouveau System Prompt, sans explications.
"""

        try:
            new_system_prompt = self.llm_service.generate(
                optimization_prompt, system_prompt="Tu es un Meta-Prompt Engineer."
            )
            if new_system_prompt:
                # 4. Sauvegarder
                self.prompt_manager.update_system_prompt(
                    prompt_key, new_system_prompt.strip()
                )
                return new_system_prompt.strip()
        except Exception as e:
            logger.error(f"LLM optimization failed: {e}")

        return None

    def validate_feedback(self, entry: Dict) -> bool:
        """Rigorous validation of a feedback entry."""
        context = entry.get("context") or entry.get("input_context")
        output = entry.get("output") or entry.get("output_text")

        if not context or not output:
            return False

        if len(output) < 15 or len(context) < 5:
            return False

        generic_errors = [
            "je ne sais pas",
            "désolé",
            "erreur",
            "temporairement indisponible",
            "i am sorry",
        ]
        if any(err in output.lower() for err in generic_errors):
            return False

        return True

    def create_dpo_pair(self, entry: Dict, chosen_override: str = None) -> Dict:
        """Creates a DPO pair (Chosen/Rejected)."""
        context = entry.get("context") or entry.get("input_context")
        output = entry.get("output") or entry.get("output_text")
        is_positive = entry.get("is_positive", False)

        if self.prompt_manager:
            prompt, _ = self.prompt_manager.get_prompt(
                "dpo_expert_response", context=context
            )
        else:
            prompt = f"Context: {context}\nResponse:"

        if is_positive:
            return {
                "prompt": prompt,
                "chosen": output,
                "rejected": self.DEFAULT_REJECTED_RESPONSE,
            }
        else:
            chosen = chosen_override or "RÉPONSE_À_GÉNÉRER_PAR_MODÈLE_ORACLE"
            return {"prompt": prompt, "chosen": chosen, "rejected": output}

    def export_preference_dataset(self):
        """Export from persistence port with sensitive data scrubbing."""
        if not self.feedback_port:
            logger.error("Feedback port missing for export.")
            return

        from core.utils.scrubbing import scrub_sensitive_data  # noqa: E402

        feedbacks = self.feedback_port.get_recent_feedback(limit=1000)
        output_path = os.path.join(self.data_dir, "dpo_export.jsonl")

        with open(output_path, "w", encoding="utf-8") as f:
            for fb in feedbacks:
                if self.validate_feedback(fb):
                    pair = self.create_dpo_pair(fb)
                    # Force recursive scrubbing of the entire pair before export
                    scrubbed_pair = scrub_sensitive_data(pair)
                    f.write(json.dumps(scrubbed_pair, ensure_ascii=False) + "\n")

    def get_rejected_for_curation(self, limit: int = 100) -> List[Dict]:
        """Retrieves negative feedback entries."""
        if not self.feedback_port:
            return []

        feedbacks = self.feedback_port.get_recent_feedback(limit=limit)
        results = []
        for fb in feedbacks:
            if not fb.get("is_positive") and self.validate_feedback(fb):
                results.append(fb)

        return results

    def analyze_feedback_trends(self) -> Dict:
        """Analyzes trends via port."""
        if not self.feedback_port:
            return {"satisfaction_rate": 0, "total": 0}

        return self.feedback_port.get_feedback_stats()

    def curate_feedback(self, feedback_id: int, chosen_text: str) -> bool:
        """
        Manually validates a rejected feedback by providing the 'Chosen' alternative.
        Persists as a GoldDatasetEntry.
        """
        from animetix.models import AIFeedback, GoldDatasetEntry  # noqa: E402

        try:
            fb = AIFeedback.objects.get(id=feedback_id)
            # Create or update gold entry
            GoldDatasetEntry.objects.update_or_create(
                source_feedback=fb,
                defaults={
                    "context": fb.input_context,
                    "instruction": "Generate high quality response",
                    "response": chosen_text,
                    "is_validated": True,
                },
            )
            logger.info(f"✅ Feedback {feedback_id} curated into Gold Dataset.")
            return True
        except Exception as e:
            logger.error(f"❌ Curation failed for feedback {feedback_id}: {e}")
            return False

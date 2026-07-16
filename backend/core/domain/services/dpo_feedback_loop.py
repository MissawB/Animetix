import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

from core.ports.feedback_port import FeedbackRepositoryPort

from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")

django_available = False
AIFeedback: Any = None
try:
    import django

    django.setup()
    django_available = True
    from animetix.models import AIFeedback  # type: ignore[no-redef]
except Exception:
    pass


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

        # Initialize Gemini client for Oracle generation (if available)
        try:
            from dotenv import load_dotenv
            from google import genai

            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                logger.info(
                    "Initializing Gemini API client for DPO Oracle responses..."
                )
                self.client = genai.Client(api_key=api_key)
            else:
                self.client = None
        except ImportError:
            self.client = None

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

    def generate_oracle_response(self, context_prompt: str) -> str:
        """
        Génère une réponse expert corrigée (chosen) via le modèle Oracle (Gemini).
        """
        if not self.client:
            return (
                "Désolé, je ne dispose pas d'informations supplémentaires sur ce sujet."
            )

        from core.utils.gemini_models import GEMINI_FLASH

        prompt = (
            f"Tu es un expert absolu de la japanimation, des mangas, des seiyuu et du marché français. "
            f"Génère une réponse parfaite, claire et 100% en français pour la question suivante :\n\n"
            f"{context_prompt}\n\n"
            f"Renvoie uniquement la réponse rédigée de manière fluide et naturelle, sans aucune salutation ou métadonnée."
        )

        model_name = GEMINI_FLASH

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response.text:
                    time.sleep(0.5)  # Respecter le rate-limiting
                    return response.text.strip()
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/3 failed to generate chosen response via Gemini: {e}"
                )
                err_msg = str(e).upper()
                if (
                    "RESOURCE_EXHAUSTED" in err_msg
                    or "429" in err_msg
                    or "UNAVAILABLE" in err_msg
                    or "503" in err_msg
                ):
                    sleep_time = (attempt + 1) * 15.0
                    logger.info(
                        f"Rate limit or service unavailable detected in DPO loop. Sleeping for {sleep_time}s..."
                    )
                    time.sleep(sleep_time)
                else:
                    time.sleep(1.0)

        return "Désolé, je ne dispose pas d'informations supplémentaires sur ce sujet."

    def create_dpo_pair(
        self,
        entry: Dict,
        chosen_override: Optional[Any] = None,
        corrupt_fn: Optional[Any] = None,
    ) -> Optional[Dict]:
        """
        Creates a DPO pair (Chosen/Rejected).
        Supports both clean-architecture views (chosen_override) and pipeline datasets (corrupt_fn with Gemini Oracle fallback).
        """
        # Resolve signature polymorphism
        if callable(chosen_override):
            corrupt_fn = chosen_override
            chosen_override = None

        context = entry.get("context") or entry.get("input_context") or ""
        output = entry.get("output") or entry.get("output_text")
        is_positive = entry.get("is_positive", False)

        if self.prompt_manager:
            prompt, _ = self.prompt_manager.get_prompt(
                "dpo_expert_response", context=context
            )
        else:
            prompt = f"Génère une réponse expert pour : {context}"

        if is_positive:
            # Chosen is the output itself
            rejected = None
            if corrupt_fn:
                rejected = corrupt_fn(output)
            if not rejected or rejected == output:
                rejected = self.DEFAULT_REJECTED_RESPONSE
            return {
                "prompt": prompt,
                "chosen": output,
                "rejected": rejected,
            }
        else:
            # Chosen is generated or provided
            if chosen_override:
                chosen = chosen_override
            else:
                # Fallback to Oracle Gemini Flash
                chosen = self.generate_oracle_response(context)
                default_refusal = "Désolé, je ne dispose pas d'informations supplémentaires sur ce sujet."
                if chosen == default_refusal or not chosen:
                    return None

            return {"prompt": prompt, "chosen": chosen, "rejected": output}

    def fetch_db_feedbacks(self) -> List[Dict[str, Any]]:
        """
        Queries AIFeedback models from Django database.
        """
        local_django_available = django_available
        local_AIFeedback = AIFeedback

        if "dpo_feedback_loop" in sys.modules:
            mod = sys.modules["dpo_feedback_loop"]
            if hasattr(mod, "django_available"):
                local_django_available = mod.django_available
            if hasattr(mod, "AIFeedback"):
                local_AIFeedback = mod.AIFeedback
        if "pipeline.mlops.dpo_feedback_loop" in sys.modules:
            mod = sys.modules["pipeline.mlops.dpo_feedback_loop"]
            if hasattr(mod, "django_available"):
                local_django_available = mod.django_available
            if hasattr(mod, "AIFeedback"):
                local_AIFeedback = mod.AIFeedback

        if not local_django_available or not local_AIFeedback:
            logger.warning(
                "Django is not configured or available. Returning empty feedback list."
            )
            return []

        try:
            feedbacks = []
            for fb in local_AIFeedback.objects.all():
                feedbacks.append(
                    {
                        "context": fb.input_context,
                        "output": fb.output_text,
                        "is_positive": fb.is_positive,
                        "feedback_type": fb.feedback_type,
                    }
                )
            logger.info(
                f"Retrieved {len(feedbacks)} feedback entries from Django database."
            )
            return feedbacks
        except Exception as e:
            logger.warning(
                f"Failed to query Django AIFeedback table: {e}. Returning empty list."
            )
            return []

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
                    if pair is not None:
                        # Force recursive scrubbing of the entire pair before export
                        scrubbed_pair = scrub_sensitive_data(pair)
                        f.write(json.dumps(scrubbed_pair, ensure_ascii=False) + "\n")

    def process_and_export(
        self, raw_data_path: str, output_path: str, corrupt_fn=None
    ) -> int:
        """
        Processes raw feedback and exports a validated DPO dataset.
        """
        if not os.path.exists(raw_data_path):
            logger.warning(f"Raw data path {raw_data_path} does not exist.")
            return 0

        processed_count = 0
        with open(output_path, "w", encoding="utf-8") as out_f:
            with open(raw_data_path, "r", encoding="utf-8") as in_f:
                for line in in_f:
                    try:
                        fb = json.loads(line)
                        if self.validate_feedback(fb):
                            pair = self.create_dpo_pair(fb, corrupt_fn=corrupt_fn)
                            if pair is not None:
                                out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                                processed_count += 1
                    except json.JSONDecodeError:
                        continue

        logger.info(
            f"✨ DPO Export complete: {processed_count} pairs validated and saved to {output_path}"
        )
        return processed_count

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

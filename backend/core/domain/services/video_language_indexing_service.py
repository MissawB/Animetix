import json
import logging
from typing import Any, Dict, Optional

from core.domain.services.prompt_manager import PromptManager
from core.ports.feedback_port import FeedbackRepositoryPort
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.video_indexing")


class VideoLanguageIndexingService:
    """
    Service d'Indexation Langage-Vidéo (Task 5.5).
    Utilise Video-LLaVA pour générer des descriptions denses de scènes d'animes.
    Intègre une 'Skill Bank' auto-évolutive (Inspiré par VisualClaw).
    """

    def __init__(
        self,
        inference_engine: InferencePort,
        prompt_manager: PromptManager,
        repository: Any = None,
        feedback_port: Optional[FeedbackRepositoryPort] = None,
    ):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.repository = repository
        self.feedback_port = feedback_port

    def generate_dense_video_description(self, video_data: bytes, title: str) -> str:
        """
        Génère une description textuelle détaillée du contenu d'une vidéo anime.
        Intègre les expériences passées (Skill Bank) pour éviter de répéter les mêmes erreurs.
        """
        logger.info(f"📽️ Video-LLaVA: Generating dense narrative for '{title}'...")

        # 1. Récupération des expériences de correction (Skill Bank)
        skill_context = self._get_skill_bank_context(title)

        prompt, system = self.prompt_manager.get_prompt(
            "video_narrative_generation", title=title
        )

        # Injection des skills évolutifs dans le système prompt
        if skill_context:
            system += (
                f"\n\n🧠 SKILL BANK (Expériences de correction) :\n{skill_context}"
            )

        # 2. Inférence Multimodale
        description = self.inference_engine.generate_video_description(
            video_data, prompt
        )

        if not description:
            logger.error(f"❌ Video-LLaVA failed for '{title}'.")
            return ""

        logger.info(f"✅ Video Narrative generated ({len(description)} chars).")
        return description

    def record_recognition_failure(
        self, query: str, actual_output: str, correction: str, user_id: Any = None
    ):
        """
        Enregistre un échec de reconnaissance visuelle dans la Skill Bank.
        Ex: Mauvaise identification d'une technique de combat ou d'un studio.
        """
        if not self.feedback_port:
            logger.warning("⚠️ No feedback port configured. Failure not recorded.")
            return

        feedback_data = {
            "error_type": "video_recognition",
            "correction": correction,
            "original_output": actual_output,
        }

        self.feedback_port.save_feedback(
            input_context=query,
            output_text=json.dumps(feedback_data),
            is_positive=False,
            user_id=user_id,
            feedback_type="skill_bank_entry",
        )
        logger.info(
            f"🧠 Skill Bank: Correction experience recorded for query: {query[:50]}..."
        )

    def _get_skill_bank_context(self, anime_title: str) -> str:
        """
        Récupère les expériences de correction pertinentes pour un anime ou un type de scène.
        """
        if not self.feedback_port:
            return ""

        # On récupère les feedbacks récents de type 'skill_bank_entry'
        recent_skills = self.feedback_port.get_recent_feedback(
            limit=5, feedback_type="skill_bank_entry"
        )

        if not recent_skills:
            return ""

        context_parts = []
        for skill in recent_skills:
            try:
                data = json.loads(skill["output_text"])
                # On ne garde que les corrections qui semblent sémantiquement liées (ou toutes les globales)
                context_parts.append(
                    f"- Échec précédent: {skill['input_context']} -> Correction: {data['correction']}"
                )
            except Exception:  # nosec B112
                continue

        return "\n".join(context_parts)

    def verify_and_evolve(
        self,
        video_data: bytes,
        generated_narrative: str,
        metadata: Dict[str, Any],
        user_id: Any = None,
    ):
        """
        Vérifie la qualité de la description et enregistre un échec si nécessaire.
        Boucle d'auto-évolution (Self-Evolving Loop).
        """
        title = metadata.get("title", "Unknown Anime")

        # Simulation d'une vérification croisée (ex: via un autre modèle plus puissant ou des métadonnées)
        # Dans un scénario réel, cela pourrait être déclenché par un feedback utilisateur 'incorrect'
        # ou par une détection d'hallucination via CoVe.

        logger.info(f"🔍 Skill Bank: Verifying narrative for {title}...")

        # Pour l'instant, on fournit une méthode manuelle de déclenchement d'évolution
        # qui pourra être appelée par l'admin ou le système XAI.
        return True

    def index_video_moment(self, video_data: bytes, metadata: Dict[str, Any]):
        """
        Pipeline complet : Vidéo -> Description Dense -> Indexation Vectorielle.
        """
        import uuid  # noqa: E402

        title = metadata.get("title", "Unknown Anime")

        try:
            narrative = self.generate_dense_video_description(video_data, title)
        except Exception as e:
            logger.error(f"❌ Failed to generate video narrative: {e}")
            return None

        if narrative and self.repository:
            try:
                # 1. Génération de l'embedding du texte
                embedding = self.inference_engine.get_text_embedding(narrative)

                # 2. Création d'un ID unique
                safe_title = "".join([c if c.isalnum() else "_" for c in title])
                doc_id = f"video_{safe_title}_{uuid.uuid4().hex[:8]}"

                # 3. Indexation dans l'espace sémantique 'video_narratives'
                self.repository.upsert_items(
                    collection_name="video_narratives",
                    ids=[doc_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[narrative],
                )
                logger.info(
                    f"💾 Narrative indexed successfully for {title} (ID: {doc_id})."
                )
            except Exception as e:
                logger.error(f"❌ Failed to index narrative for {title}: {e}")

        return narrative

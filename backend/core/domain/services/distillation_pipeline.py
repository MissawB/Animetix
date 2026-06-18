import os
import json
import logging
from typing import List, Optional
from core.ports.inference_port import InferencePort
from core.ports.gold_dataset_port import GoldDatasetPort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")


class ModelDistillationPipeline:
    """
    Pipeline de Distillation : Entraîne un modèle étudiant (1B) à partir d'un enseignant (8B+).
    Protégé contre le Model Collapse via validation HITL.
    """

    def __init__(
        self,
        teacher_engine: InferencePort,
        prompt_manager: PromptManager,
        gold_dataset_port: Optional[GoldDatasetPort] = None,
    ):
        self.teacher = teacher_engine
        self.prompt_manager = prompt_manager
        self.gold_dataset_port = gold_dataset_port

    def generate_distillation_data(
        self, topics: List[str], count_per_topic: int = 10
    ) -> int:
        """
        Génère un dataset synthétique via le modèle Enseignant et le met en attente de validation.
        """
        if not self.gold_dataset_port:
            logger.error("❌ GoldDatasetPort missing. Cannot stage distillation data.")
            return 0

        count = 0
        for topic in topics:
            logger.info(f"🧠 Teacher generating knowledge for: {topic}...")
            prompt, system_prompt = self.prompt_manager.get_prompt(
                "distillation_explanation", topic=topic
            )
            explanation = self.teacher.generate(prompt, system_prompt=system_prompt)

            self.gold_dataset_port.save_synthetic_entry(
                entry_type="DISTILLATION",
                context=f"Topic: {topic}",
                instruction=f"Explique moi {topic}.",
                response=explanation,
                metadata={"topic": topic, "teacher": "teacher_8b"},
            )
            count += 1

        logger.info(
            f"⏳ {count} distillation pairs staged for human validation (HITL)."
        )
        return count

    def fine_tune_student(
        self, student_model_id: str = "Qwen/Qwen3-0.6B", epochs: float = 3.0
    ):
        """
        Lance le fine-tuning du modèle étudiant sur les données validées par l'humain.
        """
        if not self.gold_dataset_port:
            logger.error("❌ GoldDatasetPort missing. Cannot fetch validated data.")
            return

        logger.info(f"🚀 Preparing Student Model Fine-tuning: {student_model_id}")

        # On ne récupère que les données VALIDÉES pour éviter le Model Collapse
        validated_entries = self.gold_dataset_port.get_unprocessed_validated_entries()
        distill_data = [
            e
            for e in validated_entries
            if e.get("entry_type") == "DISTILLATION" or e.get("entry_type") == "QA"
        ]

        if not distill_data:
            logger.warning(
                "⚠️ No validated synthetic data available for fine-tuning. Skipping."
            )
            return

        # Enregistrement temporaire des données pour le script d'entraînement
        data_dir = "data/mlops/datasets"
        os.makedirs(data_dir, exist_ok=True)
        data_path = os.path.join(data_dir, "trl_train_data.jsonl")

        with open(data_path, "w", encoding="utf-8") as f:
            for item in distill_data:
                # Formatage pour TRL
                f.write(
                    json.dumps(
                        {
                            "instruction": item["instruction"],
                            "output": item["response"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        logger.info(
            f"📊 {len(distill_data)} validated examples prepared at {data_path}."
        )

        # Appel de la logique d'entraînement (Import local)
        from scripts.distill_draft_model import train_speculative_draft_model  # noqa: E402

        output_dir = f"checkpoints/distilled-{student_model_id.split('/')[-1]}"

        try:
            train_speculative_draft_model(
                student_model_id=student_model_id, output_dir=output_dir, epochs=epochs
            )
            # Une fois l'entraînement fini, on marque les données comme traitées
            self.gold_dataset_port.mark_entries_as_processed(
                [e["id"] for e in distill_data]
            )
            logger.info(f"✅ Training completed. Model saved at {output_dir}")
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            raise

    def extract_golden_patterns(self, prompt_key: str) -> str:
        """
        Analyse le Gold Dataset pour extraire les 'Golden Patterns' (clés du succès).
        Ces patterns sont ensuite injectés dans les System Prompts via le PromptManager.
        """
        # Chemin vers le Gold Dataset défini dans le projet
        gold_path = "data/mlops/gold_dataset.json"
        if not os.path.exists(gold_path):
            logger.warning(
                f"⚠️ Gold Dataset missing at {gold_path}. Cannot extract patterns."
            )
            return ""

        try:
            with open(gold_path, "r", encoding="utf-8") as f:
                gold_data = json.load(f)

            # Filtrer les entrées correspondant à la clé du prompt (ex: 'fusion_scenario')
            # On prend les 5 meilleurs exemples validés
            relevant_examples = [
                item
                for item in gold_data
                if item.get("prompt_key") == prompt_key and item.get("is_gold", True)
            ][:5]

            if not relevant_examples:
                logger.info(
                    f"ℹ️ No gold examples found for '{prompt_key}'. Skipping extraction."
                )
                return ""

            logger.info(
                f"🌟 Extracting Golden Patterns for '{prompt_key}' from {len(relevant_examples)} examples..."
            )

            # Construction du prompt pour le modèle Enseignant (Meta-Prompting)
            examples_str = json.dumps(relevant_examples, indent=2, ensure_ascii=False)
            analysis_prompt = (
                f"Voici une liste d'exemples 'Gold' (réussites parfaites) pour le prompt '{prompt_key}' :\n\n"
                f"{examples_str}\n\n"
                "Analyse ces exemples et identifie les 'Golden Patterns' (structure, ton, vocabulaire, règles implicites) "
                "qui garantissent la qualité. Résume ces patterns sous forme de directives claires pour un assistant IA."
            )

            system_prompt = (
                "Tu es un expert en Meta-Prompting et Ingénierie de la connaissance."
            )

            # Le modèle enseignant (8B+) analyse les données gold
            golden_patterns = self.teacher.generate(
                analysis_prompt, system_prompt=system_prompt
            )

            if golden_patterns:
                logger.info(f"✅ Golden Patterns extracted for '{prompt_key}'.")
                # Injection automatique dans le PromptManager
                current_system = self.prompt_manager.get_system_prompt(prompt_key)
                # On ajoute les patterns au début du system prompt
                new_system = f"--- GOLDEN PATTERNS (DO NOT IGNORE) ---\n{golden_patterns}\n\n{current_system}"
                self.prompt_manager.update_system_prompt(prompt_key, new_system)
                return golden_patterns

            return ""
        except Exception as e:
            logger.error(f"❌ Failed to extract golden patterns for {prompt_key}: {e}")
            return ""

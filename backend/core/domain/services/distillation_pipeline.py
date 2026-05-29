import os
import json
import logging
from typing import List, Dict
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")

class ModelDistillationPipeline:
    """
    Pipeline de Distillation : Entraîne un modèle étudiant (1B) à partir d'un enseignant (8B+).
    """
    def __init__(self, teacher_engine: InferencePort, prompt_manager: PromptManager):
        self.teacher = teacher_engine
        self.prompt_manager = prompt_manager

    def generate_distillation_data(self, topics: List[str], count_per_topic: int = 10) -> List[Dict]:
        """
        Génère un dataset synthétique de haute qualité via le modèle Enseignant.
        """
        synthetic_data = []
        for topic in topics:
            logger.info(f"🧠 Teacher generating knowledge for: {topic}...")
            prompt, system_prompt = self.prompt_manager.get_prompt("distillation_explanation", topic=topic)
            explanation = self.teacher.generate(prompt, system_prompt=system_prompt)
            
            synthetic_data.append({
                "instruction": f"Explique moi {topic}.",
                "output": explanation
            })
        return synthetic_data

    def fine_tune_student(self, train_data: List[Dict], student_model_id: str = "HuggingFaceTB/SmolLM-135M", epochs: float = 3.0):
        """
        Lance le fine-tuning REEL du modèle étudiant sur les données distillées.
        """
        logger.info(f"🚀 Fine-tuning Student Model: {student_model_id}")
        
        # Enregistrement temporaire des données pour le script d'entraînement
        data_dir = "data/mlops/datasets"
        os.makedirs(data_dir, exist_ok=True)
        data_path = os.path.join(data_dir, "trl_train_data.jsonl")
        
        with open(data_path, "w", encoding="utf-8") as f:
            for item in train_data:
                f.write(json.dumps(item) + "\n")
        
        logger.info(f"📊 Dataset prepared at {data_path} with {len(train_data)} examples.")
        
        # Appel de la logique d'entraînement (Import local pour éviter les dépendances circulaires)
        from scripts.distill_draft_model import train_speculative_draft_model
        
        output_dir = f"checkpoints/distilled-{student_model_id.split('/')[-1]}"
        
        try:
            train_speculative_draft_model(
                student_model_id=student_model_id,
                output_dir=output_dir,
                epochs=epochs
            )
            logger.info(f"✅ Training completed successfully. Model saved at {output_dir}")
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
            logger.warning(f"⚠️ Gold Dataset missing at {gold_path}. Cannot extract patterns.")
            return ""

        try:
            with open(gold_path, "r", encoding="utf-8") as f:
                gold_data = json.load(f)
            
            # Filtrer les entrées correspondant à la clé du prompt (ex: 'fusion_scenario')
            # On prend les 5 meilleurs exemples validés
            relevant_examples = [
                item for item in gold_data 
                if item.get("prompt_key") == prompt_key and item.get("is_gold", True)
            ][:5]

            if not relevant_examples:
                logger.info(f"ℹ️ No gold examples found for '{prompt_key}'. Skipping extraction.")
                return ""

            logger.info(f"🌟 Extracting Golden Patterns for '{prompt_key}' from {len(relevant_examples)} examples...")
            
            # Construction du prompt pour le modèle Enseignant (Meta-Prompting)
            examples_str = json.dumps(relevant_examples, indent=2, ensure_ascii=False)
            analysis_prompt = (
                f"Voici une liste d'exemples 'Gold' (réussites parfaites) pour le prompt '{prompt_key}' :\n\n"
                f"{examples_str}\n\n"
                "Analyse ces exemples et identifie les 'Golden Patterns' (structure, ton, vocabulaire, règles implicites) "
                "qui garantissent la qualité. Résume ces patterns sous forme de directives claires pour un assistant IA."
            )
            
            system_prompt = "Tu es un expert en Meta-Prompting et Ingénierie de la connaissance."
            
            # Le modèle enseignant (8B+) analyse les données gold
            golden_patterns = self.teacher.generate(analysis_prompt, system_prompt=system_prompt)
            
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

import os
import json
import torch
import logging
from typing import List, Dict
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
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

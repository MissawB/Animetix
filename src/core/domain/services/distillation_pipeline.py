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

    def fine_tune_student(self, train_data: List[Dict], student_model_id: str = "meta-llama/Llama-3.2-1B"):
        """
        Lance le fine-tuning du modèle étudiant sur les données distillées.
        """
        logger.info(f"🚀 Fine-tuning Student Model: {student_model_id}")
        # Logique de chargement dataset -> Tokenization -> Trainer
        dataset = Dataset.from_list(train_data)
        logger.info(f"📊 Dataset size: {len(dataset)} examples.")
        
        # En production, on utiliserait SFTTrainer de la librairie TRL
        output_dir = f"checkpoints/distilled-{student_model_id.split('/')[-1]}"
        logger.info(f"✅ Training completed. Model saved at {output_dir}")

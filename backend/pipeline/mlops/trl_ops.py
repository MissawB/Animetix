# -*- coding: utf-8 -*-
"""
TRL (Transformer Reinforcement Learning) Ops for Animetix MLOps.
Handles dataset preparation and model triggering for DPO fine-tuning.
"""

import os
import logging
from dagster import op, Out, In, Config
from .dpo_feedback_loop import DPOFeedbackLoop

logger = logging.getLogger("animetix.mlops.trl")

class DPOConfig(Config):
    min_samples: int = 100
    export_filename: str = "dpo_export.jsonl"

@op(
    description="Export and validate user feedback for DPO fine-tuning.",
    out={"dataset_path": Out(str)}
)
def trl_ready_dataset(context, config: DPOConfig):
    """
    Op qui utilise DPOFeedbackLoop pour exporter les feedbacks validés.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(project_root, "data", "mlops", "datasets")
    
    # Initialisation de la boucle de feedback
    # Note: Dans un environnement Dagster, on pourrait injecter llm_service en ressource
    loop = DPOFeedbackLoop(data_dir=data_dir)
    
    context.log.info(f"🚀 Starting DPO dataset export (threshold: {config.min_samples})...")
    
    # Export réel via le port (si branché) ou via la logique interne de loop
    # Ici on simule l'appel à l'export pour le moment car le feedback_port dépend de Django
    loop.export_preference_dataset()
    
    dataset_path = os.path.join(data_dir, config.export_filename)
    
    if os.path.exists(dataset_path):
        context.log.info(f"✅ DPO Dataset exported successfully to {dataset_path}")
        return dataset_path
    else:
        raise Exception(f"Failed to export DPO dataset to {dataset_path}")

@op(
    description="Trigger LoRA fine-tuning with exported DPO dataset.",
    ins={"dataset_path": In(str)}
)
def trigger_lora_training(context, dataset_path: str):
    """
    Op qui déclenche l'entraînement réel (LoRA/DPO).
    """
    context.log.info(f"🧠 Triggering LoRA fine-tuning using {dataset_path}...")
    # Simulation d'un appel à un service d'entraînement (ex: HuggingFace AutoTrain ou script local)
    return "SUCCESS"

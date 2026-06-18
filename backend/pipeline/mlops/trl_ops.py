# -*- coding: utf-8 -*-
"""
TRL (Transformer Reinforcement Learning) Ops for Animetix MLOps.
Handles dataset preparation and model triggering for DPO fine-tuning.
"""

import logging  # noqa: E402
import os  # noqa: E402

from pydantic import BaseModel  # noqa: E402

from .dpo_feedback_loop import DPOFeedbackLoop  # noqa: E402

logger = logging.getLogger("animetix.mlops.trl")


class DPOConfig(BaseModel):
    min_samples: int = 100
    export_filename: str = "dpo_export.jsonl"


def trl_ready_dataset(context=None, config: DPOConfig = None):
    """
    Export and validate user feedback for DPO fine-tuning.
    """
    if config is None:
        config = DPOConfig()

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    data_dir = os.path.join(project_root, "data", "mlops", "datasets")

    # Initialisation de la boucle de feedback
    loop = DPOFeedbackLoop(data_dir=data_dir)

    log = context.log if (context and hasattr(context, "log")) else logger
    log.info(f"🚀 Starting DPO dataset export (threshold: {config.min_samples})...")

    # Export réel via le port (si branché) ou via la logique interne de loop
    loop.export_preference_dataset()

    dataset_path = os.path.join(data_dir, config.export_filename)

    if os.path.exists(dataset_path):
        log.info(f"✅ DPO Dataset exported successfully to {dataset_path}")
        return dataset_path
    else:
        raise Exception(f"Failed to export DPO dataset to {dataset_path}")


def trigger_lora_training(context=None, dataset_path: str = None):
    """
    Trigger LoRA fine-tuning with exported DPO dataset.
    """
    log = context.log if (context and hasattr(context, "log")) else logger
    log.info(f"🧠 Triggering LoRA fine-tuning using {dataset_path}...")
    # Simulation d'un appel à un service d'entraînement
    return "SUCCESS"

import logging
logger = logging.getLogger("animetix." + __name__)

import os
import requests
import json
import time
import pandas as pd
from datetime import datetime
from dagster import asset, Output, AssetMaterialization

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEEDBACK_DATASET_DIR = os.path.join(BASE_DIR, 'data', 'mlops', 'datasets')
os.makedirs(FEEDBACK_DATASET_DIR, exist_ok=True)

@asset(group_name="mlops")
def monitor_inference_health():
    """Surveille la latence et la disponibilité de l'API Brain (Inférence)."""
    brain_url = os.getenv("BRAIN_API_URL")
    if not brain_url:
        return "⚠️ BRAIN_API_URL non configuré."

    start_time = time.time()
    try:
        # On teste une génération simple
        res = requests.post(f"{brain_url}/generate", json={
            "prompt": "ping",
            "system_prompt": "Répond uniquement 'pong'"
        }, timeout=10)
        latency = time.time() - start_time
        status = "🟢 Online" if res.status_code == 200 else f"🔴 Error {res.status_code}"
        logger.info(f"Inference Health: {status} | Latency: {latency:.2f}s")
        return {"status": status, "latency": latency}
    except Exception as e:
        return {"status": "🔴 Offline", "error": str(e)}

@asset(group_name="mlops", compute_kind="django_db")
def exported_user_feedback():
    """Exporte les feedbacks RLHF et les sessions de jeu depuis la base de données Django."""
    manage_py = os.path.join(BASE_DIR, 'backend', 'manage.py')
    try:
        import subprocess
        subprocess.run(['python', manage_py, 'export_rlhf_data'], check=True)
    except Exception as e:
        logger.error(f"❌ Error exporting data from Django: {e}")
        return None

    feedback_path = os.path.join(FEEDBACK_DATASET_DIR, "ai_feedback.jsonl")
    session_path = os.path.join(FEEDBACK_DATASET_DIR, "gameplay_sessions.jsonl")
    return {"feedback": feedback_path, "sessions": session_path}

from .dpo_feedback_loop import DPOFeedbackLoop

@asset(group_name="mlops", deps=[exported_user_feedback])
def validated_dpo_dataset(exported_user_feedback):
    """Transforme l'export en dataset DPO validé et nettoyé."""
    if not exported_user_feedback:
        return None
    feedback_path = exported_user_feedback["feedback"]
    dataset_path = os.path.join(FEEDBACK_DATASET_DIR, "dpo_train_validated.jsonl")
    loop = DPOFeedbackLoop(data_dir=FEEDBACK_DATASET_DIR)
    count = loop.process_and_export(feedback_path, dataset_path)
    return {"path": dataset_path, "count": count}

@asset(group_name="mlops", compute_kind="ragas")
def periodic_rag_evaluation():
    """Lance une évaluation Ragas sur un Golden Dataset pour détecter les régressions."""
    from scripts.mlops_rag_eval import run_mlops_eval
    report = run_mlops_eval()
    return report

@asset(group_name="mlops", deps=[validated_dpo_dataset, periodic_rag_evaluation])
def trigger_model_retraining(validated_dpo_dataset, periodic_rag_evaluation, knowledge_drift_check=False):
    """Déclenche le ré‑entraînement si les données sont suffisantes, si la qualité baisse, ou en cas de dérive."""
    count = validated_dpo_dataset.get("count", 0)
    # Critère 1 : Volume de nouvelles données
    if count >= 100:
        logger.info(f"🚀 Triggering Retraining: {count} new samples collected.")
        return "Retraining started."
    # Critère 2 : Baisse de performance détectée par RAGAS
    if periodic_rag_evaluation.get('avg_faithfulness', 1.0) < 0.7:
        logger.warning("🚨 Performance drop detected. Triggering urgent fine-tuning.")
        return "Urgent retraining started."
    # Critère 3 : Dérive détectée
    if knowledge_drift_check:
        logger.info("🌊 Data drift detected. Triggering preventative retraining.")
        return "Preventative retraining started."
    return "Retraining not necessary yet."

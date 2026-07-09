import logging

logger = logging.getLogger("animetix." + __name__)

import os  # noqa: E402
import time  # noqa: E402

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEEDBACK_DATASET_DIR = os.path.join(BASE_DIR, "data", "mlops", "datasets")
os.makedirs(FEEDBACK_DATASET_DIR, exist_ok=True)

# Fix path for internal imports
import sys  # noqa: E402

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from core.utils.security import safe_http_request  # noqa: E402


def monitor_inference_health():
    """Surveille la latence et la disponibilité de l'API Brain (Inférence)."""
    brain_url = os.getenv("BRAIN_API_URL")
    brain_api_key = os.getenv("BRAIN_API_KEY", "dev-secret-key")
    if not brain_url:
        return "⚠️ BRAIN_API_URL non configuré."

    start_time = time.time()
    try:
        # On teste une génération simple via safe_http_request
        # Assurez-vous que l'URL se termine par /generate
        actual_url = (
            f"{brain_url}/generate"
            if not brain_url.endswith("/generate")
            else brain_url
        )
        res = safe_http_request(
            "POST",
            actual_url,
            json={"prompt": "ping", "system_prompt": "Répond uniquement 'pong'"},
            headers={"X-API-Key": brain_api_key},
            timeout=10,
            allow_internal=True,
        )
        latency = time.time() - start_time
        status = (
            "🟢 Online" if res.status_code == 200 else f"🔴 Error {res.status_code}"
        )
        logger.info(f"Inference Health: {status} | Latency: {latency:.2f}s")
        return {"status": status, "latency": latency}
    except Exception as e:
        return {"status": "🔴 Offline", "error": str(e)}


def exported_user_feedback():
    """Exporte les feedbacks RLHF et les sessions de jeu depuis la base de données Django."""
    manage_py = os.path.join(BASE_DIR, "api", "manage.py")
    try:
        import subprocess  # noqa: E402

        subprocess.run([sys.executable, manage_py, "export_rlhf_data"], check=True)
    except Exception as e:
        logger.error(f"[ERROR] Error exporting data from Django: {e}")
        return None

    feedback_path = os.path.join(FEEDBACK_DATASET_DIR, "ai_feedback.jsonl")
    session_path = os.path.join(FEEDBACK_DATASET_DIR, "gameplay_sessions.jsonl")
    return {"feedback": feedback_path, "sessions": session_path}


def run_sql_quality_checks():
    """Runs dbt data quality checks via Django management command before compilation."""
    manage_py = os.path.join(BASE_DIR, "api", "manage.py")
    try:
        import subprocess  # noqa: E402

        logger.info("Executing SQL database quality checks via dbt...")
        # In test/dev environment, we might exclude BigQuery checks if offline, but standard is to run both
        exclude_bq = os.getenv("MLOPS_OFFLINE_MODE", "false").lower() == "true"
        cmd = [sys.executable, manage_py, "run_data_quality_tests"]
        if exclude_bq:
            cmd.append("--exclude-bigquery")

        subprocess.run(cmd, check=True, capture_output=True, text=True)  # nosec B603
        logger.info("[SUCCESS] SQL database quality checks passed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            f"[ERROR] SQL data quality validation failed:\n{e.stderr or e.stdout}"
        )
        raise RuntimeError(
            "Training aborted due to data quality violations in SQL tables."
        ) from e


from .dpo_feedback_loop import DPOFeedbackLoop  # noqa: E402


def validated_dpo_dataset(exported_user_feedback):
    """Transforme l'export en dataset DPO validé et nettoyé."""
    if not exported_user_feedback:
        return None

    # Run database quality checks before compilation
    run_sql_quality_checks()

    feedback_path = exported_user_feedback["feedback"]
    dataset_path = os.path.join(FEEDBACK_DATASET_DIR, "dpo_train_validated.jsonl")
    loop = DPOFeedbackLoop(data_dir=FEEDBACK_DATASET_DIR)
    count = loop.process_and_export(feedback_path, dataset_path)
    return {"path": dataset_path, "count": count}


def periodic_rag_evaluation():
    """Lance une évaluation Ragas sur un Golden Dataset pour détecter les régressions."""
    from scripts.mlops_rag_eval import run_mlops_eval  # noqa: E402

    report = run_mlops_eval()
    return report


def trigger_model_retraining(
    validated_dpo_dataset, periodic_rag_evaluation, knowledge_drift_check=False
):
    """Déclenche le ré‑entraînement si les données sont suffisantes, si la qualité baisse, ou en cas de dérive."""
    count = validated_dpo_dataset.get("count", 0)
    # Critère 1 : Volume de nouvelles données
    if count >= 100:
        logger.info(f"🚀 Triggering Retraining: {count} new samples collected.")
        return "Retraining started."
    # Critère 2 : Baisse de performance détectée par RAGAS
    if periodic_rag_evaluation.get("avg_faithfulness", 1.0) < 0.7:
        logger.warning("🚨 Performance drop detected. Triggering urgent fine-tuning.")
        return "Urgent retraining started."
    # Critère 3 : Dérive détectée
    if knowledge_drift_check:
        logger.info("🌊 Data drift detected. Triggering preventative retraining.")
        return "Preventative retraining started."
    return "Retraining not necessary yet."

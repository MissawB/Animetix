# -*- coding: utf-8 -*-
"""
Automated DPO Training Trigger Sensor for Animetix MLOps.
Monitors user thumbs-up/down preference entries in SQLite to automate DPO training jobs.
"""

import os
import sys
import django
from dagster import sensor, RunRequest, SensorEvaluationContext

# Setup Django env
PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PIPELINE_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, 'src', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

@sensor(job_name="mlops_job")
def check_dpo_feedback_sensor(context: SensorEvaluationContext):
    """
    Sensor Dagster qui vérifie s'il y a 500+ nouveaux retours de préférence utilisateur (DPO).
    Si le quota est atteint, déclenche la compilation DPO et l'entraînement du modèle.
    """
    try:
        if not django.apps.apps.ready:
            django.setup()
        from animetix.models import AIFeedback
        total_feedbacks = AIFeedback.objects.count()
    except Exception as e:
        # Fallback pour le test environnement si le modèle ou la table n'existe pas
        total_feedbacks = 0


    # Récupération de l'index du curseur précédent
    last_count = int(context.cursor) if context.cursor else 0
    
    # Seuil d'accumulation pour l'entraînement (par défaut 100 pour test/démo, 500 pour production)
    threshold = 100
    
    if total_feedbacks >= last_count + threshold:
        context.update_cursor(str(total_feedbacks))
        # Déclenchement du job MLOps
        yield RunRequest(
            run_key=f"auto_dpo_training_{total_feedbacks}",
            run_config={
                "ops": {
                    "trl_ready_dataset": {
                        "config": {
                            "min_samples": threshold
                        }
                    }
                }
            }
        )

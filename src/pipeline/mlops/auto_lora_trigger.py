import os
import sys
import django
from dagster import sensor, RunRequest, SensorEvaluationContext

# Setup Django env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'src', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

@sensor(job_name="mlops_job")
def check_gold_dataset_sensor(context: SensorEvaluationContext):
    """
    Sensor Dagster qui vérifie s'il y a 100+ nouvelles entrées GoldDataset validées.
    Si oui, déclenche le job d'entraînement (Fine-Tuning LoRA).
    """
    # Initialize Django to use ORM
    if not django.apps.apps.ready:
        django.setup()
        
    from animetix.models import GoldDatasetEntry
    
    # On compte les entrées validées qui n'ont pas encore été "consommées" pour un training.
    # Pour la démo, on vérifie juste s'il y en a plus de 100 au total, ou on pourrait 
    # rajouter un flag 'is_trained' dans le modèle.
    # Pour l'instant, on déclenche si count % 100 == 0 et count > 0 par rapport au dernier state.
    
    validated_count = GoldDatasetEntry.objects.filter(is_validated=True).count()
    
    # On récupère l'état précédent du sensor
    last_count = int(context.cursor) if context.cursor else 0
    
    if validated_count >= last_count + 100:
        context.update_cursor(str(validated_count))
        # Déclenche le job
        yield RunRequest(run_key=f"auto_lora_{validated_count}")

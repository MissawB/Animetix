import os
from celery import Celery

# Définir le module de réglages par défaut de Django pour le programme 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

app = Celery('animetix_project')

# Utiliser une chaîne ici pour ne pas avoir à sérialiser l'objet de configuration.
# - namespace='CELERY' signifie que toutes les clés de configuration liées à Celery 
#   doivent avoir un préfixe 'CELERY_'.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger les modules de tâches de toutes les configurations d'application Django enregistrées.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

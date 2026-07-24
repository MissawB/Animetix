"""Migration-drift guard.

Audit dette 2026-07-22: rien en CI/pre-commit n'exécutait `makemigrations
--check` ; le seul `migrate` a lieu au cold-start du conteneur
(deploy/supervisord.conf), donc un modèle modifié sans migration générée
n'était détecté qu'en prod. Ce test fait échouer le job pytest (CI + pre-push)
dès que les modèles et les fichiers de migration divergent.

test_settings hérite d'INSTALLED_APPS via `from .settings import *`, le graphe
inspecté ici est donc celui de la prod.
"""

import pytest
from django.core.management import call_command


@pytest.mark.django_db  # makemigrations lit l'historique appliqué (check_consistent_history)
def test_no_model_change_without_generated_migration():
    try:
        call_command("makemigrations", "--check", "--dry-run", verbosity=1)
    except SystemExit:
        pytest.fail(
            "Des modèles ont changé sans migration générée — lance "
            "`python backend/api/manage.py makemigrations` et committe le résultat."
        )

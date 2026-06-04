# Plafonds budgétaires Cloud Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Définir des limites de budget mensuel (Budget Caps) pour arrêter automatiquement le service Cloud Run `animetix-brain` (GPU L4) lorsque les seuils de dépenses mensuels du projet atteignent 100%.

**Architecture:** Mettre en place un budget facturation GCP publiant des alertes dans un topic Pub/Sub, relié via un abonnement Push à un webhook Django sécurisé par Google OIDC. Ce webhook utilise l'API Cloud Run v2 REST avec les identifiants par défaut (`google-auth`) pour mettre à l'échelle le service GPU à 0 instances (`maxInstanceCount: 0`).

**Tech Stack:** Python, Django, REST API, Google Auth, Pub/Sub, Cloud Run Admin API v2, gcloud CLI.

---

### Task 1: Configuration Django & Intégration API Cloud Run V2

**Files:**
- Modify: `backend/api/animetix_project/settings.py`
- Modify: `backend/api/animetix/services.py`
- Test: `tests/adapters/test_gcp_services.py`

- [ ] **Step 1: Ajouter les variables de configuration GCP dans `settings.py`**

Ajouter à la fin de `backend/api/animetix_project/settings.py` :
```python
# GCP Cloud Run & Billing Configuration
GCP_PROJECT_ID = env('GCP_PROJECT_ID', default='animetix')
GCP_BRAIN_SERVICE_NAME = env('GCP_BRAIN_SERVICE_NAME', default='animetix-brain')
GCP_BRAIN_REGION = env('GCP_BRAIN_REGION', default='europe-west1')
GCP_BILLING_WEBHOOK_URL = env('GCP_BILLING_WEBHOOK_URL', default='https://animetix-web-836616987676.europe-west9.run.app/api/billing/webhook/')
```

- [ ] **Step 2: Ajouter les méthodes GCP REST à `backend/api/animetix/services.py`**

Créer ou modifier le fichier `backend/api/animetix/services.py` :
```python
import google.auth
from google.auth.transport.requests import AuthorizedSession
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def shutdown_brain_service():
    """
    Shuts down the animetix-brain Cloud Run GPU service by setting maxInstanceCount to 0.
    """
    project_id = getattr(settings, 'GCP_PROJECT_ID', 'animetix')
    service_name = getattr(settings, 'GCP_BRAIN_SERVICE_NAME', 'animetix-brain')
    region = getattr(settings, 'GCP_BRAIN_REGION', 'europe-west1')
    
    logger.info(f"Initiating programmatic shutdown for Cloud Run service {service_name} in {region}...")
    
    try:
        credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        session = AuthorizedSession(credentials)
        
        url = f"https://{region}-run.googleapis.com/v2/projects/{project_id}/locations/{region}/services/{service_name}"
        params = {"updateMask": "template.scaling.maxInstanceCount"}
        data = {
            "template": {
                "scaling": {
                    "maxInstanceCount": 0
                }
            }
        }
        
        response = session.patch(url, params=params, json=data)
        if response.status_code == 200:
            logger.info(f"Successfully scaled service {service_name} to 0 instances. Budget Cap enforced.")
            return True, response.json()
        else:
            error_detail = response.text
            logger.error(f"Failed to shutdown Cloud Run service. Status code: {response.status_code}. Response: {error_detail}")
            return False, error_detail
            
    except Exception as e:
        logger.exception(f"Error during programmatic shutdown of service {service_name}: {e}")
        return False, str(e)

def restore_brain_service(max_instances=10):
    """
    Restores the animetix-brain Cloud Run GPU service by resetting maxInstanceCount to a positive value.
    """
    project_id = getattr(settings, 'GCP_PROJECT_ID', 'animetix')
    service_name = getattr(settings, 'GCP_BRAIN_SERVICE_NAME', 'animetix-brain')
    region = getattr(settings, 'GCP_BRAIN_REGION', 'europe-west1')
    
    logger.info(f"Restoring Cloud Run service {service_name} to maxInstanceCount={max_instances}...")
    
    try:
        credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        session = AuthorizedSession(credentials)
        
        url = f"https://{region}-run.googleapis.com/v2/projects/{project_id}/locations/{region}/services/{service_name}"
        params = {"updateMask": "template.scaling.maxInstanceCount"}
        data = {
            "template": {
                "scaling": {
                    "maxInstanceCount": max_instances
                }
            }
        }
        
        response = session.patch(url, params=params, json=data)
        if response.status_code == 200:
            logger.info(f"Successfully restored service {service_name} to {max_instances} instances.")
            return True, response.json()
        else:
            error_detail = response.text
            logger.error(f"Failed to restore Cloud Run service. Status: {response.status_code}. Response: {error_detail}")
            return False, error_detail
            
    except Exception as e:
        logger.exception(f"Error during restoration of service {service_name}: {e}")
        return False, str(e)
```

- [ ] **Step 3: Écrire les tests unitaires pour valider les fonctions de services GCP**

Créer `tests/adapters/test_gcp_services.py` :
```python
import pytest
from unittest.mock import patch, MagicMock
from animetix.services import shutdown_brain_service, restore_brain_service

@patch('google.auth.default')
@patch('google.auth.transport.requests.AuthorizedSession.patch')
def test_shutdown_brain_service_success(mock_patch, mock_default):
    mock_default.return_value = (MagicMock(), "test-project")
    mock_patch.return_value = MagicMock(status_code=200, json=lambda: {"name": "animetix-brain"})
    
    success, result = shutdown_brain_service()
    assert success is True
    assert result == {"name": "animetix-brain"}
    mock_patch.assert_called_once()

@patch('google.auth.default')
@patch('google.auth.transport.requests.AuthorizedSession.patch')
def test_restore_brain_service_success(mock_patch, mock_default):
    mock_default.return_value = (MagicMock(), "test-project")
    mock_patch.return_value = MagicMock(status_code=200, json=lambda: {"name": "animetix-brain"})
    
    success, result = restore_brain_service(5)
    assert success is True
    assert mock_patch.call_args[1]['json']['template']['scaling']['maxInstanceCount'] == 5
```

- [ ] **Step 4: Exécuter les tests GCP Services**

Run: `pytest tests/adapters/test_gcp_services.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix_project/settings.py backend/api/animetix/services.py tests/adapters/test_gcp_services.py
git commit -m "feat: configure GCP service credentials and Cloud Run V2 REST helper methods"
```

---

### Task 2: Implémentation du Webhook Django et OIDC Jeton Vérification

**Files:**
- Create: `backend/api/animetix/views/billing.py`
- Modify: `backend/api/animetix/urls/api.py`
- Test: `tests/adapters/test_billing_webhook.py`

- [ ] **Step 1: Créer le fichier `backend/api/animetix/views/billing.py`**

```python
import json
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from animetix_project.logging_config import get_logger
from animetix.services import shutdown_brain_service

logger = get_logger("animetix." + __name__)

@csrf_exempt
def billing_alert_webhook(request):
    """
    Webhook triggered by Pub/Sub billing alerts. Scales the animetix-brain
    service to 0 if the budget is reached.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    is_prod = getattr(settings, 'IS_PRODUCTION', False) or not settings.DEBUG
    if is_prod:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Missing or invalid authorization header"}, status=401)
        
        token = auth_header.split(" ")[1]
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests
            # Verify token signature against the exact webhook URL audience
            audience = getattr(settings, 'GCP_BILLING_WEBHOOK_URL', 'https://animetix-web-836616987676.europe-west9.run.app/api/billing/webhook/')
            id_token.verify_oauth2_token(token, requests.Request(), audience=audience)
        except Exception as e:
            logger.error(f"OIDC token verification failed: {e}")
            return JsonResponse({"error": "Invalid OIDC token"}, status=403)

    try:
        payload = json.loads(request.body)
        message = payload.get("message", {})
        pubsub_data_b64 = message.get("data")
        if not pubsub_data_b64:
            return JsonResponse({"error": "No pubsub data found in message"}, status=400)
            
        decoded_bytes = base64.b64decode(pubsub_data_b64)
        billing_alert = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as parse_err:
        logger.error(f"Failed to parse billing alert payload: {parse_err}")
        return JsonResponse({"error": "Invalid JSON or base64 payload"}, status=400)

    cost_amount = billing_alert.get("costAmount", 0.0)
    budget_amount = billing_alert.get("budgetAmount", 0.0)
    budget_name = billing_alert.get("budgetDisplayName", "unknown")
    
    logger.info(f"Billing Alert received from '{budget_name}': costAmount={cost_amount}, budgetAmount={budget_amount}")

    # Enforce cap if budget is reached or exceeded
    if budget_amount > 0 and cost_amount >= budget_amount:
        logger.warning(f"Budget Cap Exceeded ({cost_amount} >= {budget_amount})! Initiating shutdown.")
        success, info = shutdown_brain_service()
        if success:
            return JsonResponse({"status": "shutdown_triggered", "info": info})
        else:
            return JsonResponse({"status": "shutdown_failed", "error": info}, status=500)
            
    return JsonResponse({"status": "ignored", "cost": cost_amount, "budget": budget_amount})
```

- [ ] **Step 2: Enregistrer la route du webhook dans `backend/api/animetix/urls/api.py`**

Ajouter l'import et la route dans `backend/api/animetix/urls/api.py` :
```python
from ..views.billing import billing_alert_webhook

# Dans urlpatterns :
urlpatterns += [
    path('billing/webhook/', billing_alert_webhook, name='api_billing_webhook'),
]
```

- [ ] **Step 3: Écrire les tests unitaires pour le webhook**

Créer `tests/adapters/test_billing_webhook.py` :
```python
import json
import base64
import pytest
from django.urls import reverse
from django.test import Client
from unittest.mock import patch, MagicMock

@pytest.fixture
def api_client():
    return Client()

@patch('animetix.views.billing.shutdown_brain_service')
def test_webhook_ignored_when_under_budget(mock_shutdown, api_client):
    mock_shutdown.return_value = (True, "mocked")
    # Budget $100, cost $50
    alert_data = {
        "costAmount": 50.0,
        "budgetAmount": 100.0,
        "budgetDisplayName": "Test Budget"
    }
    encoded_data = base64.b64encode(json.dumps(alert_data).encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": {
            "data": encoded_data
        }
    }
    
    url = reverse('api_billing_webhook')
    response = api_client.post(url, data=json.dumps(payload), content_type="application/json")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    mock_shutdown.assert_not_called()

@patch('animetix.views.billing.shutdown_brain_service')
def test_webhook_shutdown_when_budget_exceeded(mock_shutdown, api_client):
    mock_shutdown.return_value = (True, {"status": "ok"})
    # Budget $100, cost $105
    alert_data = {
        "costAmount": 105.0,
        "budgetAmount": 100.0,
        "budgetDisplayName": "Test Budget"
    }
    encoded_data = base64.b64encode(json.dumps(alert_data).encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": {
            "data": encoded_data
        }
    }
    
    url = reverse('api_billing_webhook')
    response = api_client.post(url, data=json.dumps(payload), content_type="application/json")
    
    assert response.status_code == 200
    assert response.json()["status"] == "shutdown_triggered"
    mock_shutdown.assert_called_once()
```

- [ ] **Step 4: Exécuter les tests du Webhook**

Run: `pytest tests/adapters/test_billing_webhook.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/views/billing.py backend/api/animetix/urls/api.py tests/adapters/test_billing_webhook.py
git commit -m "feat: add Django billing alert webhook with test coverage"
```

---

### Task 3: Commande de gestion CLI pour restaurer le service

**Files:**
- Create: `backend/api/animetix/management/commands/restore_brain_service.py`
- Test: `tests/adapters/test_restore_command.py`

- [ ] **Step 1: Créer la commande d'administration Django**

Créer `backend/api/animetix/management/commands/restore_brain_service.py` :
```python
from django.core.management.base import BaseCommand
from animetix.services import restore_brain_service

class Command(BaseCommand):
    help = "Restores the animetix-brain Cloud Run GPU service scale count."

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-instances',
            type=int,
            default=10,
            help='Maximum instance count to restore the service to'
        )

    def handle(self, *args, **options):
        max_instances = options['max_instances']
        self.stdout.write(f"Restoring animetix-brain with maxInstanceCount={max_instances}...")
        
        success, message = restore_brain_service(max_instances)
        if success:
            self.stdout.write(self.style.SUCCESS(f"Successfully restored service: {message}"))
        else:
            self.stderr.write(self.style.ERROR(f"Failed to restore service: {message}"))
```

- [ ] **Step 2: Créer le test pour la commande CLI**

Créer `tests/adapters/test_restore_command.py` :
```python
import pytest
from django.core.management import call_command
from unittest.mock import patch

@patch('animetix.management.commands.restore_brain_service.restore_brain_service')
def test_restore_command_success(mock_restore):
    mock_restore.return_value = (True, "restored-json")
    
    # Appel de la commande
    call_command('restore_brain_service', '--max-instances=5')
    
    mock_restore.assert_called_once_with(5)
```

- [ ] **Step 3: Exécuter le test de la commande**

Run: `pytest tests/adapters/test_restore_command.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/management/commands/restore_brain_service.py tests/adapters/test_restore_command.py
git commit -m "feat: add Django management command to restore brain service scale"
```

---

### Task 4: Script de déploiement automatique du budget sur GCP

**Files:**
- Create: `scripts/deploy/deploy_budget.py`

- [ ] **Step 1: Créer le script de déploiement `scripts/deploy/deploy_budget.py`**

```python
import subprocess
import sys
import shutil
import json
import os

def run_command(cmd_args, check=True):
    resolved_cmd = shutil.which(cmd_args[0])
    if resolved_cmd:
        cmd_args[0] = resolved_cmd
        
    print(f"Running: {' '.join(cmd_args)}")
    result = subprocess.run(cmd_args, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error executing command: {' '.join(cmd_args)}")
        print(f"Stdout:\n{result.stdout}")
        print(f"Stderr:\n{result.stderr}")
        if check:
            sys.exit(result.returncode)
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    return result

def main():
    project_id = "animetix"
    region = "europe-west9" # Region principal de Django
    brain_region = "europe-west1" # Inférence GPU L4
    topic_name = "animetix-budget-alerts"
    sub_name = "animetix-budget-alerts-push"
    
    # 1. Récupération dynamique du nom complet du compte de facturation (Billing Account)
    print("\n--- Step 1: Retrieving Billing Account ---")
    billing_desc = run_command([
        "gcloud", "billing", "projects", "describe", project_id,
        "--format=value(billingAccountName)"
    ])
    billing_account_name = billing_desc.stdout.strip()
    if not billing_account_name:
        print("Error: Could not retrieve Billing Account associated with the project.")
        sys.exit(1)
        
    # billing_account_name est sous la forme 'billingAccounts/XXXXXX-YYYYYY-ZZZZZZ'
    billing_account_id = billing_account_name.replace("billingAccounts/", "")
    print(f"Associated Billing Account ID is: {billing_account_id}")

    # 2. Création du Topic Pub/Sub
    print("\n--- Step 2: Creating Pub/Sub Topic ---")
    run_command([
        "gcloud", "pubsub", "topics", "create", topic_name,
        f"--project={project_id}"
    ], check=False)

    # 3. Récupération de l'URL du service Django animetix-web
    print("\n--- Step 3: Retrieving Django Webhook URL ---")
    web_url_desc = run_command([
        "gcloud", "run", "services", "describe", "animetix-web",
        f"--region={region}",
        "--format=value(status.url)",
        f"--project={project_id}"
    ])
    web_url = web_url_desc.stdout.strip()
    if not web_url:
        print("Error: Could not retrieve Django web service URL.")
        sys.exit(1)
        
    webhook_url = f"{web_url}/api/billing/webhook/"
    print(f"Webhook Push Endpoint is: {webhook_url}")

    # 4. Provisionnement du compte de service pour la souscription Pub/Sub push
    print("\n--- Step 4: Creating Subscription Invoker Service Account ---")
    invoker_sa = "animetix-budget-invoker"
    invoker_sa_email = f"{invoker_sa}@{project_id}.iam.gserviceaccount.com"
    run_command([
        "gcloud", "iam", "service-accounts", "create", invoker_sa,
        "--display-name=Service Account for PubSub Budget push subscription",
        f"--project={project_id}"
    ], check=False)

    # Autoriser ce SA à appeler le service animetix-web
    run_command([
        "gcloud", "run", "services", "add-iam-policy-binding", "animetix-web",
        f"--member=serviceAccount:{invoker_sa_email}",
        "--role=roles/run.invoker",
        f"--region={region}",
        f"--project={project_id}"
    ])

    # 5. Création de la souscription Pub/Sub Push sécurisée par OIDC
    print("\n--- Step 5: Creating Push Subscription ---")
    # Supprimer la souscription existante pour s'assurer que l'audience et l'URL sont correctes
    run_command([
        "gcloud", "pubsub", "subscriptions", "delete", sub_name,
        f"--project={project_id}"
    ], check=False)

    run_command([
        "gcloud", "pubsub", "subscriptions", "create", sub_name,
        f"--topic={topic_name}",
        f"--push-endpoint={webhook_url}",
        f"--push-auth-service-account={invoker_sa_email}",
        f"--push-auth-token-audience={webhook_url}",
        f"--project={project_id}"
    ])

    # 6. Attribution du rôle run.developer au service account Django sur la Brain API
    print("\n--- Step 6: Assigning IAM Permissions for django-web to manage animetix-brain ---")
    web_sa = f"836616987676-compute@developer.gserviceaccount.com"
    run_command([
        "gcloud", "run", "services", "add-iam-policy-binding", "animetix-brain",
        f"--member=serviceAccount:{web_sa}",
        "--role=roles/run.developer",
        f"--region={brain_region}",
        f"--project={project_id}"
    ])

    # 7. Création ou mise à jour du budget facturation
    print("\n--- Step 7: Configuring GCP Billing Budget ---")
    budget_name = "animetix-monthly-budget"
    
    # Supprimer le budget existant s'il existe pour éviter le doublon
    run_command([
        "gcloud", "beta", "billing", "budgets", "delete",
        f"projects/{project_id}/budgets/{budget_name}",
        f"--billing-account={billing_account_id}",
        f"--project={project_id}"
    ], check=False)
    
    # Création du budget à $100 relié au topic Pub/Sub
    run_command([
        "gcloud", "beta", "billing", "budgets", "create",
        f"--billing-account={billing_account_id}",
        f"--display-name={budget_name}",
        "--budget-amount=100USD",
        "--threshold-rule=percent=0.5,percent=0.9,percent=1.0",
        "--all-services",
        f"--pubsub-topic=projects/{project_id}/topics/{topic_name}",
        f"--project={project_id}"
    ])
    
    print("\n✅ Budget Caps and notifications successfully deployed on GCP project!")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/deploy/deploy_budget.py
git commit -m "infra: create deploy_budget.py script for automatic billing cap orchestration"
```

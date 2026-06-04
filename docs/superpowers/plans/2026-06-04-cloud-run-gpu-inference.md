# Inférence ML Lourde sur Cloud Run GPU Serverless Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Déployer la Brain API (FastAPI) sur Cloud Run avec GPU Nvidia L4 serverless (Belgique) et l'intégrer automatiquement au service web principal Django.

**Architecture:** Déploiement d'un service Cloud Run séparé `animetix-brain` avec GPU L4 (europe-west1) alimenté par un conteneur dédié construit à distance via Google Cloud Build. Liaison dynamique avec `animetix-web` (europe-west9) en mettant à jour sa variable d'environnement `BRAIN_API_URL`.

**Tech Stack:** Python, FastAPI, Docker, PyTorch, Uvicorn, Google Cloud SDK (gcloud CLI), Google Cloud Build.

---

### Task 1: Dockerfile pour la Brain API

**Files:**
- Create: `deploy/Dockerfile.brain`

- [ ] **Step 1: Créer le fichier Dockerfile.brain**

Créer `deploy/Dockerfile.brain` avec le contenu suivant :
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/backend:${PYTHONPATH}" \
    TORCH_HOME="/app/data/models/torch" \
    HF_HOME="/app/data/models/huggingface"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libpq5 \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/models/torch data/models/huggingface

EXPOSE 7861

CMD ["sh", "-c", "uvicorn adapters.inference.brain_api:app --host 0.0.0.0 --port ${PORT:-7861}"]
```

- [ ] **Step 2: Vérifier le Dockerfile localement via un dry-run de build**

Lancer une commande de validation locale de la syntaxe de build Docker :
Run: `docker build -f deploy/Dockerfile.brain --target=builder .` (Note: Ce step est optionnel si Docker n'est pas actif localement, mais valide la syntaxe).

- [ ] **Step 3: Commit**

```bash
git add deploy/Dockerfile.brain
git commit -m "infra: add Dockerfile.brain for Cloud Run GPU deployment"
```

---

### Task 2: Alignement et Enrichissement des Routes FastAPI de la Brain API

**Files:**
- Modify: `backend/adapters/inference/brain_api.py`
- Test: `tests/adapters/test_brain_api_routes.py`

- [ ] **Step 1: Écrire les tests unitaires manquants pour valider les nouvelles routes de la Brain API**

Créer le fichier de test `tests/adapters/test_brain_api_routes.py` pour tester le démarrage de l'app et les codes de retour (401 si pas de clé API).
```python
import pytest
from fastapi.testclient import TestClient
from adapters.inference.brain_api import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

def test_unauthenticated_generate():
    response = client.post("/generate", json={"prompt": "test"})
    assert response.status_code == 401
```

- [ ] **Step 2: Lancer les tests pour s'assurer qu'ils échouent ou passent selon le cas**

Run: `pytest tests/adapters/test_brain_api_routes.py -v`
Expected: PASS si l'API est initialisable de base avec le health check.

- [ ] **Step 3: Enrichir `backend/adapters/inference/brain_api.py` avec les nouvelles routes**

Remplacer le contenu de `backend/adapters/inference/brain_api.py` avec la version complète supportant toutes les routes (voir spécification Section B).

- [ ] **Step 4: Écrire les tests de succès avec authentification mockée**

Ajouter dans `tests/adapters/test_brain_api_routes.py` :
```python
def test_authenticated_generate(monkeypatch):
    # Mocking verify_api_key dependency
    from adapters.inference.brain_api import verify_api_key
    app.dependency_overrides[verify_api_key] = lambda: "valid-key"
    
    # Mock de unified_inference_adapter.generate
    class MockResponse:
        text = "Hello world"
        metadata = None
    
    from adapters.inference.brain_api import brain_engine
    monkeypatch.setattr(brain_engine, "generate", lambda *args, **kwargs: MockResponse())

    response = client.post("/generate", json={"prompt": "Bonjour"}, headers={"X-API-Key": "valid-key"})
    assert response.status_code == 200
    assert response.json()["text"] == "Hello world"
    
    app.dependency_overrides.clear()
```

- [ ] **Step 5: Exécuter à nouveau les tests**

Run: `pytest tests/adapters/test_brain_api_routes.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/adapters/inference/brain_api.py tests/adapters/test_brain_api_routes.py
git commit -m "feat: implement complete endpoints for Brain API FastAPI service"
```

---

### Task 3: Script de Déploiement et de Liaison Automatique

**Files:**
- Create: `scripts/deploy/deploy_brain.py`

- [ ] **Step 1: Créer le script `deploy_brain.py`**

Écrire la logique complète de build Cloud Build et de déploiement Cloud Run (avec `--gpu 1 --gpu-type=nvidia-l4 --cpu 4 --memory 16Gi --no-cpu-throttling`) dans `scripts/deploy/deploy_brain.py` (voir Section C de la spécification).

- [ ] **Step 2: Créer un test unitaire de validation pour le script de déploiement**

Créer `tests/deploy/test_deploy_brain.py` en mockant les appels subprocess :
```python
import subprocess
from unittest.mock import patch, MagicMock
from scripts.deploy.deploy_brain import main

@patch("subprocess.run")
def test_deploy_brain_calls_gcloud(mock_run):
    # Mock de subprocess.run pour renvoyer des retours réussis
    mock_run.return_value = MagicMock(returncode=0, stdout="https://brain-url.run.app\n")
    
    # Exécute sans crash
    main()
    
    # Vérifie qu'on a appelé gcloud builds submit
    calls = [call[0][0] for call in mock_run.call_args_list]
    assert any("builds" in c for c in calls)
    assert any("deploy" in c for c in calls)
    assert any("describe" in c for c in calls)
```

- [ ] **Step 3: Exécuter les tests de déploiement**

Run: `pytest tests/deploy/test_deploy_brain.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/deploy/deploy_brain.py tests/deploy/test_deploy_brain.py
git commit -m "infra: create deploy_brain.py script for Cloud Run GPU deployment"
```

---

### Task 4: Exécution du déploiement GCP et tests réels

**Files:**
- None (Opération GCP)

- [ ] **Step 1: Lancer le déploiement sur Google Cloud**

Run: `python scripts/deploy/deploy_brain.py`
Expected: Affichage de la progression du build, du déploiement en région `europe-west1`, de la récupération de l'URL et du succès de la mise à jour de `animetix-web`.

- [ ] **Step 2: Exécuter les tests de fumée pour valider l'adaptateur Django**

Valider que le Django local (ou en prod) communique correctement avec l'URL déployée.
Run: `python scripts/verify_brain_adapter.py`
Expected: PASS (ou confirmation de la connectivité via HTTP).

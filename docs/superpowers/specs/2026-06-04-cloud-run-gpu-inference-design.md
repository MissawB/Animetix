# Spécification - Inférence ML Lourde sur Cloud Run GPU Serverless

Ce document décrit le plan d'architecture et de déploiement de la Brain API (FastAPI) sur Google Cloud Run en utilisant des GPU Nvidia L4 serverless, avec une intégration automatique dans le service web Django principal (`animetix-web`).

---

## 1. Objectifs
- Déployer la Brain API (qui héberge les modèles d'inférence lourde comme XTTS, AudioLDM, MangaOCR, Stable Diffusion, etc.) sur Cloud Run avec accélération matérielle GPU Nvidia L4.
- Activer l'auto-scaling de 0 à N instances (scale-to-zero) pour optimiser les coûts en dehors des phases d'activité.
- Permettre le téléchargement dynamique des poids des modèles lors de la phase d'initialisation du conteneur (démarrage à froid).
- Automatiser le build de l'image de conteneur via Google Cloud Build (à distance).
- Automatiser la liaison entre la Brain API déployée en Belgique (`europe-west1`) et le service web principal situé à Paris (`europe-west9`).

---

## 2. Composants Impactés & Modifiés

### A. Dockerfile Brain API (Nouveau)
Création de `deploy/Dockerfile.brain` basé sur `python:3.11-slim`. Il installe les dépendances systèmes nécessaires (comme ffmpeg et libsndfile1), installe les packages requis de `requirements.txt` et lance l'application via Uvicorn en écoutant sur le port dynamique `$PORT`.

### B. Enrichissement de la Brain API (`backend/adapters/inference/brain_api.py`)
Mise à jour pour exposer l'ensemble des routes attendues par `BrainAPIAdapter` côté Django (modifications d'images, audio, TTS/clonage de voix, estimation 3D, diagnostics sémantiques, modération, etc.). Toutes les données binaires volumineuses seront transmises en base64 au format JSON.

### C. Script d'automatisation de déploiement (`scripts/deploy/deploy_brain.py`)
Nouveau script Python qui :
- Soumet le code de la Brain API à **Cloud Build** pour compiler l'image.
- Déploie le conteneur sur Cloud Run (`europe-west1`) avec 1 GPU L4, 4 vCPUs, 16 GiB RAM et `--no-cpu-throttling`.
- Configure les secrets (`BRAIN_API_KEY`, `HF_TOKEN`) depuis GCP Secret Manager.
- Récupère l'URL finale et met à jour dynamiquement la variable d'environnement `BRAIN_API_URL` du service `animetix-web` (GCP Paris).

---

## 3. Plan de Vérification et de Test

### Tests Unitaires & Intégration
- Validation de la syntaxe et du chargement de la Brain API FastAPI localement avec la commande :
  ```bash
  python backend/adapters/inference/brain_api.py
  ```
- Exécution du script de test de l'adaptateur :
  ```bash
  python scripts/verify_brain_adapter.py
  ```

### Vérification du Déploiement
- Exécuter le script de déploiement et valider qu'aucune erreur n'est remontée par la CLI `gcloud`.
- Inspecter l'état du service `animetix-brain` dans la console GCP Cloud Run pour s'assurer du bon statut "online" et de la détection correcte du GPU L4.
- Valider le lien fonctionnel en surveillant les logs de `animetix-web` lors d'un appel d'inférence.

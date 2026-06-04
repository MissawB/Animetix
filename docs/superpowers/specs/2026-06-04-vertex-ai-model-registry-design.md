# Design Spec - Vertex AI Model Registry & Volumes Mount FUSE (Cold Start Mitigation)

Ce document décrit l'architecture et les modifications requises pour versionner et héberger les modèles lourds d'inférence (MangaOCR et XTTS v2) sur Vertex AI Model Registry, et les connecter à Cloud Run via un montage de volume GCS FUSE pour éliminer le temps de téléchargement lors des cold starts.

---

## 1. Objectifs
- Réduire à zéro le temps d'attente lié au téléchargement des poids des modèles (MangaOCR et XTTS v2) depuis Hugging Face au démarrage à froid (Cold Start) des instances GPU L4.
- Versionner, documenter et cataloguer les modèles lourds utilisés par la Brain API au sein de **Vertex AI Model Registry**.
- Automatiser la création du bucket de modèles et l'enregistrement dans le registre via un script de déploiement idempotent.
- Adapter les adaptateurs d'inférence de la Brain API pour charger les poids localement depuis le volume FUSE si présent, avec repli transparent sur Hugging Face (Hugging Face Hub) en local ou en cas d'absence.

---

## 2. Architecture & Montage GCS FUSE

```mermaid
graph TD
    User[Utilisateur] -->|Requête Inférence| Django[Django Web]
    Django -->|Requête ML| CloudRun[Cloud Run GPU L4 - animetix-brain]
    CloudRun -->|1. Lecture directe ultra-rapide| FUSE[/mnt/models/ GCS FUSE]
    FUSE -.->|2. Flux à la demande| GCS[Bucket gs://animetix-models]
    Registry[Vertex AI Model Registry] -.->|Référence & Versioning| GCS
```

### Avantages de GCS FUSE sur Cloud Run
Plutôt que de télécharger 5 Go de poids de modèles en RAM à chaque démarrage d'instance (ce qui prend ~2 minutes et consomme de la mémoire), Cloud Run monte le bucket GCS contenant les poids directement en tant que répertoire local (`/mnt/models`). Les fichiers de poids sont mappés en mémoire et lus à la demande (streaming partiel), réduisant le démarrage à froid de la Brain API à quelques secondes.

---

## 3. Composants Impactés & Modifications

### A. Configuration de la Brain API (FastAPI)
Nous allons modifier la Brain API pour qu'elle lise la variable d'environnement `GCP_MODELS_MOUNT_PATH` (valeur par défaut : `/mnt/models`).

*   **Fichier :** [manga_ocr.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/manga_ocr.py)
    ```python
    mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
    local_model_path = os.path.join(mount_path, "manga-ocr")
    model_id = local_model_path if os.path.exists(local_model_path) else "microsoft/trocr-base-handwritten"
    ```

*   **Fichier :** [audio_mixin.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/audio_mixin.py)
    ```python
    mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
    local_model_path = os.path.join(mount_path, "xtts_v2")
    if os.path.exists(local_model_path):
        logger.info(f"🎙️ Loading XTTS Model from local FUSE path: {local_model_path}")
        self._tts_model = TTS(model_path=local_model_path)
    else:
        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        logger.info(f"🎙️ Loading XTTS Model from Hugging Face: {model_name}")
        self._tts_model = TTS(model_name)
    ```

### B. Script d'enregistrement de modèles (`register_models.py`)
Nous créons un nouveau script [register_models.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/scripts/deploy/register_models.py) pour enregistrer les métadonnées des modèles dans Vertex AI Model Registry :
1. Crée un bucket de stockage `gs://animetix-models` s'il n'existe pas.
2. Enregistre (téléversement logique) les métadonnées des modèles dans **Vertex AI Model Registry** avec l'URI de l'artefact pointant vers le bucket GCS.

```python
# scripts/deploy/register_models.py
# Utilise gcloud ai models upload pour cataloguer :
# Display Name: "manga-ocr" (URI: gs://animetix-models/manga-ocr)
# Display Name: "xtts_v2" (URI: gs://animetix-models/xtts_v2)
```

### C. Script de déploiement de la Brain API (`deploy_brain.py`)
Mise à jour de [deploy_brain.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/scripts/deploy/deploy_brain.py) pour :
1. Déclarer le volume et son montage dans Cloud Run :
   ```bash
   --add-volume=name=models-vol,type=cloud-storage,bucket=animetix-models
   --add-volume-mount=volume=models-vol,mount-path=/mnt/models
   ```
2. Déclarer la variable d'environnement `GCP_MODELS_MOUNT_PATH=/mnt/models` dans la commande de déploiement Cloud Run.

---

## 4. Plan de Vérification

### Tests Automatisés
- Écriture de `tests/deploy/test_deploy_brain_with_volumes.py` pour valider que `deploy_brain.py` intègre bien les arguments de volume et la nouvelle variable d'environnement.
- Validation des comportements de chargement local dans la Brain API par mock de l'existence des dossiers.

### Vérification Manuelle en Production
1. Exécuter le script d'enregistrement et de création de bucket :
   ```bash
   python scripts/deploy/register_models.py
   ```
2. Téléverser les fichiers de modèles dans le bucket `gs://animetix-models`.
3. Déployer la Brain API via `python scripts/deploy/deploy_brain.py` et s'assurer que Cloud Run se lance avec le volume FUSE monté.
4. Consulter les logs de démarrage pour valider la mention : *"Loading XTTS Model from local FUSE path"*.

# Vertex AI Model Registry & Cloud Run FUSE Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Vertex AI Model Registry for model tracking and enable Cloud Run GCS FUSE volume mounts to serve heavy model weights (MangaOCR, XTTS v2) locally inside the container, reducing cold start times.

**Architecture:** Update model loading in the Brain API to check for mounted local directory `/mnt/models` and dynamically load local files if present, falling back to Hugging Face downloads if absent. Create an idempotent Python script to build the GCS models bucket and register metadata in Vertex AI Model Registry. Add GCS Volume and Volume Mount options to the Cloud Run deployment script.

**Tech Stack:** FastAPI, PyTorch, TTS, Transformers, Google Cloud SDK (gcloud CLI), Python (subprocess), Pytest (mocking).

---

### Task 1: Update Brain API Model Loading

**Files:**
- Modify: `backend/adapters/inference/manga_ocr.py`
- Modify: `backend/adapters/inference/audio_mixin.py`

- [ ] **Step 1: Update manga_ocr.py to check local mount path**

Modify `backend/adapters/inference/manga_ocr.py` around line 24:
```python
            model_id = "microsoft/trocr-base-handwritten"
            if not hasattr(self, '_manga_ocr_pipeline'):
                logger.info("🏗️ Loading Manga OCR (fallback to generic OCR if specialized unavailable)...")
                
                # Check for mounted local volume
                mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
                local_model_path = os.path.join(mount_path, "manga-ocr")
                if os.path.exists(local_model_path):
                    logger.info(f"📚 Loading Manga OCR from local FUSE path: {local_model_path}")
                    model_id = local_model_path
                
                self._manga_ocr_pipeline = pipeline(
                    "image-to-text",
                    model=model_id,
                    device=0 if torch.cuda.is_available() else -1
                )
```

- [ ] **Step 2: Update audio_mixin.py to load XTTS from local mount path**

Modify `backend/adapters/inference/audio_mixin.py` around line 32:
```python
            from TTS.api import TTS
            
            # Check for mounted local volume
            mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
            local_model_path = os.path.join(mount_path, "xtts_v2")
            if os.path.exists(local_model_path):
                logger.info(f"🎙️ Loading XTTS Model from local FUSE path: {local_model_path}")
                self._tts_model = TTS(model_path=local_model_path)
            else:
                model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
                logger.info(f"🎙️ Loading XTTS Model from Hugging Face: {model_name}")
                self._tts_model = TTS(model_name)
                
            if torch.cuda.is_available(): self._tts_model.to("cuda")
```

---

### Task 2: Create Vertex AI Model Registry Script

**Files:**
- Create: `scripts/deploy/register_models.py`

- [ ] **Step 1: Write register_models.py script**

Create `scripts/deploy/register_models.py` with:
```python
import os
import subprocess
import sys
import shutil

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
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "animetix")
    region = os.getenv("GCP_BRAIN_REGION", "europe-west1")
    bucket_name = f"{project_id}-models"
    
    # 1. Enable Vertex AI API
    print("Step 1: Enabling Vertex AI API...")
    run_command([
        "gcloud", "services", "enable", "aiplatform.googleapis.com",
        f"--project={project_id}"
    ])
    
    # 2. Check/Create GCS models bucket
    print(f"\nStep 2: Checking storage bucket 'gs://{bucket_name}'...")
    check_bucket = run_command([
        "gcloud", "storage", "buckets", "describe", f"gs://{bucket_name}",
        f"--project={project_id}"
    ], check=False)
    
    if check_bucket.returncode != 0:
        print(f"Creating storage bucket 'gs://{bucket_name}' in region '{region}'...")
        run_command([
            "gcloud", "storage", "buckets", "create", f"gs://{bucket_name}",
            f"--location={region}",
            f"--project={project_id}"
        ])
    else:
        print(f"Bucket 'gs://{bucket_name}' already exists.")
        
    # 3. Register models in Vertex AI Model Registry
    models = [
        {"name": "manga-ocr", "path": "manga-ocr", "description": "Trained MangaOCR Trocr models"},
        {"name": "xtts_v2", "path": "xtts_v2", "description": "XTTS v2 Voice Cloning model weights"}
    ]
    
    for model in models:
        display_name = model["name"]
        artifact_uri = f"gs://{bucket_name}/{model['path']}"
        print(f"\nStep 3: Registering model '{display_name}' in Vertex AI Model Registry...")
        
        # Check if model is already registered
        check_model = run_command([
            "gcloud", "ai", "models", "list",
            f"--region={region}",
            f"--filter=display_name={display_name}",
            f"--project={project_id}"
        ], check=False)
        
        if display_name in check_model.stdout:
            print(f"Model '{display_name}' is already registered. Skipping upload.")
        else:
            run_command([
                "gcloud", "ai", "models", "upload",
                f"--region={region}",
                f"--display-name={display_name}",
                f"--artifact-uri={artifact_uri}",
                "--container-image-uri=europe-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-9:latest", # Dummy container since serving is Cloud Run
                f"--description={model['description']}",
                f"--project={project_id}"
            ])
            
    print("\n✅ Vertex AI Model Registry catalog and storage bucket configured successfully!")

if __name__ == "__main__":
    main()
```

---

### Task 3: Update Cloud Run deploy_brain.py Script

**Files:**
- Modify: `scripts/deploy/deploy_brain.py`

- [ ] **Step 1: Update deploy_brain.py to mount GCS models bucket**

Modify `scripts/deploy/deploy_brain.py` around line 55:
```python
    # Configuration du réseau pour Direct VPC Egress
    vpc_network = os.getenv("GCP_VPC_NETWORK", "default")
    vpc_subnet = os.getenv("GCP_VPC_SUBNET", "default")
    models_bucket = f"{project_id}-models"

    deploy_cmd = [
        "gcloud", "beta", "run", "deploy", "animetix-brain",
        f"--image={image_tag}",
        f"--region={brain_region}",
        f"--service-account={service_account}",
        f"--network={vpc_network}",
        f"--subnet={vpc_subnet}",
        "--vpc-egress=private-ranges-only",
        # FUSE Storage Volume configuration:
        f"--add-volume=name=models-vol,type=cloud-storage,bucket={models_bucket}",
        "--add-volume-mount=volume=models-vol,mount-path=/mnt/models",
        # Configurations GPU requises :
        "--gpu=1",
        "--gpu-type=nvidia-l4",
        "--cpu=4",
        "--memory=16Gi",
        "--no-cpu-throttling",  # Requis pour garder le CPU alloué avec GPU
        f"--set-secrets={secrets}",
        "--set-env-vars=DJANGO_ENV=production,LLM_API_BASE=http://localhost:11434/v1,LLM_MODEL_NAME=llama3,GCP_MODELS_MOUNT_PATH=/mnt/models",
        "--port=7861",
        "--allow-unauthenticated", # L'authentification est gérée par X-API-Key au niveau applicatif
        f"--project={project_id}"
    ]
    run_command(deploy_cmd)
```

---

### Task 4: Create Unit Tests & Verification

**Files:**
- Create: `tests/deploy/test_deploy_brain_with_volumes.py`

- [ ] **Step 1: Write unit test for the deploy_brain.py volume update**

Create `tests/deploy/test_deploy_brain_with_volumes.py` with:
```python
import subprocess
import os
from unittest.mock import patch, MagicMock
from scripts.deploy.deploy_brain import main

@patch("subprocess.run")
def test_deploy_brain_calls_gcloud_with_volume_fuse(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")
    
    with patch.dict(os.environ, {"GCP_VPC_NETWORK": "test-network", "GCP_VPC_SUBNET": "test-subnet"}):
        main()
        
    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]
    
    # Assert builds submit
    assert any("builds submit" in c for c in flat_calls)
    
    # Assert run deploy command with volumes exists
    run_deploys = [c for c in flat_calls if "run deploy animetix-brain" in c]
    assert len(run_deploys) > 0
    assert "add-volume=name=models-vol,type=cloud-storage,bucket=animetix-models" in run_deploys[0]
    assert "add-volume-mount=volume=models-vol,mount-path=/mnt/models" in run_deploys[0]
    assert "GCP_MODELS_MOUNT_PATH=/mnt/models" in run_deploys[0]
```

- [ ] **Step 2: Run new deploy brain tests**

Run:
```bash
.venv\Scripts\pytest tests/deploy/test_deploy_brain_with_volumes.py -v
```
Expected: 1 passed.

- [ ] **Step 3: Run register_models unit test simulation**

Create a simple test for `register_models.py` in `tests/deploy/test_register_models.py`:
```python
import subprocess
from unittest.mock import patch, MagicMock
from scripts.deploy.register_models import main

@patch("subprocess.run")
def test_register_models_calls_gcloud(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")
    
    main()
    
    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]
    
    assert any("services enable aiplatform.googleapis.com" in c for c in flat_calls)
    assert any("storage buckets describe gs://animetix-models" in c for c in flat_calls)
    assert any("ai models upload" in c for c in flat_calls)
```

Run:
```bash
.venv\Scripts\pytest tests/deploy/test_register_models.py -v
```
Expected: 1 passed.

- [ ] **Step 4: Commit all changes**

Run:
```bash
git add backend/adapters/inference/manga_ocr.py backend/adapters/inference/audio_mixin.py scripts/deploy/register_models.py scripts/deploy/deploy_brain.py tests/deploy/test_deploy_brain_with_volumes.py tests/deploy/test_register_models.py docs/superpowers/plans/2026-06-04-vertex-ai-model-registry.md docs/superpowers/specs/2026-06-04-vertex-ai-model-registry-design.md
git commit -m "feat: implement Vertex AI Model Registry registration and Cloud Run GCS FUSE volume mounting"
```

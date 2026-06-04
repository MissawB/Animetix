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

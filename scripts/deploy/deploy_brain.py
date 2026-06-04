import subprocess
import sys
import shutil
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
    brain_region = "europe-west1"      # GPU L4 disponible en Belgique
    web_region = "europe-west9"        # Django principal à Paris
    
    image_tag = f"europe-west9-docker.pkg.dev/{project_id}/animetix-repo/brain:latest"
    service_account = f"836616987676-compute@developer.gserviceaccount.com"

    # Step 1: Build de l'image via Cloud Build
    print("\n--- Step 1: Building Brain API image with Google Cloud Build ---")
    build_cmd = [
        "gcloud", "builds", "submit",
        "--config=deploy/cloudbuild.brain.yaml",
        f"--project={project_id}",
        "."
    ]
    run_command(build_cmd)

    # Step 2: Déploiement du service Brain API sur Cloud Run GPU
    print("\n--- Step 2: Deploying Brain API with Nvidia L4 GPU on Cloud Run ---")
    secrets = (
        "BRAIN_API_KEY=BRAIN_API_KEY:latest,"
        "HF_TOKEN=HF_TOKEN:latest"
    )
    
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
        # GCS FUSE Volume mount configuration:
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

    # Step 3: Récupération de l'URL du service Brain API
    print("\n--- Step 3: Retrieving Brain API URL ---")
    url_cmd = [
        "gcloud", "run", "services", "describe", "animetix-brain",
        f"--region={brain_region}",
        "--format=value(status.url)",
        f"--project={project_id}"
    ]
    res_url = run_command(url_cmd)
    brain_url = res_url.stdout.strip()
    if not brain_url:
        print("Error: Could not retrieve Brain API URL.")
        sys.exit(1)
    print(f"Brain API URL is: {brain_url}")

    # Step 4: Liaison dans le service web Django principal
    print("\n--- Step 4: Linking Brain API URL to animetix-web ---")
    link_cmd = [
        "gcloud", "run", "services", "update", "animetix-web",
        f"--region={web_region}",
        f"--update-env-vars=BRAIN_API_URL={brain_url}",
        f"--project={project_id}"
    ]
    run_command(link_cmd)
    
    print("\n✅ Heavy ML Inference successfully deployed on Cloud Run GPU Serverless and linked to Django!")

if __name__ == "__main__":
    main()

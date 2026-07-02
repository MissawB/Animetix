import os

from google.cloud import aiplatform

# Load .env file
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#"):
                key_val = line.strip().split("=", 1)
                if len(key_val) == 2:
                    val = key_val[1].strip().strip('"').strip("'")
                    os.environ[key_val[0].strip()] = val

token = os.getenv("HF_TOKEN")
if not token:
    raise ValueError("HF_TOKEN environment variable not set.")

project_id = "animetix"
region = "europe-west1"  # Let's try T4 in europe-west1 first
staging_bucket = "gs://animetix-vertex-pipelines-staging"

print("Initializing Vertex AI platform...")
aiplatform.init(project=project_id, location=region, staging_bucket=staging_bucket)

print("Defining Custom Training Job on Vertex AI...")
job = aiplatform.CustomTrainingJob(
    display_name="qwen35-9b-star-lora-expert-training",
    script_path="backend/pipeline/mlops/remote_train_expert.py",
    container_uri="us-docker.pkg.dev/vertex-ai/training/pytorch-gpu.2-1.py310:latest",
    requirements=[
        "trl>=0.12.0",
        "peft>=0.7.0",
        "transformers>=4.45.0",
        "datasets",
        "accelerate",
        "huggingface_hub",
        "trackio",
        "bitsandbytes",
    ],
)

print(
    "Submitting training job to Vertex AI (n1-standard-4 / Nvidia T4 in europe-west1)..."
)
# Submit the training job to run on the GPU cluster
job.run(
    replica_count=1,
    machine_type="n1-standard-4",  # T4 GPU machine type
    accelerator_type="NVIDIA_TESLA_T4",
    accelerator_count=1,
    environment_variables={
        "HF_TOKEN": token,
        "DATASET_NAME": "MissawB/otaku-expert-dataset",
        "HUB_MODEL_ID": "MissawB/otaku-qwen-7b-adapter",
    },
    service_account="vertex-express@animetix.iam.gserviceaccount.com",
)

print("✅ Custom Training Job successfully submitted and running on Vertex AI!")

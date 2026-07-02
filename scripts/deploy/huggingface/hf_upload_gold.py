import os
import sys

from huggingface_hub import HfApi, create_repo

# Load .env file
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
env_path = os.path.join(project_root, ".env")
custom_env = os.environ.copy()

if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#"):
                key_val = line.strip().split("=", 1)
                if len(key_val) == 2:
                    val = key_val[1].strip().strip('"').strip("'")
                    custom_env[key_val[0].strip()] = val

token = custom_env.get("HF_TOKEN")
if not token:
    print("Error: HF_TOKEN not found in .env file.")
    sys.exit(1)

repo_id = "MissawB/otaku-gold-dataset"
gold_dataset_path = "data/mlops/gold_dataset.json"

if not os.path.exists(gold_dataset_path):
    print(f"Error: Gold dataset not found at {gold_dataset_path}")
    sys.exit(1)

print(f"Creating Hugging Face dataset repository: {repo_id}...")
create_repo(repo_id, token=token, repo_type="dataset", exist_ok=True)

print(f"Uploading gold dataset file {gold_dataset_path}...")
api = HfApi()
api.upload_file(
    path_or_fileobj=gold_dataset_path,
    path_in_repo="gold_dataset.json",
    repo_id=repo_id,
    repo_type="dataset",
    token=token,
)
print(
    f"Gold dataset successfully uploaded! View it at: https://huggingface.co/datasets/{repo_id}"
)

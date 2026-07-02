import os

from huggingface_hub import HfApi, create_repo

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
repo_id = "MissawB/otaku-expert-dataset"
dataset_path = "data/mlops/datasets/animetix_expert_ft.jsonl"

print(f"Creating Hugging Face dataset repository: {repo_id}...")
create_repo(repo_id, token=token, repo_type="dataset", exist_ok=True)

print(f"Uploading dataset file {dataset_path}...")
api = HfApi()
api.upload_file(
    path_or_fileobj=dataset_path,
    path_in_repo="train.jsonl",
    repo_id=repo_id,
    repo_type="dataset",
    token=token,
)
print(
    f"Dataset successfully uploaded! View it at: https://huggingface.co/datasets/{repo_id}"
)

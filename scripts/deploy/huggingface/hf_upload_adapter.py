import os

from huggingface_hub import HfApi, create_repo

# Load .env file if it exists at project root to read HF_TOKEN securely
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
                    os.environ[key_val[0].strip()] = key_val[1].strip()

token = os.getenv("HF_TOKEN")
if not token:
    raise ValueError(
        "HF_TOKEN environment variable not set. Please define it in your environment or in the .env file."
    )

repo_id = "MissawB/otaku-qwen-7b-adapter"
folder_path = "data/models/otaku-qwen-7b-adapter/checkpoint-2500"

print(f"Creating Hugging Face repository: {repo_id}...")
create_repo(repo_id, token=token, repo_type="model", exist_ok=True)

print(f"Uploading adapter and tokenizer files from {folder_path}...")
# Exclude training state files to keep the model repo clean
ignore_patterns = ["optimizer.pt", "scheduler.pt", "rng_state.pth", "training_args.bin"]

api = HfApi()
api.upload_folder(
    folder_path=folder_path,
    repo_id=repo_id,
    repo_type="model",
    token=token,
    ignore_patterns=ignore_patterns,
)
print(f"Adapter successfully uploaded! View it at: https://huggingface.co/{repo_id}")

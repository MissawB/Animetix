import os
import subprocess
import sys

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

# Construct command
hf_path = os.path.join(project_root, ".venv", "Scripts", "hf")
if not os.path.exists(hf_path) and not os.path.exists(hf_path + ".exe"):
    hf_path = "hf"  # Fallback to global hf if local venv hf doesn't exist

cmd = [
    hf_path,
    "jobs",
    "uv",
    "run",
    "--flavor",
    "a10g-large",
    "--timeout",
    "2h",
    "--secrets",
    "HF_TOKEN",
    "-d",  # Detach mode to submit and return immediately
    "scripts/deploy/hf_train_qwen35.py",
]

print(f"Executing: {' '.join(cmd)}")
result = subprocess.run(cmd, env=custom_env, capture_output=True, text=True)

if result.returncode == 0:
    print("HF Job successfully submitted!")
    print(result.stdout)
else:
    print("Failed to submit HF Job.")
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)
    sys.exit(result.returncode)

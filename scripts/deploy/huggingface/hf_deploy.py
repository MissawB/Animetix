import os
import textwrap

from huggingface_hub import HfApi, create_repo

# Repo root. This file lives at scripts/deploy/huggingface/hf_deploy.py, i.e.
# THREE dirs below the root, so we strip four path components (file + 3 dirs).
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

token = custom_env.get("HF_TOKEN") or custom_env.get("HF_SPACES")
if not token:
    raise ValueError(
        "Neither HF_SPACES nor HF_TOKEN environment variables are set in system or .env."
    )

api = HfApi()


def deploy_space(repo_id, docker_content, readme_content, ignore):
    print(f"Syncing {repo_id}...")
    # Only create the Space when it is genuinely missing. Calling create_repo on
    # every sync hits /api/repos/create, which can return 402 Payment Required on
    # accounts with billing/quota gating even when the repo already exists (the
    # billing check runs before the "already exists" short-circuit). We only need
    # to push updates to the existing Spaces, so skip creation when they exist.
    if api.repo_exists(repo_id, repo_type="space", token=token):
        print(f"  {repo_id} already exists — skipping create_repo.")
    else:
        create_repo(
            repo_id, token=token, repo_type="space", space_sdk="docker", exist_ok=True
        )

    docker_final = textwrap.dedent(docker_content).strip()
    readme_final = textwrap.dedent(readme_content).strip()

    # Exclusions non négociables, quel que soit le `ignore` fourni par l'appelant :
    # le .env racine contient des secrets réels et ne doit jamais être uploadé.
    always_ignore = ["Dockerfile", "README.md", ".env", "**/.env"]
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        token=token,
        ignore_patterns=ignore + always_ignore,
    )

    api.upload_file(
        path_or_fileobj=docker_final.encode(),
        path_in_repo="Dockerfile",
        repo_id=repo_id,
        repo_type="space",
        token=token,
    )
    api.upload_file(
        path_or_fileobj=readme_final.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="space",
        token=token,
    )
    print(f"{repo_id} synced successfully!")


# --- CONFIG WEB ---
# The web Space is a faithful mirror of the Cloud Run deployment, so it reuses
# the exact same recipe: deploy/Dockerfile (multi-stage node frontend build +
# python 3.12 + collectstatic + deploy/supervisord.conf on port 7860). Keeping a
# second inlined Dockerfile here caused drift (it went stale: python 3.11, no
# frontend build, wrong supervisord path) so the Space never booted. Read the
# real file at runtime instead — single source of truth.
with open(os.path.join(project_root, "deploy", "Dockerfile"), encoding="utf-8") as _f:
    web_docker = _f.read()

web_readme = """
---
title: Animetix Web
emoji: 🧩
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
---

# 🧩 Animetix Web Client

Welcome to the flagship frontend client interface for **Animetix (Anime Archetype Engine)**.

This interface provides an immersive, premium user experience connecting all components of our multi-layered AI cognitive architecture.

## 🌟 Interactive Playgrounds Included

1. **Akinetix Thematic Character Guessing:**
   - Play a 20-questions style game where an AI agent attempts to guess your favorite anime character.
   - Powered by a reinforcement learning agent trained via **Proximal Policy Optimization (PPO)** in a custom gym environment.

2. **Paradox Quest Riddles:**
   - Solve complex thematic anomalies and find the logical "intruder" among a triplet of anime titles.
   - Powered by a Neuro-Symbolic logic layer compiled and solved in real-time by the **Z3 Theorem Prover**.

3. **La Forge Laboratory:**
   - Mix visual styles and characters using **Stable Diffusion XL**, **IP-Adapter**, and **ControlNet** pipelines.
   - Experience zero-shot voice cloning with spatialized character speech via **XTTS-v2**.

## 🔌 Connection & Backend
This space connects with the backend inference engine **Animetix Brain** to fetch vector RAG documents, Neo4j graph nodes, and execute the Qwen 3.5 9B reasoning adapter.

---

### Research References & Foundations
This platform is built upon key AI academic research:
- **STaR (Self-Taught Reasoner):** [STaR paper](https://arxiv.org/abs/2203.14465) (Zelikman et al., 2022).
- **DPO (Direct Preference Optimization):** [DPO paper](https://arxiv.org/abs/2305.18290) (Rafailov et al., 2023).
- **ReAct Agents:** [ReAct paper](https://arxiv.org/abs/2210.03629) (Yao et al., 2023).
- **Z3 Neuro-Symbolic Integration:** Z3 theorem prover integration.
"""

# --- CONFIG BRAIN ---
brain_docker = """
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch transformers accelerate fastapi uvicorn pydantic huggingface_hub python-dotenv requests
COPY core/brain.py ./brain.py
COPY data/artifacts/ ./data/artifacts/
EXPOSE 7860
CMD ["uvicorn", "brain:app", "--host", "0.0.0.0", "--port", "7860"]
"""

brain_readme = """
---
title: Animetix Brain
emoji: 🧠
colorFrom: pink
colorTo: red
sdk: docker
pinned: false
---

# 🧠 Animetix Brain API

Welcome to the backend AI inference engine for **Animetix (Anime Archetype Engine)**.

This API serves all neural, vector, and symbolic queries powering the Animetix ecosystem.

## 🛠️ Key AI Capabilities & Endpoints

- **`/query` (Semantic RAG Search):**
  - Executes dual-retrieval (Neo4j Multi-Hop graph queries + Vertex AI vector database search).
  - Integrates **Jina-v3** Matryoshka Representation Learning (MRL) embeddings and **BGE-Reranker** to filter unrelated noise.
- **`/reason` (Thinking Mode):**
  - Triggers the Test-Time Compute reasoning trace.
  - Utilizes the custom-tuned **Qwen 3.5 9B LoRA adapter** to produce structured reasoning paths inside `<thought>` tags.
- **`/akinetix` (Entropy Policy Engine):**
  - Determines the next best query question to ask by calculating database entropy at each step.
- **`/paradox` (Neuro-Symbolic Riddle Solver):**
  - Compiles facts into boolean logic clauses and runs the **Z3 Theorem Prover** to verify riddle anomalies.

---

### Research References
This API implements systems based on:
- **DeepSeek-R1:** [DeepSeek-R1 paper](https://arxiv.org/abs/2501.12948) (DeepSeek-AI, 2025).
- **Toolformer:** [Toolformer paper](https://arxiv.org/abs/2302.04761) (Schick et al., 2023).
- **S-LoRA Adapter Serving:** [S-LoRA paper](https://arxiv.org/abs/2311.03285) (Sheng et al., 2023).
- **RAGAS Evaluations:** [RAGAS paper](https://arxiv.org/abs/2309.15217) (Es et al., 2023).
"""

# EXÉCUTION
if __name__ == "__main__":
    deploy_space(
        "MissawB/animetix-web",
        web_docker,
        web_readme,
        [
            ".venv/*",
            ".env",
            "data/models/*",
            "data/raw/*",
            "core/brain.py",
            "pipeline/*",
            ".github/*",
            "node_modules/*",
            "frontend/node_modules/*",
            "frontend/dist/*",
            "checkpoints/*",
            "backend/api/db.sqlite3",
            "**/db.sqlite3",
            "**/*.pyc",
            "**/__pycache__/*",
            "scripts/*",
            "wandb/*",
        ],
    )
    deploy_space(
        "MissawB/animetix-brain",
        brain_docker,
        brain_readme,
        [
            ".venv/*",
            ".env",
            "backend/*",
            "data/raw/*",
            "data/processed/*",
            ".github/*",
            "pipeline/*",
            "core/__init__.py",
            "node_modules/*",
            "frontend/node_modules/*",
            "checkpoints/*",
            "backend/api/db.sqlite3",
            "**/db.sqlite3",
            "**/*.pyc",
            "**/__pycache__/*",
            "scripts/*",
            "data/models/*",
            "frontend/*",
            "wandb/*",
        ],
    )

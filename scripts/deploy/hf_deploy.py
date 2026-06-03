from huggingface_hub import HfApi, create_repo
import os
import textwrap

api = HfApi()
token = os.environ['HF_TOKEN']

def deploy_space(repo_id, docker_content, readme_content, ignore):
    print(f'🚀 Syncing {repo_id}...')
    create_repo(repo_id, token=token, repo_type='space', space_sdk='docker', exist_ok=True)
    
    docker_final = textwrap.dedent(docker_content).strip()
    readme_final = textwrap.dedent(readme_content).strip()

    api.upload_folder(
        folder_path='.',
        repo_id=repo_id,
        repo_type='space',
        token=token,
        ignore_patterns=ignore + ['Dockerfile', 'README.md']
    )
    
    api.upload_file(path_or_fileobj=docker_final.encode(), path_in_repo='Dockerfile', repo_id=repo_id, repo_type='space', token=token)
    api.upload_file(path_or_fileobj=readme_final.encode(), path_in_repo='README.md', repo_id=repo_id, repo_type='space', token=token)
    print(f'✅ {repo_id} synced!')

# --- CONFIG WEB ---
web_docker = """
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH='/app/backend:${PYTHONPATH}'
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn supervisor
COPY . .
RUN mkdir -p data/artifacts data/processed
EXPOSE 7860
CMD ["supervisord", "-c", "infra/supervisord.conf"]
"""

web_readme = """
---
title: Animetix
emoji: 🧩
sdk: docker
---
# 🧩 Animetix Web
"""

# --- CONFIG BRAIN ---
brain_docker = """
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
# On installe les dépendances nécessaires pour l'inférence
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
sdk: docker
---
# 🧠 Animetix Brain API
"""

# EXÉCUTION
deploy_space('MissawB/animetix-web', web_docker, web_readme, ['.venv/*', '.env', 'data/models/*', 'data/raw/*', 'core/brain.py', 'pipeline/*', '.github/*'])
deploy_space('MissawB/animetix-brain', brain_docker, brain_readme, ['.venv/*', '.env', 'backend/*', 'data/raw/*', 'data/processed/*', '.github/*', 'pipeline/*', 'core/__init__.py'])

# Image de base stable et légère
FROM python:3.11-slim

# Éviter la génération de fichiers .pyc et forcer l'affichage des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Configuration de Dagster Home
ENV DAGSTER_HOME=/app/pipeline
RUN mkdir -p /app/pipeline/.dagster_home

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Création des dossiers nécessaires
RUN mkdir -p data/raw data/processed data/models data/artifacts data/chroma_db

# Hugging Face utilise le port 7860 par défaut
EXPOSE 7860

# Commande de lancement via Supervisor (Django + Celery)
CMD ["supervisord", "-c", "infra/supervisord.conf"]

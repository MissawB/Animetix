# Stage 1: Frontend Builder
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Builder
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev gcc libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy assets & venv
COPY --from=builder /opt/venv /opt/venv
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/backend:/app/backend/api:$PYTHONPATH"

# Copy source files
COPY --chown=appuser:appuser . .

# Aggregate React assets with Django statics
RUN python backend/api/manage.py collectstatic --noinput

RUN mkdir -p data/raw data/processed data/models data/artifacts data/chroma_db && chown -R appuser:appuser /app
USER appuser
ENV DAGSTER_HOME=/app/backend/pipeline
EXPOSE 7860
CMD ["supervisord", "-c", "deploy/supervisord.conf"]

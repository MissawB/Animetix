# Stage 1: Builder
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy code and set permissions
COPY --chown=appuser:appuser . .

# Collect static files (assuming settings.py is configured correctly for STATIC_ROOT)
RUN python backend/api/manage.py collectstatic --noinput

# Set up data directories with proper permissions
RUN mkdir -p data/raw data/processed data/models data/artifacts data/chroma_db && chown -R appuser:appuser /app

USER appuser

ENV DAGSTER_HOME=/app/backend/pipeline

EXPOSE 7860

CMD ["supervisord", "-c", "deploy/supervisord.conf"]

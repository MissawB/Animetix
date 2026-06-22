# Stage 1: Frontend Builder
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Builder
FROM python:3.12-slim-bookworm AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.* \
    libpq-dev=15.* \
    gcc=4:12.2.* \
    libsndfile1=1.2.0* \
    ffmpeg=7:5.1.* \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ultralytics pins the GUI opencv-python (needs libGL, absent from this slim image)
# alongside our opencv-python-headless; both own the same `cv2` files, so plainly
# uninstalling one would delete the shared files. Remove both, then reinstall only
# headless (version read from the lockfile) — smaller image, `import cv2` needs no libGL.
RUN pip uninstall -y opencv-python opencv-python-headless \
    && pip install --no-cache-dir "$(grep -E '^opencv-python-headless==' requirements.txt)"

# Stage 3: Runtime
FROM python:3.12-slim-bookworm
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5=15.* \
    curl=7.88.1* \
    libsndfile1=1.2.0* \
    ffmpeg=7:5.1.* \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*
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

RUN mkdir -p data/raw data/processed data/models data/artifacts && chown -R appuser:appuser /app
USER appuser
EXPOSE 7860
CMD ["supervisord", "-c", "deploy/supervisord.conf"]

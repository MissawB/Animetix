# Multi-stage Frontend Build & Production Serving Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure Django settings to look up templates and static assets inside the React production build (`frontend/dist`), and update the deployment Dockerfile to compile the React frontend dynamically in a multi-stage build.

**Architecture:** Use a multi-stage Docker container. The Node.js stage compiles the frontend into `frontend/dist`. The final Python stage copies `frontend/dist` and runs Django `collectstatic` to merge React assets into `STATIC_ROOT` so they are compressed and cached by Whitenoise.

**Tech Stack:** Docker, Node.js (Vite, React 19), Python 3.11, Django 5, Whitenoise.

---

### Task 1: Configure Django Settings

**Files:**
* Modify: [backend/api/animetix_project/settings.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py)

- [ ] **Step 1: Configure template lookup directories**
  Update the `TEMPLATES` setting in `settings.py` so that Django discovers `index.html` inside the React SPA build directory.
  
  Replace lines 221-225 in `settings.py`:
  ```python
  TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [],
          'APP_DIRS': True,
  ```
  With:
  ```python
  TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [os.path.join(PROJECT_ROOT, "frontend", "dist")],
          'APP_DIRS': True,
  ```

- [ ] **Step 2: Configure static asset lookup directories**
  Add `STATICFILES_DIRS` to discovery paths in `settings.py` so that Whitenoise and Django `collectstatic` find the Vite-built static files (CSS/JS chunks).
  
  Add the following lines under `STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')` (around line 297-298):
  ```python
  STATICFILES_DIRS = [
      os.path.join(PROJECT_ROOT, "frontend", "dist"),
  ]
  ```

- [ ] **Step 3: Run local template verification**
  Run the local template origin test to ensure no `TemplateDoesNotExist` error is thrown when looking up `index.html` (after creating a local empty placeholder `frontend/dist/index.html` if needed).
  
  Run:
  ```powershell
  $env:DJANGO_SETTINGS_MODULE="animetix_project.settings"
  $env:PYTHONPATH="C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project;C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\backend;C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\backend\api"
  python -c "import django; django.setup(); from django.template.loader import get_template; print('Template found at:', get_template('index.html').origin.name)"
  ```
  Expected output:
  `Template found at: C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\frontend\dist\index.html`

- [ ] **Step 4: Commit**
  ```bash
  git add backend/api/animetix_project/settings.py
  git commit -m "feat: configure TEMPLATES and STATICFILES_DIRS to serve frontend dist"
  ```

---

### Task 2: Multi-stage Dockerfile Implementation

**Files:**
* Modify: [deploy/Dockerfile](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/deploy/Dockerfile)

- [ ] **Step 1: Implement three-stage compilation**
  Overwrite the contents of `deploy/Dockerfile` with the optimized Node + Python multi-stage build.

  ```dockerfile
  # Stage 1: Frontend Builder
  FROM node:20-alpine AS frontend-builder
  WORKDIR /app/frontend
  COPY frontend/package*.json ./
  RUN npm ci || npm install
  COPY frontend/ ./
  RUN npm run build

  # Stage 2: Backend Builder
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
  ```

- [ ] **Step 2: Commit**
  ```bash
  git add deploy/Dockerfile
  git commit -m "build: implement multi-stage frontend compilation in Dockerfile"
  ```

---

### Task 3: Trigger Cloud Build & Deploy

**Files:**
* Command Line Execution

- [ ] **Step 1: Submit optimized remote build**
  Launch Cloud Build compilation to compile the frontend, python environment, and tag the output docker image.
  
  Run:
  ```powershell
  gcloud builds submit --config cloudbuild.yaml .
  ```
  Expected output:
  `SUCCESS` (tagged image `europe-west9-docker.pkg.dev/animetix/animetix-repo/web:latest` pushed successfully).

- [ ] **Step 2: Deploy new revision to Cloud Run**
  Deploy the new multi-stage compiled image live.
  
  Run:
  ```powershell
  gcloud run deploy animetix-web --image europe-west9-docker.pkg.dev/animetix/animetix-repo/web:latest --region europe-west9 --allow-unauthenticated --port 7860 --memory 4Gi --cpu 2 --update-env-vars DJANGO_ENV=production --set-secrets="DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest,BRAIN_API_KEY=BRAIN_API_KEY:latest,TMDB_API_KEY=TMDB_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,IGDB_CLIENT_ID=IGDB_CLIENT_ID:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,HF_TOKEN=HF_TOKEN:latest,IGDB_CLIENT_SECRET=IGDB_CLIENT_SECRET:latest,WANDB_API_KEY=WANDB_API_KEY:latest"
  ```
  Expected output:
  `Service [animetix-web] revision [...] has been deployed and is serving 100 percent of traffic.`

- [ ] **Step 3: Verification of live React SPA**
  Perform an HTTP validation check to verify `/fr/` returns the complete compiled Vite/React SPA instead of the text placeholder.
  
  Run:
  ```powershell
  curl.exe -i https://animetix-web-836616987676.europe-west9.run.app/fr/
  ```
  Expected output:
  `HTTP/1.1 200 OK`
  The response body should contain the React Vite imports: `<script type="module" crossorigin src="/assets/index-...js"></script>`

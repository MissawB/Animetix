# Scalable Apache Beam Dataflow Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package and orchestrate the lore scraping and embedding pipeline (`lore_ingestion_beam.py`) on Google Cloud Dataflow using a Single Docker Image Flex Template.

**Architecture:** Use `apache/beam_python3.12_sdk:2.74.0` as the worker runtime image. Bundle launcher binary, application codebase, and all dependencies (including Django and BeautifulSoup) into the image, configuring PYTHONPATH and propagating database credentials to worker nodes via pipeline options.

**Tech Stack:** Apache Beam (Python), Google Cloud Dataflow, Docker, Cloud Build, Django ORM, pgvector.

---

### Task 1: Package Dependencies

**Files:**
- Modify: [requirements.txt](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/requirements.txt)

- [ ] **Step 1: Write the requirement addition**
  Add `beautifulsoup4==4.12.3` at the end of the `requirements.txt` file to guarantee it is installed inside the container.
- [ ] **Step 2: Install dependencies locally**
  Run: `.venv\Scripts\pip install -r requirements.txt`
  Expected: Successful installation of BeautifulSoup4.
- [ ] **Step 3: Verify installation**
  Run: `.venv\Scripts\python -c "import bs4; print(bs4.__version__)"`
  Expected: `4.12.3`
- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add requirements.txt
  git commit -m "deps: add beautifulsoup4 for beam scraping"
  ```

---

### Task 2: Implement Options and DoFn Constructors in Ingestion Pipeline

**Files:**
- Modify: [lore_ingestion_beam.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/lore_ingestion_beam.py)
- Test: [test_lore_ingestion_beam.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/backend/test_lore_ingestion_beam.py)

- [ ] **Step 1: Write the failing test**
  Add a new test `test_dofn_parameter_propagation` in `tests/backend/test_lore_ingestion_beam.py` to verify that `GenerateEmbeddingsDoFn` and `WriteToVectorDBDoFn` accept constructors and set environment variables.
  
  ```python
  def test_dofn_parameter_propagation():
      from backend.pipeline.mlops.lore_ingestion_beam import GenerateEmbeddingsDoFn, WriteToVectorDBDoFn
      import os
      
      # Test GenerateEmbeddingsDoFn
      embedder = GenerateEmbeddingsDoFn(database_url="postgresql://test_url", django_env="test_env")
      assert embedder.database_url == "postgresql://test_url"
      assert embedder.django_env == "test_env"
      
      # Test WriteToVectorDBDoFn
      writer = WriteToVectorDBDoFn(database_url="postgresql://test_url", django_env="test_env")
      assert writer.database_url == "postgresql://test_url"
      assert writer.django_env == "test_env"
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest tests/backend/test_lore_ingestion_beam.py::test_dofn_parameter_propagation -v`
  Expected: FAIL (TypeError: `__init__()` takes no arguments)

- [ ] **Step 3: Modify `lore_ingestion_beam.py` to add `IngestionOptions` and constructor parameter handling**
  Modify lines 86-97 and 145-156 in [lore_ingestion_beam.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/lore_ingestion_beam.py) to implement `__init__` and environment setups:

  ```python
  class IngestionOptions(PipelineOptions):
      @classmethod
      def _add_argparse_args(cls, parser):
          parser.add_argument('--pubsub_subscription', type=str, help='Pub/sub subscription path')
          parser.add_argument('--database_url', type=str, help='Database connection URL')
          parser.add_argument('--django_env', type=str, default='production', help='Django environment')

  class GenerateEmbeddingsDoFn(beam.DoFn):
      def __init__(self, database_url=None, django_env=None):
          self.database_url = database_url
          self.django_env = django_env
          super().__init__()

      def setup(self):
          if self.database_url:
              os.environ['DATABASE_URL'] = self.database_url
          if self.django_env:
              os.environ['DJANGO_ENV'] = self.django_env
          import django
          os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
          try:
              django.setup()
              from animetix.containers import get_container
              self.container = get_container()
          except Exception as e:
              logger.warning(f"Django setup warning in Beam worker: {e}")
              self.container = None

  class WriteToVectorDBDoFn(beam.DoFn):
      def __init__(self, database_url=None, django_env=None):
          self.database_url = database_url
          self.django_env = django_env
          super().__init__()

      def setup(self):
          if self.database_url:
              os.environ['DATABASE_URL'] = self.database_url
          if self.django_env:
              os.environ['DJANGO_ENV'] = self.django_env
          import django
          os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
          try:
              django.setup()
              from animetix.containers import get_container
              self.container = get_container()
          except Exception as e:
              logger.warning(f"Django setup warning in Beam worker: {e}")
              self.container = None
  ```

  Also modify `run_pipeline` in [lore_ingestion_beam.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/mlops/lore_ingestion_beam.py) to read custom arguments:
  ```python
  def run_pipeline(argv=None, test_input=None):
      pipeline_options = PipelineOptions(argv)
      
      with beam.Pipeline(options=pipeline_options) as p:
          if test_input is not None:
              raw_input = p | "CreateMockInput" >> beam.Create(test_input)
              db_url = None
              dj_env = None
          else:
              options = pipeline_options.view_as(IngestionOptions)
              subscription_path = options.pubsub_subscription
              db_url = options.database_url
              dj_env = options.django_env
              if not subscription_path:
                  raise ValueError("Missing required parameter: --pubsub_subscription")
              raw_input = (
                  p 
                  | "ReadFromPubSub" >> beam.io.ReadFromPubSub(subscription=subscription_path)
                  | "DecodeMessage" >> beam.Map(lambda bytes_data: json.loads(bytes_data.decode("utf-8")))
              )
              
          (
              raw_input
              | "ScrapeAndClean" >> beam.ParDo(ScrapeAndCleanDoFn())
              | "ChunkText" >> beam.ParDo(ChunkTextDoFn())
              | "GenerateEmbeddings" >> beam.ParDo(GenerateEmbeddingsDoFn(database_url=db_url, django_env=dj_env))
              | "WriteToVectorDB" >> beam.ParDo(WriteToVectorDBDoFn(database_url=db_url, django_env=dj_env))
          )
  ```

- [ ] **Step 4: Run tests to verify they pass**
  Run: `.venv\Scripts\pytest tests/backend/test_lore_ingestion_beam.py -v`
  Expected: PASS (Both tests pass successfully)
- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/pipeline/mlops/lore_ingestion_beam.py tests/backend/test_lore_ingestion_beam.py
  git commit -m "feat: propagate database credentials to Beam workers via options"
  ```

---

### Task 3: Create Dockerfile and Template Metadata for Dataflow Flex Template

**Files:**
- Create: `deploy/Dockerfile.dataflow`
- Create: `deploy/lore_ingestion_metadata.json`

- [ ] **Step 1: Create `deploy/Dockerfile.dataflow`**
  Write:
  ```dockerfile
  # --- Stage 1: Get Python Flex Template Launcher Binary ---
  FROM gcr.io/dataflow-templates-base/python3-template-launcher-base:latest AS launcher

  # --- Stage 2: Build Application Image ---
  FROM apache/beam_python3.12_sdk:2.74.0

  # Copy Flex Template launcher binary
  COPY --from=launcher /opt/google/dataflow/python_template_launcher /opt/google/dataflow/python_template_launcher

  # Set working directory
  WORKDIR /template

  # Install system dependencies
  USER root
  RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      gcc \
      libsndfile1 \
      ffmpeg \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements.txt
  COPY requirements.txt ./

  # Install requirements + bs4
  RUN pip install --no-cache-dir -r requirements.txt && \
      pip install --no-cache-dir beautifulsoup4

  # Copy backend codebase
  COPY backend/ ./backend/

  # Configure Python search path
  ENV PYTHONPATH="/template/backend:/template/backend/api:$PYTHONPATH"

  # Specify Pipeline Entrypoint
  ENV FLEX_TEMPLATE_PYTHON_PY_FILE=/template/backend/pipeline/mlops/lore_ingestion_beam.py

  ENTRYPOINT ["/opt/google/dataflow/python_template_launcher"]
  ```

- [ ] **Step 2: Create `deploy/lore_ingestion_metadata.json`**
  Write:
  ```json
  {
    "name": "Lore Ingestion Pipeline",
    "description": "Scalable Apache Beam pipeline on Dataflow to ingest, chunk, embed, and load wiki lore pages into pgvector database.",
    "parameters": [
      {
        "name": "pubsub_subscription",
        "label": "Pub/Sub Subscription Path",
        "helpText": "The Pub/Sub subscription to consume wiki ingestion tasks from (e.g. projects/animetix/subscriptions/lore-ingestion-sub).",
        "type": "TEXT",
        "isOptional": false
      },
      {
        "name": "database_url",
        "label": "Database URL",
        "helpText": "Connection URL for the PostgreSQL/AlloyDB database.",
        "type": "TEXT",
        "isOptional": true
      },
      {
        "name": "django_env",
        "label": "Django Environment",
        "helpText": "Set to 'production' to enable production configurations.",
        "type": "TEXT",
        "isOptional": true
      }
    ]
  }
  ```

- [ ] **Step 3: Verify file existence**
  Run: `ls deploy/Dockerfile.dataflow, deploy/lore_ingestion_metadata.json`
  Expected: Both files exist
- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add deploy/Dockerfile.dataflow deploy/lore_ingestion_metadata.json
  git commit -m "deploy: add Dataflow Flex Template Dockerfile and metadata"
  ```

---

### Task 4: Create Cloud Build Configuration

**Files:**
- Create: `deploy/cloudbuild_dataflow.yaml`

- [ ] **Step 1: Create `deploy/cloudbuild_dataflow.yaml`**
  Write:
  ```yaml
  steps:
    # 1. Build the Single Docker Image
    - name: 'gcr.io/cloud-builders/docker'
      args: [
        'build',
        '-t', 'europe-west9-docker.pkg.dev/animetix/animetix-repo/lore-ingestion-beam:latest',
        '-f', 'deploy/Dockerfile.dataflow',
        '.'
      ]

    # 2. Push the Image to Artifact Registry
    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'europe-west9-docker.pkg.dev/animetix/animetix-repo/lore-ingestion-beam:latest']

    # 3. Build the Dataflow Flex Template spec file and upload to GCS
    - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
      entrypoint: 'gcloud'
      args: [
        'dataflow', 'flex-template', 'build',
        'gs://animetix-dataflow/templates/lore-ingestion-beam.json',
        '--image', 'europe-west9-docker.pkg.dev/animetix/animetix-repo/lore-ingestion-beam:latest',
        '--sdk-language', 'PYTHON',
        '--metadata-file', 'deploy/lore_ingestion_metadata.json'
      ]

  images:
    - 'europe-west9-docker.pkg.dev/animetix/animetix-repo/lore-ingestion-beam:latest'
  ```
- [ ] **Step 2: Commit**
  Run:
  ```bash
  git add deploy/cloudbuild_dataflow.yaml
  git commit -m "deploy: add Cloud Build config for Dataflow Flex Template"
  ```

---

### Task 5: Check off Task in TODO List

**Files:**
- Modify: [TODO.md](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/docs/TODO.md)

- [ ] **Step 1: Update TODO task**
  Modify line 34 of `docs/TODO.md` to change `- [ ] **Orchestration Apache Beam scalable**` to `- [x] **Orchestration Apache Beam scalable**`.
- [ ] **Step 2: Commit**
  Run:
  ```bash
  git add docs/TODO.md
  git commit -m "docs: mark scalable apache beam task as completed"
  ```

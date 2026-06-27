"""Idempotent bootstrap of foundational stateless GCP resources the app consumes
but which no other scripts/deploy/*.py provisions.

Modes:
  --check    read-only: report each resource exists/MISSING; exit !=0 if any missing
  --dry-run  print the gcloud/bq commands without executing
  --apply    create resources idempotently (creates tolerate "already exists")

Creation-only; never deletes. Never passes a secret value.
"""

import shutil
import subprocess
import sys

PROJECT_ID = "animetix"
WEB_REGION = "europe-west9"  # Django / web + media bucket
INFRA_REGION = "europe-west1"  # Cloud Tasks, Vertex, Scheduler, Brain
GH_REPO = "MissawB/Animetix"


def run_command(cmd_args, check=True):
    resolved = shutil.which(cmd_args[0])
    if resolved:
        cmd_args[0] = resolved
    print(f"Running: {' '.join(cmd_args)}")
    result = subprocess.run(cmd_args, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error executing: {' '.join(cmd_args)}")
        print(f"Stdout:\n{result.stdout}")
        print(f"Stderr:\n{result.stderr}")
        if check:
            sys.exit(result.returncode)
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    return result


def _apply_or_check(mode, missing, create_args, check_args, desc):
    """Single resource step. apply=create (tolerant); check=describe + record;
    dry-run=print only."""
    if mode == "dry-run":
        print(f"[DRY-RUN] {desc}: {' '.join(create_args)}")
        return
    if mode == "check":
        res = run_command(check_args, check=False)
        ok = res.returncode == 0
        print(f"  {'OK     ' if ok else 'MISSING'} : {desc}")
        if not ok:
            missing.append(desc)
        return
    # apply
    print(f"[apply] {desc}")
    run_command(create_args, check=False)


def ensure_apis(mode, missing):
    apis = [
        "cloudbuild.googleapis.com",
        "run.googleapis.com",
        "artifactregistry.googleapis.com",
        "cloudtasks.googleapis.com",
        "pubsub.googleapis.com",
        "bigquery.googleapis.com",
        "secretmanager.googleapis.com",
        "iam.googleapis.com",
        "iamcredentials.googleapis.com",
        "sts.googleapis.com",
        "aiplatform.googleapis.com",
        "cloudscheduler.googleapis.com",
    ]
    create_args = ["gcloud", "services", "enable", *apis, f"--project={PROJECT_ID}"]
    if mode == "dry-run":
        print(f"[DRY-RUN] Enable APIs: {' '.join(create_args)}")
        return
    if mode == "check":
        res = run_command(
            [
                "gcloud",
                "services",
                "list",
                "--enabled",
                f"--project={PROJECT_ID}",
                "--format=value(config.name)",
            ],
            check=False,
        )
        enabled = set(res.stdout.split())
        for api in apis:
            ok = api in enabled
            print(f"  {'OK     ' if ok else 'MISSING'} : API {api}")
            if not ok:
                missing.append(f"API {api}")
        return
    print("[apply] Enabling required APIs")
    run_command(create_args, check=False)


def ensure_artifact_registry(mode, missing):
    _apply_or_check(
        mode,
        missing,
        [
            "gcloud",
            "artifacts",
            "repositories",
            "create",
            "animetix-repo",
            "--repository-format=docker",
            f"--location={WEB_REGION}",
            f"--project={PROJECT_ID}",
        ],
        [
            "gcloud",
            "artifacts",
            "repositories",
            "describe",
            "animetix-repo",
            f"--location={WEB_REGION}",
            f"--project={PROJECT_ID}",
        ],
        "Artifact Registry repo animetix-repo",
    )


def ensure_tasks_queue(mode, missing):
    _apply_or_check(
        mode,
        missing,
        [
            "gcloud",
            "tasks",
            "queues",
            "create",
            "animetix-queue",
            f"--location={INFRA_REGION}",
            f"--project={PROJECT_ID}",
        ],
        [
            "gcloud",
            "tasks",
            "queues",
            "describe",
            "animetix-queue",
            f"--location={INFRA_REGION}",
            f"--project={PROJECT_ID}",
        ],
        "Cloud Tasks queue animetix-queue",
    )


def ensure_buckets(mode, missing):
    buckets = [
        ("animetix-media-bucket", WEB_REGION),
        ("animetix-vertex-pipelines-staging", INFRA_REGION),
        ("animetix-dataflow", INFRA_REGION),
    ]
    for name, loc in buckets:
        _apply_or_check(
            mode,
            missing,
            [
                "gcloud",
                "storage",
                "buckets",
                "create",
                f"gs://{name}",
                f"--location={loc}",
                "--uniform-bucket-level-access",
                f"--project={PROJECT_ID}",
            ],
            [
                "gcloud",
                "storage",
                "buckets",
                "describe",
                f"gs://{name}",
                f"--project={PROJECT_ID}",
            ],
            f"GCS bucket gs://{name}",
        )


def ensure_pubsub(mode, missing):
    for topic in ("animetix-events-topic", "lore-ingestion-topic"):
        _apply_or_check(
            mode,
            missing,
            ["gcloud", "pubsub", "topics", "create", topic, f"--project={PROJECT_ID}"],
            [
                "gcloud",
                "pubsub",
                "topics",
                "describe",
                topic,
                f"--project={PROJECT_ID}",
            ],
            f"Pub/Sub topic {topic}",
        )
    _apply_or_check(
        mode,
        missing,
        [
            "gcloud",
            "pubsub",
            "subscriptions",
            "create",
            "lore-ingestion-sub",
            "--topic=lore-ingestion-topic",
            f"--project={PROJECT_ID}",
        ],
        [
            "gcloud",
            "pubsub",
            "subscriptions",
            "describe",
            "lore-ingestion-sub",
            f"--project={PROJECT_ID}",
        ],
        "Pub/Sub subscription lore-ingestion-sub",
    )


def ensure_bigquery(mode, missing):
    _apply_or_check(
        mode,
        missing,
        [
            "bq",
            f"--project_id={PROJECT_ID}",
            "mk",
            "--dataset",
            f"--location={WEB_REGION}",
            f"{PROJECT_ID}:telemetry",
        ],
        ["bq", f"--project_id={PROJECT_ID}", "show", f"{PROJECT_ID}:telemetry"],
        "BigQuery dataset telemetry",
    )
    tables = {
        "user_interactions": "event_id:STRING,user_id:STRING,media_item_id:STRING,interaction_type:STRING,weight:FLOAT,created_at:TIMESTAMP",
        "archetype_drift": "event_id:STRING,user_id:STRING,archetype_id:STRING,intensity:FLOAT,shonen_affinity:FLOAT,seinen_affinity:FLOAT,logic_consistency:FLOAT,created_at:TIMESTAMP",
    }
    for table, schema in tables.items():
        _apply_or_check(
            mode,
            missing,
            [
                "bq",
                f"--project_id={PROJECT_ID}",
                "mk",
                "--table",
                f"{PROJECT_ID}:telemetry.{table}",
                schema,
            ],
            [
                "bq",
                f"--project_id={PROJECT_ID}",
                "show",
                f"{PROJECT_ID}:telemetry.{table}",
            ],
            f"BigQuery table telemetry.{table}",
        )


def _sa_email(name):
    return f"{name}@{PROJECT_ID}.iam.gserviceaccount.com"


def ensure_service_accounts(mode, missing):
    accounts = [
        ("animetix-tasks-invoker", "Cloud Tasks OIDC invoker", ["roles/run.invoker"]),
        (
            "animetix-vertex-sa",
            "Vertex AI pipelines SA",
            ["roles/aiplatform.user", "roles/storage.objectAdmin"],
        ),
    ]
    for name, display, roles in accounts:
        _apply_or_check(
            mode,
            missing,
            [
                "gcloud",
                "iam",
                "service-accounts",
                "create",
                name,
                f"--display-name={display}",
                f"--project={PROJECT_ID}",
            ],
            [
                "gcloud",
                "iam",
                "service-accounts",
                "describe",
                _sa_email(name),
                f"--project={PROJECT_ID}",
            ],
            f"Service account {name}",
        )
        if mode == "apply":
            for role in roles:
                run_command(
                    [
                        "gcloud",
                        "projects",
                        "add-iam-policy-binding",
                        PROJECT_ID,
                        f"--member=serviceAccount:{_sa_email(name)}",
                        f"--role={role}",
                    ],
                    check=False,
                )
        elif mode == "dry-run":
            for role in roles:
                print(f"[DRY-RUN] bind {role} to {_sa_email(name)}")

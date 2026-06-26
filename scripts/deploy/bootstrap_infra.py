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

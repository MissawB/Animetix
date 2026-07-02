import os
import shutil
import subprocess
import sys

import yaml


def run_command(cmd_args, check=True):
    # Resolve command path (especially important for gcloud cmd/bat on Windows)
    resolved_cmd = shutil.which(cmd_args[0])
    if resolved_cmd:
        cmd_args[0] = resolved_cmd

    print(f"Running: {' '.join(cmd_args)}")
    result = subprocess.run(cmd_args, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error executing command: {' '.join(cmd_args)}")
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


def main():
    project_id = "animetix"
    region = "europe-west9"
    scheduler_region = "europe-west1"  # Cloud Scheduler is not available in europe-west9, using europe-west1
    service_account = "836616987676-compute@developer.gserviceaccount.com"
    image = f"{region}-docker.pkg.dev/{project_id}/animetix-repo/web:latest"
    vpc_network = os.getenv("GCP_VPC_NETWORK", "default")
    vpc_subnet = os.getenv("GCP_VPC_SUBNET", "default")

    # Configuration for all 8 serverless periodic jobs
    jobs_config = [
        {
            "name": "animetix-sync-catalog",
            "args": "backend/api/manage.py,sync_catalog",
            "schedule": "0 2 * * *",
            "memory": "2Gi",
            "cpu": "1",
        },
        {
            "name": "animetix-dpo-optimization",
            "args": "backend/api/manage.py,run_scheduled_task,dpo-optimization-daily",
            "schedule": "0 3 * * *",
            "memory": "2Gi",
            "cpu": "1",
        },
        {
            "name": "animetix-data-ingestion",
            "args": "backend/api/manage.py,run_scheduled_task,daily-data-ingestion",
            "schedule": "0 3 * * *",
            "memory": "4Gi",
            "cpu": "2",
        },
        {
            "name": "animetix-maintenance-mlops",
            "args": "backend/api/manage.py,run_scheduled_task,daily-maintenance-mlops",
            "schedule": "0 5 * * *",
            "memory": "4Gi",
            "cpu": "2",
        },
        {
            "name": "animetix-health-monitoring",
            "args": "backend/api/manage.py,run_scheduled_task,hourly-health-monitoring",
            "schedule": "0 * * * *",
            "memory": "2Gi",
            "cpu": "1",
        },
        {
            "name": "animetix-lora-sensor",
            "args": "backend/api/manage.py,run_scheduled_task,gold-dataset-lora-sensor",
            "schedule": "*/10 * * * *",
            "memory": "2Gi",
            "cpu": "1",
        },
        {
            "name": "animetix-dpo-sensor",
            "args": "backend/api/manage.py,run_scheduled_task,gold-dataset-dpo-sensor",
            "schedule": "*/10 * * * *",
            "memory": "2Gi",
            "cpu": "1",
        },
        {
            "name": "animetix-manga-updates",
            "args": "backend/api/manage.py,run_scheduled_task,manga-updates-check",
            "schedule": "0 */6 * * *",  # toutes les 6 h
            "memory": "2Gi",
            "cpu": "1",
        },
    ]

    # 1. Enable Cloud Scheduler API
    print("Step 1: Enabling Cloud Scheduler API...")
    run_command(
        [
            "gcloud",
            "services",
            "enable",
            "cloudscheduler.googleapis.com",
            f"--project={project_id}",
        ]
    )

    # Write env vars to a YAML file to avoid Windows shell escaping/comma issues
    # Variables d'environnement NON sensibles uniquement. Les secrets (tokens, clés)
    # passent par Secret Manager via `--set-secrets` ci-dessous — JAMAIS en dur ici.
    env_vars_data = {
        "ALLOWED_HOSTS": "*.run.app,missawb-animetix-web.hf.space,localhost,127.0.0.1",
        "DJANGO_ENV": "production",
        "SENTRY_DSN": "https://16adfd8a3ea5046c55ba1c7a4a919619@o4511298977202176.ingest.de.sentry.io/4511298998894672",
    }

    temp_yaml_path = "env_vars_temp.yaml"
    with open(temp_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(env_vars_data, f, default_flow_style=False)

    try:
        secrets = (
            "DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest,"
            "BRAIN_API_KEY=BRAIN_API_KEY:latest,"
            "TMDB_API_KEY=TMDB_API_KEY:latest,"
            "DATABASE_URL=DATABASE_URL:latest,"
            "REDIS_URL=REDIS_URL:latest,"
            "IGDB_CLIENT_ID=IGDB_CLIENT_ID:latest,"
            "GEMINI_API_KEY=GEMINI_API_KEY:latest,"
            "HF_TOKEN=HF_TOKEN:latest,"
            "HF_SPACES=HF_SPACES:latest,"
            "IGDB_CLIENT_SECRET=IGDB_CLIENT_SECRET:latest,"
            "WANDB_API_KEY=WANDB_API_KEY:latest"
        )

        for job in jobs_config:
            job_name = job["name"]

            # 2. Check and Create/Update Cloud Run Job
            print(f"\nChecking Cloud Run Job status for '{job_name}'...")
            check_job = run_command(
                [
                    "gcloud",
                    "run",
                    "jobs",
                    "describe",
                    job_name,
                    f"--region={region}",
                    f"--project={project_id}",
                ],
                check=False,
            )

            action = "update" if check_job.returncode == 0 else "create"
            print(
                f"Job '{job_name}' check returned code {check_job.returncode}. Action: {action}"
            )

            deploy_cmd = [
                "gcloud",
                "run",
                "jobs",
                action,
                job_name,
                f"--image={image}",
                "--command=python",
                f"--args={job['args']}",
                f"--region={region}",
                f"--service-account={service_account}",
                f"--network={vpc_network}",
                f"--subnet={vpc_subnet}",
                "--vpc-egress=private-ranges-only",
                f"--memory={job['memory']}",
                f"--cpu={job['cpu']}",
                f"--env-vars-file={temp_yaml_path}",
                f"--set-secrets={secrets}",
                f"--project={project_id}",
            ]

            run_command(deploy_cmd)

            # 3. Check and Create/Update Cloud Scheduler Job
            scheduler_job_name = f"{job_name}-trigger"
            print(f"Checking Cloud Scheduler Job status for '{scheduler_job_name}'...")
            check_sched = run_command(
                [
                    "gcloud",
                    "scheduler",
                    "jobs",
                    "describe",
                    scheduler_job_name,
                    f"--location={scheduler_region}",
                    f"--project={project_id}",
                ],
                check=False,
            )

            sched_action = "update" if check_sched.returncode == 0 else "create"
            uri = f"https://{region}-run.googleapis.com/v2/projects/{project_id}/locations/{region}/jobs/{job_name}:run"

            sched_cmd = [
                "gcloud",
                "scheduler",
                "jobs",
                sched_action,
                "http",
                scheduler_job_name,
                f"--location={scheduler_region}",
                f"--schedule={job['schedule']}",
                "--time-zone=Europe/Paris",
                f"--uri={uri}",
                "--http-method=POST",
                f"--oauth-service-account-email={service_account}",
                f"--project={project_id}",
            ]

            run_command(sched_cmd)

        print("\nAll 8 periodic jobs deployed successfully!")

    finally:
        if os.path.exists(temp_yaml_path):
            os.remove(temp_yaml_path)


if __name__ == "__main__":
    main()

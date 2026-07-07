import json
import os
import shutil
import subprocess
import sys

import yaml


def run_command(cmd_args, check=True):
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


def find_project_root():
    current = os.path.abspath(__file__)
    for _ in range(4):
        current = os.path.dirname(current)
    return current


def load_config():
    root = find_project_root()
    config_path = os.path.join(root, "deploy", "deployments.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    project_id = config["global"]["project_id"]
    jobs_root = config["gcp_services"]["jobs"]

    region = jobs_root["region"]
    scheduler_region = jobs_root["scheduler_region"]
    service_account = jobs_root["service_account"]
    image = f"{jobs_root['image_base']}:latest"
    vpc_connector = os.getenv("GCP_VPC_CONNECTOR", jobs_root["vpc_connector"])
    jobs_config = jobs_root["items"]

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

    # BRAIN_API_URL is REQUIRED at import time (containers/inference.py runs
    # validate_inference_config on django.setup()), so the jobs crash without it.
    brain_api_url = os.getenv("BRAIN_API_URL", "").strip()
    if not brain_api_url:
        res = run_command(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                config["gcp_services"].get("web", {}).get("name", "animetix-web"),
                f"--region={config['global']['regions']['web']}",
                f"--project={project_id}",
                "--format=json",
            ],
            check=False,
        )
        try:
            svc = json.loads(res.stdout or "{}")
            envs = svc["spec"]["template"]["spec"]["containers"][0].get("env", [])
            brain_api_url = next(
                (e.get("value", "") for e in envs if e.get("name") == "BRAIN_API_URL"),
                "",
            ).strip()
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            brain_api_url = ""
    if not brain_api_url:
        print(
            "ERROR: could not resolve BRAIN_API_URL (not in env and not found on the "
            "animetix-web service). Deploy the web service + deploy_brain.py first, "
            "or set BRAIN_API_URL=... before running this script.\n"
            "The jobs would crash on django.setup() without it."
        )
        sys.exit(1)

    # Write env vars to a YAML file to avoid Windows shell escaping/comma issues
    env_vars_data = {
        "ALLOWED_HOSTS": "*.run.app,missawb-animetix-web.hf.space,localhost,127.0.0.1",
        "DJANGO_ENV": "production",
        "BRAIN_API_URL": brain_api_url,
        "DJANGO_DB_USE_IAM": "false",
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
            "WANDB_API_KEY=WANDB_API_KEY:latest,"
            "NEO4J_URI=NEO4J_URI:latest,"
            "NEO4J_USER=NEO4J_USER:latest,"
            "NEO4J_PASSWORD=NEO4J_PASSWORD:latest"
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
                f"--vpc-connector={vpc_connector}",
                "--vpc-egress=private-ranges-only",
                f"--memory={job['memory']}",
                f"--cpu={job['cpu']}",
                f"--task-timeout={job.get('timeout', '3600s')}",
                f"--env-vars-file={temp_yaml_path}",
                f"--set-secrets={secrets}",
                f"--project={project_id}",
            ]

            run_command(deploy_cmd)

            if not job.get("schedule"):
                print(
                    f"Job '{job_name}' has no schedule — on-demand only, "
                    "skipping Cloud Scheduler."
                )
                continue

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

        print(f"\nAll {len(jobs_config)} jobs deployed successfully!")

    finally:
        if os.path.exists(temp_yaml_path):
            os.remove(temp_yaml_path)


if __name__ == "__main__":
    main()

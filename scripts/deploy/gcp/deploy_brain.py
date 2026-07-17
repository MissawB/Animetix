import os
import shutil
import subprocess
import sys

import yaml

# Windows consoles/redirected pipes default to cp1252, which cannot encode the
# ✅ (and other non-Latin-1) characters this script and gcloud emit. Without
# this, a fully successful deploy crashes on its final status print with
# UnicodeEncodeError and exits non-zero. Force UTF-8 so success reports as success.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


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


def get_git_tag():
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "latest"


def main():
    config = load_config()
    project_id = config["global"]["project_id"]
    brain_config = config["gcp_services"]["brain"]
    web_region = config["global"]["regions"]["web"]

    git_tag = get_git_tag()
    image_tag = f"{brain_config['image_base']}:{git_tag}"

    # Step 1: Build de l'image via Cloud Build
    print("\n--- Step 1: Building Brain API image with Google Cloud Build ---")
    build_cmd = [
        "gcloud",
        "builds",
        "submit",
        "--config=cloudbuild.yaml",
        f"--project={project_id}",
        f"--substitutions=_BUILD_TARGET=brain,_TAG={git_tag}",
        ".",
    ]
    run_command(build_cmd)

    # Step 2: Déploiement du service Brain API sur Cloud Run GPU
    print("\n--- Step 2: Deploying Brain API with Nvidia L4 GPU on Cloud Run ---")
    secrets_str = ",".join(brain_config["secrets"])
    env_vars_str = ",".join([f"{k}={v}" for k, v in brain_config["env_vars"].items()])

    deploy_cmd = [
        "gcloud",
        "beta",
        "run",
        "deploy",
        brain_config["name"],
        f"--image={image_tag}",
        f"--region={brain_config['region']}",
        f"--service-account={brain_config['service_account']}",
        f"--network={brain_config['vpc_network']}",
        f"--subnet={brain_config['vpc_subnet']}",
        "--vpc-egress=private-ranges-only",
    ]

    for vol in brain_config.get("volumes", []):
        deploy_cmd.append(
            f"--add-volume=name={vol['name']},type={vol['type']},bucket={vol['bucket']}"
        )
        deploy_cmd.append(
            f"--add-volume-mount=volume={vol['name']},mount-path={vol['mount_path']}"
        )

    deploy_cmd.extend(
        [
            f"--gpu={brain_config['gpu']}",
            f"--gpu-type={brain_config['gpu_type']}",
            f"--cpu={brain_config['cpu']}",
            f"--memory={brain_config['memory']}",
            "--no-cpu-throttling",
            f"--min-instances={brain_config['min_instances']}",
            f"--max-instances={brain_config['max_instances']}",
            f"--set-secrets={secrets_str}",
            f"--set-env-vars={env_vars_str}",
            f"--port={brain_config['port']}",
            "--allow-unauthenticated",
            f"--project={project_id}",
        ]
    )

    run_command(deploy_cmd)

    # Step 3: Récupération de l'URL du service Brain API
    print("\n--- Step 3: Retrieving Brain API URL ---")
    url_cmd = [
        "gcloud",
        "run",
        "services",
        "describe",
        brain_config["name"],
        f"--region={brain_config['region']}",
        "--format=value(status.url)",
        f"--project={project_id}",
    ]
    res_url = run_command(url_cmd)
    brain_url = res_url.stdout.strip()
    if not brain_url:
        print("Error: Could not retrieve Brain API URL.")
        sys.exit(1)
    print(f"Brain API URL is: {brain_url}")

    # Step 4: Liaison dans le service web Django principal
    print("\n--- Step 4: Linking Brain API URL to animetix-web ---")
    link_cmd = [
        "gcloud",
        "run",
        "services",
        "update",
        config["gcp_services"].get("web", {}).get("name", "animetix-web"),
        f"--region={web_region}",
        f"--update-env-vars=BRAIN_API_URL={brain_url}",
        f"--project={project_id}",
    ]
    run_command(link_cmd)

    print(
        "\n✅ Heavy ML Inference successfully deployed on Cloud Run GPU Serverless and linked to Django!"
    )


if __name__ == "__main__":
    main()

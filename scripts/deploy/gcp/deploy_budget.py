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
    budget_config = config["gcp_services"]["budget"]

    region = budget_config["region"]
    brain_region = budget_config["brain_region"]
    topic_name = budget_config["topic_name"]
    sub_name = budget_config["subscription_name"]
    invoker_sa = budget_config["invoker_service_account"]
    web_service_name = config["gcp_services"].get("web", {}).get("name", "animetix-web")

    # 1. Récupération dynamique du nom complet du compte de facturation (Billing Account)
    print("\n--- Step 1: Retrieving Billing Account ---")
    billing_desc = run_command(
        [
            "gcloud",
            "billing",
            "projects",
            "describe",
            project_id,
            "--format=value(billingAccountName)",
        ]
    )
    billing_account_name = billing_desc.stdout.strip()
    if not billing_account_name:
        print("Error: Could not retrieve Billing Account associated with the project.")
        sys.exit(1)

    billing_account_id = billing_account_name.replace("billingAccounts/", "")
    print(f"Associated Billing Account ID is: {billing_account_id}")

    # 2. Création du Topic Pub/Sub
    print("\n--- Step 2: Creating Pub/Sub Topic ---")
    run_command(
        ["gcloud", "pubsub", "topics", "create", topic_name, f"--project={project_id}"],
        check=False,
    )

    # 3. Récupération de l'URL du service Django animetix-web
    print("\n--- Step 3: Retrieving Django Webhook URL ---")
    web_url_desc = run_command(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            web_service_name,
            f"--region={region}",
            "--format=value(status.url)",
            f"--project={project_id}",
        ]
    )
    web_url = web_url_desc.stdout.strip()
    if not web_url:
        print("Error: Could not retrieve Django web service URL.")
        sys.exit(1)

    webhook_url = f"{web_url}/api/billing/webhook/"
    print(f"Webhook Push Endpoint is: {webhook_url}")

    # 4. Provisionnement du compte de service pour la souscription Pub/Sub push
    print("\n--- Step 4: Creating Subscription Invoker Service Account ---")
    invoker_sa_email = f"{invoker_sa}@{project_id}.iam.gserviceaccount.com"
    run_command(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "create",
            invoker_sa,
            "--display-name=Service Account for PubSub Budget push subscription",
            f"--project={project_id}",
        ],
        check=False,
    )

    # Autoriser ce SA à appeler le service animetix-web
    run_command(
        [
            "gcloud",
            "run",
            "services",
            "add-iam-policy-binding",
            web_service_name,
            f"--member=serviceAccount:{invoker_sa_email}",
            "--role=roles/run.invoker",
            f"--region={region}",
            f"--project={project_id}",
        ]
    )

    # 5. Création de la souscription Pub/Sub Push sécurisée par OIDC
    print("\n--- Step 5: Creating Push Subscription ---")
    run_command(
        [
            "gcloud",
            "pubsub",
            "subscriptions",
            "delete",
            sub_name,
            f"--project={project_id}",
        ],
        check=False,
    )

    run_command(
        [
            "gcloud",
            "pubsub",
            "subscriptions",
            "create",
            sub_name,
            f"--topic={topic_name}",
            f"--push-endpoint={webhook_url}",
            f"--push-auth-service-account={invoker_sa_email}",
            f"--push-auth-token-audience={webhook_url}",
            f"--project={project_id}",
        ]
    )

    # 6. Attribution du rôle run.developer au service account Django sur la Brain API
    print(
        "\n--- Step 6: Assigning IAM Permissions for django-web to manage animetix-brain ---"
    )
    web_sa = config["global"]["service_account"]
    brain_service_name = (
        config["gcp_services"].get("brain", {}).get("name", "animetix-brain")
    )
    run_command(
        [
            "gcloud",
            "run",
            "services",
            "add-iam-policy-binding",
            brain_service_name,
            f"--member=serviceAccount:{web_sa}",
            "--role=roles/run.developer",
            f"--region={brain_region}",
            f"--project={project_id}",
        ]
    )

    # 7. Création ou mise à jour du budget facturation
    print("\n--- Step 7: Configuring GCP Billing Budget ---")
    budget_name = "animetix-monthly-budget"

    run_command(
        [
            "gcloud",
            "beta",
            "billing",
            "budgets",
            "delete",
            f"projects/{project_id}/budgets/{budget_name}",
            f"--billing-account={billing_account_id}",
            f"--project={project_id}",
        ],
        check=False,
    )

    run_command(
        [
            "gcloud",
            "beta",
            "billing",
            "budgets",
            "create",
            f"--billing-account={billing_account_id}",
            f"--display-name={budget_name}",
            "--budget-amount=100USD",
            "--threshold-rule=percent=0.5,percent=0.9,percent=1.0",
            "--all-services",
            f"--pubsub-topic=projects/{project_id}/topics/{topic_name}",
            f"--project={project_id}",
        ]
    )

    print("\n✅ Budget Caps and notifications successfully deployed on GCP project!")


if __name__ == "__main__":
    main()

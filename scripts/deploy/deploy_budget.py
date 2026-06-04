import subprocess
import sys
import shutil
import json
import os

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

def main():
    project_id = "animetix"
    region = "europe-west9" # Region principal de Django
    brain_region = "europe-west1" # Inférence GPU L4
    topic_name = "animetix-budget-alerts"
    sub_name = "animetix-budget-alerts-push"
    
    # 1. Récupération dynamique du nom complet du compte de facturation (Billing Account)
    print("\n--- Step 1: Retrieving Billing Account ---")
    billing_desc = run_command([
        "gcloud", "billing", "projects", "describe", project_id,
        "--format=value(billingAccountName)"
    ])
    billing_account_name = billing_desc.stdout.strip()
    if not billing_account_name:
        print("Error: Could not retrieve Billing Account associated with the project.")
        sys.exit(1)
        
    # billing_account_name est sous la forme 'billingAccounts/XXXXXX-YYYYYY-ZZZZZZ'
    billing_account_id = billing_account_name.replace("billingAccounts/", "")
    print(f"Associated Billing Account ID is: {billing_account_id}")

    # 2. Création du Topic Pub/Sub
    print("\n--- Step 2: Creating Pub/Sub Topic ---")
    run_command([
        "gcloud", "pubsub", "topics", "create", topic_name,
        f"--project={project_id}"
    ], check=False)

    # 3. Récupération de l'URL du service Django animetix-web
    print("\n--- Step 3: Retrieving Django Webhook URL ---")
    web_url_desc = run_command([
        "gcloud", "run", "services", "describe", "animetix-web",
        f"--region={region}",
        "--format=value(status.url)",
        f"--project={project_id}"
    ])
    web_url = web_url_desc.stdout.strip()
    if not web_url:
        print("Error: Could not retrieve Django web service URL.")
        sys.exit(1)
        
    webhook_url = f"{web_url}/api/billing/webhook/"
    print(f"Webhook Push Endpoint is: {webhook_url}")

    # 4. Provisionnement du compte de service pour la souscription Pub/Sub push
    print("\n--- Step 4: Creating Subscription Invoker Service Account ---")
    invoker_sa = "animetix-budget-invoker"
    invoker_sa_email = f"{invoker_sa}@{project_id}.iam.gserviceaccount.com"
    run_command([
        "gcloud", "iam", "service-accounts", "create", invoker_sa,
        "--display-name=Service Account for PubSub Budget push subscription",
        f"--project={project_id}"
    ], check=False)

    # Autoriser ce SA à appeler le service animetix-web
    run_command([
        "gcloud", "run", "services", "add-iam-policy-binding", "animetix-web",
        f"--member=serviceAccount:{invoker_sa_email}",
        "--role=roles/run.invoker",
        f"--region={region}",
        f"--project={project_id}"
    ])

    # 5. Création de la souscription Pub/Sub Push sécurisée par OIDC
    print("\n--- Step 5: Creating Push Subscription ---")
    # Supprimer la souscription existante pour s'assurer que l'audience et l'URL sont correctes
    run_command([
        "gcloud", "pubsub", "subscriptions", "delete", sub_name,
        f"--project={project_id}"
    ], check=False)

    run_command([
        "gcloud", "pubsub", "subscriptions", "create", sub_name,
        f"--topic={topic_name}",
        f"--push-endpoint={webhook_url}",
        f"--push-auth-service-account={invoker_sa_email}",
        f"--push-auth-token-audience={webhook_url}",
        f"--project={project_id}"
    ])

    # 6. Attribution du rôle run.developer au service account Django sur la Brain API
    print("\n--- Step 6: Assigning IAM Permissions for django-web to manage animetix-brain ---")
    web_sa = f"836616987676-compute@developer.gserviceaccount.com"
    run_command([
        "gcloud", "run", "services", "add-iam-policy-binding", "animetix-brain",
        f"--member=serviceAccount:{web_sa}",
        "--role=roles/run.developer",
        f"--region={brain_region}",
        f"--project={project_id}"
    ])

    # 7. Création ou mise à jour du budget facturation
    print("\n--- Step 7: Configuring GCP Billing Budget ---")
    budget_name = "animetix-monthly-budget"
    
    # Supprimer le budget existant s'il existe pour éviter le doublon
    run_command([
        "gcloud", "beta", "billing", "budgets", "delete",
        f"projects/{project_id}/budgets/{budget_name}",
        f"--billing-account={billing_account_id}",
        f"--project={project_id}"
    ], check=False)
    
    # Création du budget à $100 relié au topic Pub/Sub
    run_command([
        "gcloud", "beta", "billing", "budgets", "create",
        f"--billing-account={billing_account_id}",
        f"--display-name={budget_name}",
        "--budget-amount=100USD",
        "--threshold-rule=percent=0.5,percent=0.9,percent=1.0",
        "--all-services",
        f"--pubsub-topic=projects/{project_id}/topics/{topic_name}",
        f"--project={project_id}"
    ])
    
    print("\n✅ Budget Caps and notifications successfully deployed on GCP project!")

if __name__ == "__main__":
    main()

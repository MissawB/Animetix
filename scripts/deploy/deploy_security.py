import shutil
import subprocess
import sys


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
    policy_name = "animetix-edge-security-policy"

    # Step 1: Activation des APIs nécessaires
    print("Step 1: Enabling Compute Engine API (required for Cloud Armor)...")
    run_command(
        [
            "gcloud",
            "services",
            "enable",
            "compute.googleapis.com",
            f"--project={project_id}",
        ]
    )

    # Step 2: Vérification / Création de la politique de sécurité
    print(f"\nStep 2: Checking Cloud Armor Security Policy '{policy_name}'...")
    check_policy = run_command(
        [
            "gcloud",
            "compute",
            "security-policies",
            "describe",
            policy_name,
            f"--project={project_id}",
        ],
        check=False,
    )

    if check_policy.returncode != 0:
        print(f"Security policy '{policy_name}' does not exist. Creating...")
        run_command(
            [
                "gcloud",
                "compute",
                "security-policies",
                "create",
                policy_name,
                "--description=Cloud Armor WAF Policy for Animetix (OWASP Web & LLM/Token DoS mitigation)",
                f"--project={project_id}",
            ]
        )
    else:
        print(f"Security policy '{policy_name}' already exists.")

    # Définition de la liste des règles à configurer de manière idempotente
    rules_config = [
        # 1. Rate Limiting pour prévenir le Token DoS
        {
            "priority": "1000",
            "description": "Rate limiting per IP to mitigate Token DoS and flooding",
            "args": [
                "--action=throttle",
                "--src-ip-ranges=*",
                "--rate-limit-threshold-count=100",
                "--rate-limit-threshold-interval-sec=60",
                "--conform-action=allow",
                "--exceed-action=deny-429",
                "--enforce-on-key=ip",
            ],
        },
        # 2. WAF - SQL Injection
        {
            "priority": "2000",
            "description": "OWASP CRS SQL Injection protection",
            "args": [
                "--action=deny-403",
                "--expression=evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1})",
            ],
        },
        # 3. WAF - Cross-Site Scripting (XSS)
        {
            "priority": "2100",
            "description": "OWASP CRS XSS protection",
            "args": [
                "--action=deny-403",
                "--expression=evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1})",
            ],
        },
        # 4. WAF - Remote Command Execution (RCE)
        {
            "priority": "2200",
            "description": "OWASP CRS RCE protection",
            "args": [
                "--action=deny-403",
                "--expression=evaluatePreconfiguredWaf('rce-v33-stable', {'sensitivity': 1})",
            ],
        },
        # 5. Règle Custom CEL pour prompt injection
        {
            "priority": "3000",
            "description": "Custom LLM Prompt Injection filter",
            "args": [
                "--action=deny-403",
                "--expression=request.body.matches('(?i)(ignore.*previous.*instruction|system.*prompt.*override|bypass.*filter|jailbreak)')",
            ],
        },
    ]

    # Step 3: Configuration des règles
    print("\nStep 3: Configuring security rules...")
    for rule in rules_config:
        prio = rule["priority"]
        print(f"\nChecking rule at priority {prio} ({rule['description']})...")

        check_rule = run_command(
            [
                "gcloud",
                "compute",
                "security-policies",
                "rules",
                "describe",
                prio,
                f"--security-policy={policy_name}",
                f"--project={project_id}",
            ],
            check=False,
        )

        action = "update" if check_rule.returncode == 0 else "create"
        print(f"Rule {prio} action: {action}")

        cmd = [
            "gcloud",
            "compute",
            "security-policies",
            "rules",
            action,
            prio,
            f"--security-policy={policy_name}",
            f"--description={rule['description']}",
            f"--project={project_id}",
        ] + rule["args"]

        run_command(cmd)

    print(
        "\n✅ Google Cloud Armor security policies and rules successfully configured!"
    )
    print(
        "\nTo associate this security policy with your Application Load Balancer backend service, run:"
    )
    print(
        f"gcloud compute backend-services update BACKEND_SERVICE_NAME --security-policy={policy_name} --global"
    )


if __name__ == "__main__":
    main()

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
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", config["global"]["project_id"])
    cdn_config = config["gcp_services"]["cdn"]

    bucket_name = os.getenv("GS_BUCKET_NAME", cdn_config["bucket_name"])
    domain_name = os.getenv("ANIMETIX_CDN_DOMAIN", None)

    backend_name = cdn_config["backend_name"]
    url_map_name = cdn_config["url_map_name"]
    ssl_cert_name = cdn_config["ssl_cert_name"]
    https_proxy_name = cdn_config["https_proxy_name"]
    https_rule_name = cdn_config["https_rule_name"]
    http_proxy_name = cdn_config["http_proxy_name"]
    http_rule_name = cdn_config["http_rule_name"]
    ip_name = cdn_config["ip_name"]

    # Step 1: Enable Compute Engine API
    print("Step 1: Enabling Compute Engine API...")
    run_command(
        [
            "gcloud",
            "services",
            "enable",
            "compute.googleapis.com",
            f"--project={project_id}",
        ]
    )

    # Step 2: Ensure static IP
    print(f"\nStep 2: Checking global static IP '{ip_name}'...")
    check_ip = run_command(
        [
            "gcloud",
            "compute",
            "addresses",
            "describe",
            ip_name,
            "--global",
            f"--project={project_id}",
        ],
        check=False,
    )

    if check_ip.returncode != 0:
        print(f"Creating global static IP '{ip_name}'...")
        run_command(
            [
                "gcloud",
                "compute",
                "addresses",
                "create",
                ip_name,
                "--global",
                f"--project={project_id}",
            ]
        )
    else:
        print(f"Global static IP '{ip_name}' already exists.")

    # Step 3: Ensure Backend Bucket with CDN enabled
    print(f"\nStep 3: Configuring Backend Bucket for '{bucket_name}'...")
    check_backend = run_command(
        [
            "gcloud",
            "compute",
            "backend-buckets",
            "describe",
            backend_name,
            f"--project={project_id}",
        ],
        check=False,
    )

    if check_backend.returncode != 0:
        print(f"Creating backend-bucket '{backend_name}' with Cloud CDN...")
        run_command(
            [
                "gcloud",
                "compute",
                "backend-buckets",
                "create",
                backend_name,
                f"--gcs-bucket-name={bucket_name}",
                "--enable-cdn",
                f"--project={project_id}",
            ]
        )
    else:
        print(f"Updating backend-bucket '{backend_name}' to ensure CDN is active...")
        run_command(
            [
                "gcloud",
                "compute",
                "backend-buckets",
                "update",
                backend_name,
                "--enable-cdn",
                f"--project={project_id}",
            ]
        )

    # Step 4: Ensure URL Map
    print("\nStep 4: Configuring URL map...")
    check_url_map = run_command(
        [
            "gcloud",
            "compute",
            "url-maps",
            "describe",
            url_map_name,
            f"--project={project_id}",
        ],
        check=False,
    )

    if check_url_map.returncode != 0:
        print(f"Creating URL Map '{url_map_name}'...")
        run_command(
            [
                "gcloud",
                "compute",
                "url-maps",
                "create",
                url_map_name,
                f"--default-backend-bucket={backend_name}",
                f"--project={project_id}",
            ]
        )
    else:
        print(f"URL Map '{url_map_name}' already exists.")

    # Step 5: Configure Proxy & Forwarding Rules
    if domain_name:
        print(f"\nStep 5: Configuring HTTPS for domain '{domain_name}'...")

        check_cert = run_command(
            [
                "gcloud",
                "compute",
                "ssl-certificates",
                "describe",
                ssl_cert_name,
                f"--project={project_id}",
            ],
            check=False,
        )
        if check_cert.returncode != 0:
            print("Creating SSL Certificate...")
            run_command(
                [
                    "gcloud",
                    "compute",
                    "ssl-certificates",
                    "create",
                    ssl_cert_name,
                    f"--domains={domain_name}",
                    f"--project={project_id}",
                ]
            )

        check_proxy = run_command(
            [
                "gcloud",
                "compute",
                "target-https-proxies",
                "describe",
                https_proxy_name,
                f"--project={project_id}",
            ],
            check=False,
        )
        if check_proxy.returncode != 0:
            print("Creating Target HTTPS Proxy...")
            run_command(
                [
                    "gcloud",
                    "compute",
                    "target-https-proxies",
                    "create",
                    https_proxy_name,
                    f"--url-map={url_map_name}",
                    f"--ssl-certificates={ssl_cert_name}",
                    f"--project={project_id}",
                ]
            )

        check_rule = run_command(
            [
                "gcloud",
                "compute",
                "forwarding-rules",
                "describe",
                https_rule_name,
                "--global",
                f"--project={project_id}",
            ],
            check=False,
        )
        if check_rule.returncode != 0:
            print("Creating Global Forwarding Rule for Port 443...")
            run_command(
                [
                    "gcloud",
                    "compute",
                    "forwarding-rules",
                    "create",
                    https_rule_name,
                    f"--address={ip_name}",
                    "--global",
                    f"--target-https-proxy={https_proxy_name}",
                    "--ports=443",
                    f"--project={project_id}",
                ]
            )
    else:
        print("\nStep 5: Configuring HTTP (fallback proxy)...")

        check_proxy = run_command(
            [
                "gcloud",
                "compute",
                "target-http-proxies",
                "describe",
                http_proxy_name,
                f"--project={project_id}",
            ],
            check=False,
        )
        if check_proxy.returncode != 0:
            print("Creating Target HTTP Proxy...")
            run_command(
                [
                    "gcloud",
                    "compute",
                    "target-http-proxies",
                    "create",
                    http_proxy_name,
                    f"--url-map={url_map_name}",
                    f"--project={project_id}",
                ]
            )

        check_rule = run_command(
            [
                "gcloud",
                "compute",
                "forwarding-rules",
                "describe",
                http_rule_name,
                "--global",
                f"--project={project_id}",
            ],
            check=False,
        )
        if check_rule.returncode != 0:
            print("Creating Global Forwarding Rule for Port 80...")
            run_command(
                [
                    "gcloud",
                    "compute",
                    "forwarding-rules",
                    "create",
                    http_rule_name,
                    f"--address={ip_name}",
                    "--global",
                    f"--target-http-proxy={http_proxy_name}",
                    "--ports=80",
                    f"--project={project_id}",
                ]
            )

    # Step 6: Set public GCS read permissions
    print(
        f"\nStep 6: Ensuring GCS bucket '{bucket_name}' has public-read viewer access..."
    )
    run_command(
        [
            "gcloud",
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{bucket_name}",
            "--member=allUsers",
            "--role=roles/storage.objectViewer",
            f"--project={project_id}",
        ],
        check=False,
    )

    print("\n✅ Google Cloud CDN and Load Balancer successfully configured!")


if __name__ == "__main__":
    main()

import os
import subprocess
import sys
import shutil

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
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "animetix")
    bucket_name = os.getenv("GS_BUCKET_NAME", "animetix-media-bucket")
    domain_name = os.getenv("ANIMETIX_CDN_DOMAIN", None)
    
    # Step 1: Enable Compute Engine API
    print("Step 1: Enabling Compute Engine API...")
    run_command([
        "gcloud", "services", "enable", "compute.googleapis.com",
        f"--project={project_id}"
    ])
    
    # Step 2: Ensure static IP
    print("\nStep 2: Checking global static IP 'animetix-cdn-ip'...")
    check_ip = run_command([
        "gcloud", "compute", "addresses", "describe", "animetix-cdn-ip",
        "--global", f"--project={project_id}"
    ], check=False)
    
    if check_ip.returncode != 0:
        print("Creating global static IP 'animetix-cdn-ip'...")
        run_command([
            "gcloud", "compute", "addresses", "create", "animetix-cdn-ip",
            "--global", f"--project={project_id}"
        ])
    else:
        print("Global static IP 'animetix-cdn-ip' already exists.")
        
    # Step 3: Ensure Backend Bucket with CDN enabled
    print(f"\nStep 3: Configuring Backend Bucket for '{bucket_name}'...")
    check_backend = run_command([
        "gcloud", "compute", "backend-buckets", "describe", "animetix-cdn-backend",
        f"--project={project_id}"
    ], check=False)
    
    if check_backend.returncode != 0:
        print("Creating backend-bucket 'animetix-cdn-backend' with Cloud CDN...")
        run_command([
            "gcloud", "compute", "backend-buckets", "create", "animetix-cdn-backend",
            f"--gcs-bucket-name={bucket_name}",
            "--enable-cdn",
            f"--project={project_id}"
        ])
    else:
        print("Updating backend-bucket 'animetix-cdn-backend' to ensure CDN is active...")
        run_command([
            "gcloud", "compute", "backend-buckets", "update", "animetix-cdn-backend",
            "--enable-cdn",
            f"--project={project_id}"
        ])
        
    # Step 4: Ensure URL Map
    print("\nStep 4: Configuring URL map...")
    check_url_map = run_command([
        "gcloud", "compute", "url-maps", "describe", "animetix-cdn-url-map",
        f"--project={project_id}"
    ], check=False)
    
    if check_url_map.returncode != 0:
        print("Creating URL Map 'animetix-cdn-url-map'...")
        run_command([
            "gcloud", "compute", "url-maps", "create", "animetix-cdn-url-map",
            "--default-backend-bucket=animetix-cdn-backend",
            f"--project={project_id}"
        ])
    else:
        print("URL Map 'animetix-cdn-url-map' already exists.")
        
    # Step 5: Configure Proxy & Forwarding Rules (HTTPS if domain provided, HTTP fallback otherwise)
    if domain_name:
        print(f"\nStep 5: Configuring HTTPS for domain '{domain_name}'...")
        
        # 5.1 SSL Certificate
        check_cert = run_command([
            "gcloud", "compute", "ssl-certificates", "describe", "animetix-cdn-cert",
            f"--project={project_id}"
        ], check=False)
        if check_cert.returncode != 0:
            print("Creating SSL Certificate...")
            run_command([
                "gcloud", "compute", "ssl-certificates", "create", "animetix-cdn-cert",
                f"--domains={domain_name}",
                f"--project={project_id}"
            ])
            
        # 5.2 HTTPS Target Proxy
        check_proxy = run_command([
            "gcloud", "compute", "target-https-proxies", "describe", "animetix-cdn-https-proxy",
            f"--project={project_id}"
        ], check=False)
        if check_proxy.returncode != 0:
            print("Creating Target HTTPS Proxy...")
            run_command([
                "gcloud", "compute", "target-https-proxies", "create", "animetix-cdn-https-proxy",
                "--url-map=animetix-cdn-url-map",
                "--ssl-certificates=animetix-cdn-cert",
                f"--project={project_id}"
            ])
            
        # 5.3 HTTPS Forwarding Rule
        check_rule = run_command([
            "gcloud", "compute", "forwarding-rules", "describe", "animetix-cdn-https-rule",
            "--global", f"--project={project_id}"
        ], check=False)
        if check_rule.returncode != 0:
            print("Creating Global Forwarding Rule for Port 443...")
            run_command([
                "gcloud", "compute", "forwarding-rules", "create", "animetix-cdn-https-rule",
                "--address=animetix-cdn-ip",
                "--global",
                "--target-https-proxy=animetix-cdn-https-proxy",
                "--ports=443",
                f"--project={project_id}"
            ])
    else:
        print("\nStep 5: Configuring HTTP (fallback proxy)...")
        
        # 5.1 HTTP Target Proxy
        check_proxy = run_command([
            "gcloud", "compute", "target-http-proxies", "describe", "animetix-cdn-http-proxy",
            f"--project={project_id}"
        ], check=False)
        if check_proxy.returncode != 0:
            print("Creating Target HTTP Proxy...")
            run_command([
                "gcloud", "compute", "target-http-proxies", "create", "animetix-cdn-http-proxy",
                "--url-map=animetix-cdn-url-map",
                f"--project={project_id}"
            ])
            
        # 5.2 HTTP Forwarding Rule
        check_rule = run_command([
            "gcloud", "compute", "forwarding-rules", "describe", "animetix-cdn-http-rule",
            "--global", f"--project={project_id}"
        ], check=False)
        if check_rule.returncode != 0:
            print("Creating Global Forwarding Rule for Port 80...")
            run_command([
                "gcloud", "compute", "forwarding-rules", "create", "animetix-cdn-http-rule",
                "--address=animetix-cdn-ip",
                "--global",
                "--target-http-proxy=animetix-cdn-http-proxy",
                "--ports=80",
                f"--project={project_id}"
            ])

    # Step 6: Set public GCS read permissions
    print(f"\nStep 6: Ensuring GCS bucket '{bucket_name}' has public-read viewer access...")
    run_command([
        "gcloud", "storage", "buckets", "add-iam-policy-binding", f"gs://{bucket_name}",
        "--member=allUsers",
        "--role=roles/storage.objectViewer",
        f"--project={project_id}"
    ], check=False)

    print("\n✅ Google Cloud CDN and Load Balancer successfully configured!")

if __name__ == "__main__":
    main()

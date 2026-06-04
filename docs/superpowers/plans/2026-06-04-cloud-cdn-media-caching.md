# Cloud CDN Media Caching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure Google Cloud CDN for the GCS media bucket and integrate it into Django to cache static assets and user-generated content, minimizing latency and egress costs.

**Architecture:** Use a dynamic GCS custom endpoint setting (`GS_CUSTOM_ENDPOINT`) in Django, deploy an external Global Application Load Balancer with CDN enabled using an idempotent Python deployment script, and verify via mocked unit tests.

**Tech Stack:** Django (django-storages, Google Cloud Storage), Google Cloud SDK (gcloud CLI), Python (subprocess), Pytest (mocking).

---

### Task 1: Django Settings Update

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Update settings.py to load GS_CUSTOM_ENDPOINT and pass it to STORAGES**

Update `backend/api/animetix_project/settings.py` around line 417:
```python
# Target lines to replace:
GS_BUCKET_NAME = env('GS_BUCKET_NAME', default=None)

if IS_PRODUCTION or GS_BUCKET_NAME:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
            'OPTIONS': {
                'bucket_name': GS_BUCKET_NAME,
                'project_id': env('GOOGLE_CLOUD_PROJECT', default='animetix'),
            }
        },
```
With:
```python
GS_BUCKET_NAME = env('GS_BUCKET_NAME', default=None)
GS_CUSTOM_ENDPOINT = env('GS_CUSTOM_ENDPOINT', default=None)

if IS_PRODUCTION or GS_BUCKET_NAME:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
            'OPTIONS': {
                'bucket_name': GS_BUCKET_NAME,
                'project_id': env('GOOGLE_CLOUD_PROJECT', default='animetix'),
                'custom_endpoint': GS_CUSTOM_ENDPOINT,
            }
        },
```

---

### Task 2: Create Deployment Script

**Files:**
- Create: `scripts/deploy/deploy_cdn.py`

- [ ] **Step 1: Write deploy_cdn.py script**

Create `scripts/deploy/deploy_cdn.py` with the following content:
```python
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
```

---

### Task 3: Create Deployment Unit Tests

**Files:**
- Create: `tests/deploy/test_deploy_cdn.py`

- [ ] **Step 1: Write test_deploy_cdn.py test suite**

Create `tests/deploy/test_deploy_cdn.py` with:
```python
import subprocess
from unittest.mock import patch, MagicMock
from scripts.deploy.deploy_cdn import main

@patch("subprocess.run")
def test_deploy_cdn_calls_gcloud_http_fallback(mock_run):
    # Mock subprocess.run for HTTP deployment (no domain in env)
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")
    
    with patch.dict("os.environ", {"ANIMETIX_CDN_DOMAIN": "", "GS_BUCKET_NAME": "animetix-test"}):
        main()
        
    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]
    
    # Assert API enabled
    assert any("services enable compute.googleapis.com" in c for c in flat_calls)
    # Assert static IP checked
    assert any("compute addresses describe animetix-cdn-ip" in c for c in flat_calls)
    # Assert backend bucket checked
    assert any("compute backend-buckets describe animetix-cdn-backend" in c for c in flat_calls)
    # Assert URL map checked
    assert any("compute url-maps describe animetix-cdn-url-map" in c for c in flat_calls)
    # Assert HTTP target proxy checked and HTTP forwarding rule checked
    assert any("compute target-http-proxies describe animetix-cdn-http-proxy" in c for c in flat_calls)
    assert any("compute forwarding-rules describe animetix-cdn-http-rule" in c for c in flat_calls)
    # Assert GCS public viewer policy bound
    assert any("storage buckets add-iam-policy-binding gs://animetix-test" in c for c in flat_calls)

@patch("subprocess.run")
def test_deploy_cdn_calls_gcloud_https_custom_domain(mock_run):
    # Mock subprocess.run for HTTPS deployment (with domain in env)
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")
    
    with patch.dict("os.environ", {"ANIMETIX_CDN_DOMAIN": "cdn.animetix.com", "GS_BUCKET_NAME": "animetix-test"}):
        main()
        
    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]
    
    # Assert SSL certificate checked
    assert any("compute ssl-certificates describe animetix-cdn-cert" in c for c in flat_calls)
    # Assert HTTPS proxy checked
    assert any("compute target-https-proxies describe animetix-cdn-https-proxy" in c for c in flat_calls)
    # Assert HTTPS forwarding rule checked
    assert any("compute forwarding-rules describe animetix-cdn-https-rule" in c for c in flat_calls)
```

- [ ] **Step 2: Run pytest to verify new deploy tests pass**

Run:
```bash
.venv\Scripts\pytest tests/deploy/test_deploy_cdn.py -v
```
Expected: 2 passed.

---

### Task 4: Create Django Settings Unit Test

**Files:**
- Modify: `tests/adapters/test_gcp_deployment_validation.py`

- [ ] **Step 1: Add unit test to verify GCS custom endpoint settings parsing**

Add the following test at the end of `tests/adapters/test_gcp_deployment_validation.py`:
```python
def test_gcs_storage_custom_endpoint(mocker):
    # Verify that the custom endpoint settings are correctly bound to GoogleCloudStorage
    from storages.backends.gcloud import GoogleCloudStorage
    
    # Mock the client property to prevent actual GCS credentials initialization
    mocker.patch(
        "storages.backends.gcloud.GoogleCloudStorage.client",
        new_callable=mocker.PropertyMock,
        return_value=MagicMock()
    )
    
    gcs_storage = GoogleCloudStorage(
        bucket_name="animetix-test-bucket", 
        custom_endpoint="https://cdn.animetix.com"
    )
    assert gcs_storage.custom_endpoint == "https://cdn.animetix.com"
```

- [ ] **Step 2: Run verification tests**

Run:
```bash
.venv\Scripts\pytest tests/adapters/test_gcp_deployment_validation.py -v
```
Expected: All tests pass.

- [ ] **Step 3: Commit all changes**

Run:
```bash
git add backend/api/animetix_project/settings.py scripts/deploy/deploy_cdn.py tests/deploy/test_deploy_cdn.py tests/adapters/test_gcp_deployment_validation.py
git commit -m "feat: implement Google Cloud CDN caching configuration and deploy automation script"
```

from unittest.mock import patch, MagicMock
from scripts.deploy.deploy_cdn import main


@patch("subprocess.run")
def test_deploy_cdn_calls_gcloud_http_fallback(mock_run):
    # Mock subprocess.run for HTTP deployment (no domain in env)
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")

    with patch.dict(
        "os.environ", {"ANIMETIX_CDN_DOMAIN": "", "GS_BUCKET_NAME": "animetix-test"}
    ):
        main()

    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]

    # Assert API enabled
    assert any("services enable compute.googleapis.com" in c for c in flat_calls)
    # Assert static IP checked
    assert any("compute addresses describe animetix-cdn-ip" in c for c in flat_calls)
    # Assert backend bucket checked
    assert any(
        "compute backend-buckets describe animetix-cdn-backend" in c for c in flat_calls
    )
    # Assert URL map checked
    assert any(
        "compute url-maps describe animetix-cdn-url-map" in c for c in flat_calls
    )
    # Assert HTTP target proxy checked and HTTP forwarding rule checked
    assert any(
        "compute target-http-proxies describe animetix-cdn-http-proxy" in c
        for c in flat_calls
    )
    assert any(
        "compute forwarding-rules describe animetix-cdn-http-rule" in c
        for c in flat_calls
    )
    # Assert GCS public viewer policy bound
    assert any(
        "storage buckets add-iam-policy-binding gs://animetix-test" in c
        for c in flat_calls
    )


@patch("subprocess.run")
def test_deploy_cdn_calls_gcloud_https_custom_domain(mock_run):
    # Mock subprocess.run for HTTPS deployment (with domain in env)
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")

    with patch.dict(
        "os.environ",
        {"ANIMETIX_CDN_DOMAIN": "cdn.animetix.com", "GS_BUCKET_NAME": "animetix-test"},
    ):
        main()

    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]

    # Assert SSL certificate checked
    assert any(
        "compute ssl-certificates describe animetix-cdn-cert" in c for c in flat_calls
    )
    # Assert HTTPS proxy checked
    assert any(
        "compute target-https-proxies describe animetix-cdn-https-proxy" in c
        for c in flat_calls
    )
    # Assert HTTPS forwarding rule checked
    assert any(
        "compute forwarding-rules describe animetix-cdn-https-rule" in c
        for c in flat_calls
    )

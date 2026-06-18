from unittest.mock import patch, MagicMock
from scripts.deploy.deploy_security import main


@patch("subprocess.run")
def test_deploy_security_calls_gcloud(mock_run):
    # Mock subprocess.run to return successful status code
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")

    # Run the deployment function
    main()

    # Retrieve all commands executed by the script
    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]

    # Assert APIs are enabled
    assert any("services enable compute.googleapis.com" in c for c in flat_calls)

    # Assert policy check and configuration happened
    assert any(
        "compute security-policies describe animetix-edge-security-policy" in c
        for c in flat_calls
    )

    # Assert check and updates for security-policies rules
    assert any("compute security-policies rules describe 1000" in c for c in flat_calls)
    assert any("compute security-policies rules describe 2000" in c for c in flat_calls)
    assert any("compute security-policies rules describe 2100" in c for c in flat_calls)
    assert any("compute security-policies rules describe 2200" in c for c in flat_calls)
    assert any("compute security-policies rules describe 3000" in c for c in flat_calls)

    # Assert rule configuration commands are called
    # For priority 1000 (throttle, exceed-action=deny-429)
    assert any(
        "compute security-policies rules update 1000" in c
        or "compute security-policies rules create 1000" in c
        for c in flat_calls
    )

    # For WAF rules
    assert any("sqli-v33-stable" in c for c in flat_calls)
    assert any("xss-v33-stable" in c for c in flat_calls)
    assert any("rce-v33-stable" in c for c in flat_calls)

    # For custom CEL prompt injection rule
    assert any("request.body.matches" in c for c in flat_calls)

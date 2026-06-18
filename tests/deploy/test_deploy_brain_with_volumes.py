import os
from unittest.mock import patch, MagicMock
from scripts.deploy.deploy_brain import main


@patch("subprocess.run")
def test_deploy_brain_calls_gcloud_with_volume_fuse(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")

    with patch.dict(
        os.environ, {"GCP_VPC_NETWORK": "test-network", "GCP_VPC_SUBNET": "test-subnet"}
    ):
        main()

    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]

    # Assert builds submit
    assert any("builds submit" in c for c in flat_calls)

    # Assert run deploy command with volumes exists
    run_deploys = [c for c in flat_calls if "run deploy animetix-brain" in c]
    assert len(run_deploys) > 0
    assert (
        "add-volume=name=models-vol,type=cloud-storage,bucket=animetix-models"
        in run_deploys[0]
    )
    assert "add-volume-mount=volume=models-vol,mount-path=/mnt/models" in run_deploys[0]
    assert "GCP_MODELS_MOUNT_PATH=/mnt/models" in run_deploys[0]

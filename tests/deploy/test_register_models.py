from unittest.mock import MagicMock, patch

from scripts.deploy.gcp.register_models import main


@patch("subprocess.run")
def test_register_models_calls_gcloud(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")

    main()

    calls = [call[0][0] for call in mock_run.call_args_list]
    flat_calls = [" ".join(cmd) for cmd in calls]

    assert any("services enable aiplatform.googleapis.com" in c for c in flat_calls)
    assert any("storage buckets describe gs://animetix-models" in c for c in flat_calls)
    assert any("ai models upload" in c for c in flat_calls)

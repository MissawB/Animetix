from unittest.mock import MagicMock

from scripts.deploy.gcp.deploy_jobs import main


def test_deploy_jobs_main(mocker):
    # Mock run_command in deploy_jobs
    mock_run = mocker.patch("scripts.deploy.gcp.deploy_jobs.run_command")

    # We want run_command to return a mock response
    mock_response = MagicMock()
    mock_response.returncode = 1  # Force action = create
    mock_run.return_value = mock_response

    # Run main
    main()

    # Assert run_command was called for Cloud Scheduler API enablement
    assert mock_run.call_args_list[0][0][0] == [
        "gcloud",
        "services",
        "enable",
        "cloudscheduler.googleapis.com",
        "--project=animetix",
    ]

    # 8 jobs are scheduled (1 describe run, 1 deploy run, 1 describe scheduler,
    # 1 deploy scheduler = 4 calls per job). The 9th job,
    # animetix-generate-drift-baselines, has schedule=None: it is created but
    # deliberately NOT wired to Cloud Scheduler (2 calls: describe run, deploy run).
    # Total calls: 1 (enable api) + 8 * 4 (scheduled jobs) + 1 * 2 (on-demand job) = 35
    assert len(mock_run.call_args_list) == 35

    # Check details of specific jobs
    # animetix-sync-catalog
    describe_catalog_job = mock_run.call_args_list[1][0][0]
    assert "animetix-sync-catalog" in describe_catalog_job
    assert "describe" in describe_catalog_job

    deploy_catalog_job = mock_run.call_args_list[2][0][0]
    assert "animetix-sync-catalog" in deploy_catalog_job
    assert "create" in deploy_catalog_job
    assert "--args=backend/api/manage.py,sync_catalog" in deploy_catalog_job
    assert "--memory=2Gi" in deploy_catalog_job
    assert "--cpu=1" in deploy_catalog_job

    # animetix-maintenance-mlops
    deploy_maintenance_job = mock_run.call_args_list[14][0][0]
    assert "animetix-maintenance-mlops" in deploy_maintenance_job
    assert (
        "--args=backend/api/manage.py,run_scheduled_task,daily-maintenance-mlops"
        in deploy_maintenance_job
    )
    assert "--memory=4Gi" in deploy_maintenance_job
    assert "--cpu=2" in deploy_maintenance_job

    # animetix-generate-drift-baselines: the 9th (last) job, on-demand only
    # (schedule=None). It must be created but never wired up to Cloud Scheduler.
    deploy_drift_job = mock_run.call_args_list[34][0][0]
    assert "animetix-generate-drift-baselines" in deploy_drift_job
    assert "create" in deploy_drift_job

    assert not any(
        "animetix-generate-drift-baselines" in call[0][0] and "scheduler" in call[0][0]
        for call in mock_run.call_args_list
    )

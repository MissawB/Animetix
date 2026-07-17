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

    # Derive the expected count from the config so adding a job doesn't break
    # this test: 1 (enable Scheduler API) + 4 calls per SCHEDULED job (describe
    # + deploy run, describe + deploy scheduler) + 2 per ON-DEMAND job
    # (schedule=="" -> describe + deploy run only, never wired to Scheduler).
    from scripts.deploy.gcp.deploy_jobs import load_config

    jobs = load_config()["gcp_services"]["jobs"]["items"]
    expected_calls = 1 + sum(4 if job.get("schedule") else 2 for job in jobs)
    assert len(mock_run.call_args_list) == expected_calls

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

    # animetix-build-character-index: the 10th job, on-demand only, wiring the
    # phase-2 character-index backfill. Created, never scheduled.
    deploy_char_job = mock_run.call_args_list[36][0][0]
    assert "animetix-build-character-index" in deploy_char_job
    assert "create" in deploy_char_job
    assert (
        "--args=backend/api/manage.py,build_visual_index,--target,character"
        in deploy_char_job
    )
    assert not any(
        "animetix-build-character-index" in call[0][0] and "scheduler" in call[0][0]
        for call in mock_run.call_args_list
    )

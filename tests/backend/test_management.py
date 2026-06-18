import pytest
from django.core.management import call_command, CommandError


def test_run_scheduled_task_invalid_key():
    with pytest.raises(CommandError) as exc_info:
        call_command("run_scheduled_task", "invalid-task-key")
    assert "Unknown task key" in str(exc_info.value)


@pytest.mark.parametrize(
    "task_key,target_patch",
    [
        (
            "dpo-optimization-daily",
            "animetix.tasks.meta_tasks.scheduled_dpo_optimization",
        ),
        (
            "daily-data-ingestion",
            "animetix.tasks.pipeline_tasks.run_daily_ingestion_workflow",
        ),
        (
            "daily-maintenance-mlops",
            "animetix.tasks.pipeline_tasks.run_daily_maintenance_workflow",
        ),
        (
            "hourly-health-monitoring",
            "animetix.tasks.pipeline_tasks.run_hourly_monitoring_workflow",
        ),
        (
            "gold-dataset-lora-sensor",
            "animetix.tasks.pipeline_tasks.check_gold_dataset_sensor_task",
        ),
        (
            "gold-dataset-dpo-sensor",
            "animetix.tasks.pipeline_tasks.check_dpo_feedback_sensor_task",
        ),
    ],
)
def test_run_scheduled_task_success(mocker, task_key, target_patch):
    mock_task = mocker.patch(target_patch)
    mock_task.return_value = "SUCCESS"

    call_command("run_scheduled_task", task_key)
    mock_task.assert_called_once()

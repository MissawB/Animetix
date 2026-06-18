from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Runs a specified periodic/scheduled task synchronously."

    def add_arguments(self, parser):
        parser.add_argument(
            "task_key", type=str, help="The identifier of the scheduled task to run."
        )

    def handle(self, *args, **options):
        # Import dynamically to support clean testing and avoid early import side effects
        from animetix.tasks.meta_tasks import scheduled_dpo_optimization  # noqa: E402
        from animetix.tasks.pipeline_tasks import (  # noqa: E402
            check_dpo_feedback_sensor_task,
            check_gold_dataset_sensor_task,
            run_daily_ingestion_workflow,
            run_daily_maintenance_workflow,
            run_hourly_monitoring_workflow,
        )

        task_mapping = {
            "dpo-optimization-daily": scheduled_dpo_optimization,
            "daily-data-ingestion": run_daily_ingestion_workflow,
            "daily-maintenance-mlops": run_daily_maintenance_workflow,
            "hourly-health-monitoring": run_hourly_monitoring_workflow,
            "gold-dataset-lora-sensor": check_gold_dataset_sensor_task,
            "gold-dataset-dpo-sensor": check_dpo_feedback_sensor_task,
        }

        task_key = options["task_key"]
        if task_key not in task_mapping:
            valid_keys = ", ".join(task_mapping.keys())
            raise CommandError(
                f"Unknown task key '{task_key}'. Valid options are: {valid_keys}"
            )

        self.stdout.write(f"Executing task '{task_key}'...")
        task_func = task_mapping[task_key]
        try:
            result = task_func()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Task '{task_key}' completed successfully. Result: {result}"
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Task '{task_key}' failed with error: {e}")
            )
            raise CommandError(f"Task '{task_key}' execution failed.")

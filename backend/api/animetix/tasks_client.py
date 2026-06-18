import uuid
import json
from django.conf import settings
from django.core.cache import cache
from animetix_project.logging_config import get_logger
from animetix.tasks_registry import get_registered_task

logger = get_logger("animetix." + __name__)


def enqueue_task(task_name, *args, **kwargs):
    task_id = str(uuid.uuid4())

    # Store initial state
    cache.set(
        f"task_result:{task_id}",
        {"ready": False, "result": None, "state": "PENDING"},
        timeout=86400,
    )

    is_prod = getattr(settings, "IS_PRODUCTION", False)

    if not is_prod:
        # Run synchronously in development/test
        logger.info(f"Running task {task_name} eagerly (dev/test environment)")
        task_func = get_registered_task(task_name)
        if not task_func:
            error_msg = f"Task {task_name} not registered in TASK_REGISTRY"
            logger.error(error_msg)
            cache.set(
                f"task_result:{task_id}",
                {"ready": True, "result": {"error": error_msg}, "state": "FAILURE"},
                timeout=86400,
            )
            return task_id

        try:
            res = task_func(*args, **kwargs)
            cache.set(
                f"task_result:{task_id}",
                {"ready": True, "result": res, "state": "SUCCESS"},
                timeout=86400,
            )
        except Exception as e:
            logger.exception(f"Error executing task {task_name} eagerly")
            cache.set(
                f"task_result:{task_id}",
                {"ready": True, "result": {"error": str(e)}, "state": "FAILURE"},
                timeout=86400,
            )
        return task_id

    else:
        # Push to Google Cloud Tasks in production
        from google.cloud import tasks_v2  # noqa: E402

        project = settings.GCP_PROJECT_ID
        queue = settings.GCP_TASKS_QUEUE_NAME
        location = settings.GCP_TASKS_LOCATION
        url = settings.GCP_TASKS_WORKER_URL
        service_account = settings.GCP_TASKS_SERVICE_ACCOUNT

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
        }

        from animetix.telemetry import inject_trace_context  # noqa: E402

        task_headers = {"Content-type": "application/json"}
        inject_trace_context(task_headers)

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": task_headers,
                "body": json.dumps(payload).encode("utf-8"),
                "oidc_token": {
                    "service_account_email": service_account,
                    "audience": url,
                },
            }
        }

        logger.info(f"Enqueuing task {task_name} to Google Cloud Tasks queue {queue}")
        client.create_task(request={"parent": parent, "task": task})
        return task_id

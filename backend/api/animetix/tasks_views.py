import json

from animetix.tasks_client import enqueue_task
from animetix.tasks_registry import get_registered_task
from animetix_project.logging_config import get_logger
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.auth.transport import requests as google_requests

# Eventarc imports
from google.oauth2 import id_token

logger = get_logger("animetix." + __name__)


@csrf_exempt
def run_task_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # OIDC verification in production
    is_prod = getattr(settings, "IS_PRODUCTION", False)
    if is_prod:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Missing or invalid authorization header"}, status=401
            )

        token = auth_header.split(" ")[1]
        try:
            from google.auth.transport import requests  # noqa: E402
            from google.oauth2 import id_token  # noqa: E402

            # Verify the token against Google with STATIC audience
            audience = settings.GCP_TASKS_WORKER_URL
            id_token.verify_oauth2_token(token, requests.Request(), audience=audience)
        except Exception as e:
            logger.error(f"OIDC token verification failed for Cloud Tasks: {e}")
            return JsonResponse({"error": "Invalid OIDC token"}, status=403)

    try:
        data = json.loads(request.body)
        task_id = data.get("task_id")
        task_name = data.get("task_name")
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})
    except Exception as parse_err:
        logger.error(f"Failed to parse task payload: {parse_err}")
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    if not task_id or not task_name:
        return JsonResponse({"error": "task_id and task_name are required"}, status=400)

    task_func = get_registered_task(task_name)
    if not task_func:
        error_msg = f"Task {task_name} is not registered in the system."
        logger.error(error_msg)
        cache.set(
            f"task_result:{task_id}",
            {"ready": True, "result": {"error": error_msg}, "state": "FAILURE"},
            timeout=86400,
        )
        return JsonResponse({"error": error_msg}, status=400)

    logger.info(f"Running task {task_name} (ID: {task_id}) via worker endpoint.")
    cache.set(
        f"task_result:{task_id}",
        {"ready": False, "result": None, "state": "RUNNING"},
        timeout=86400,
    )

    from animetix.telemetry import extract_trace_context  # noqa: E402
    from opentelemetry import trace  # noqa: E402
    from opentelemetry.trace import Status, StatusCode  # noqa: E402

    headers = {k.lower(): v for k, v in request.headers.items()}
    context = extract_trace_context(headers)
    tracer = trace.get_tracer("animetix.tasks.worker")

    with tracer.start_as_current_span(f"Task {task_name}", context=context) as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("task.name", task_name)
        try:
            res = task_func(*args, **kwargs)
            cache.set(
                f"task_result:{task_id}",
                {"ready": True, "result": res, "state": "SUCCESS"},
                timeout=86400,
            )
            span.set_status(Status(StatusCode.OK))
            return JsonResponse({"status": "success", "task_id": task_id})
        except Exception as run_err:
            logger.exception(f"Error running task {task_name} (ID: {task_id})")
            cache.set(
                f"task_result:{task_id}",
                {"ready": True, "result": {"error": str(run_err)}, "state": "FAILURE"},
                timeout=86400,
            )
            span.record_exception(run_err)
            span.set_status(Status(StatusCode.ERROR, description=str(run_err)))
            # Return 500 so Google Cloud Tasks knows to retry
            return JsonResponse({"error": str(run_err)}, status=500)


from adapters.inference.workflows_client import GCPWorkflowsClient  # noqa: E402
from django.http import HttpResponse  # noqa: E402


@csrf_exempt
def poll_workflow_view(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    # Security: Require OIDC token from Cloud Tasks / Scheduler in Prod
    is_prod = getattr(settings, "IS_PRODUCTION", False)
    if is_prod:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Unauthorized"}, status=401)

        token = auth_header.split(" ")[1]
        try:
            # STATIC audience for workflow polling
            audience = settings.GCP_WORKFLOW_POLL_URL
            id_token.verify_oauth2_token(
                token, google_requests.Request(), audience=audience
            )
        except Exception as e:
            logger.error(f"OIDC token verification failed for Workflow Polling: {e}")
            return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body)
        execution_name = data.get("execution_name")
        task_id = data.get("task_id")
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid payload"}, status=400)

    if not execution_name or not task_id:
        return JsonResponse({"error": "Missing execution_name or task_id"}, status=400)

    client = GCPWorkflowsClient()
    status = client.get_execution_status(execution_name)

    state = status.get("state")
    if state == "ACTIVE":
        # Cloud Tasks will retry automatically upon receiving 503
        return HttpResponse("Workflow is still active", status=503)

    elif state == "SUCCEEDED":
        result = status.get("result", {})
        cache.set(
            f"task_result:{task_id}",
            {
                "ready": True,
                "status": "success",
                "result": {
                    "translated_text": result.get("translated_text", ""),
                    "audio_url": result.get("audio_url", ""),
                },
            },
            timeout=3600,
        )
        return JsonResponse({"status": "completed"})

    else:
        # FAILED or CANCELLED
        cache.set(
            f"task_result:{task_id}",
            {
                "ready": True,
                "status": "failed",
                "error": status.get("error", "Workflow execution failed"),
            },
            timeout=3600,
        )
        return JsonResponse({"status": "failed"})


@csrf_exempt
def eventarc_gcs_upload_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    is_prod = getattr(settings, "IS_PRODUCTION", False)
    if is_prod:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Missing or invalid authorization header"}, status=401
            )

        token = auth_header.split(" ")[1]
        try:
            # STATIC audience for Eventarc (No more dynamic build_absolute_uri fallback)
            audience = settings.EVENTARC_RECEIVER_URL
            id_token.verify_oauth2_token(
                token, google_requests.Request(), audience=audience
            )
        except Exception as e:
            logger.error(f"OIDC token verification failed for Eventarc: {e}")
            return JsonResponse({"error": "Invalid OIDC token"}, status=403)

    try:
        body = json.loads(request.body)
    except Exception as e:
        return JsonResponse({"error": f"Invalid JSON body: {e}"}, status=400)

    bucket = body.get("bucket")
    name = body.get("name")

    if not bucket or not name:
        return JsonResponse({"error": "Missing bucket or name in payload"}, status=400)

    # Automate processing if object path indicates raw manga images
    if "manga" in name.lower() and (
        name.lower().endswith(".png")
        or name.lower().endswith(".jpg")
        or name.lower().endswith(".jpeg")
        or name.lower().endswith(".webp")
    ):
        logger.info(
            f"Triggering automated manga processing for GCS upload: gs://{bucket}/{name}"
        )
        try:
            enqueue_task("process_gcs_upload_task", bucket=bucket, name=name)
        except Exception as enqueue_err:
            logger.error(f"Failed to enqueue GCS upload task: {enqueue_err}")
            return JsonResponse(
                {"error": f"Failed to enqueue task: {enqueue_err}"}, status=500
            )

    return JsonResponse({"status": "event processed", "bucket": bucket, "name": name})

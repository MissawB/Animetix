import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from animetix.tasks_registry import get_registered_task
from animetix_project.logging_config import get_logger

logger = get_logger("animetix." + __name__)

@csrf_exempt
def run_task_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    # OIDC verification in production
    is_prod = getattr(settings, 'IS_PRODUCTION', False)
    if is_prod:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Missing or invalid authorization header"}, status=401)
        
        token = auth_header.split(" ")[1]
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests
            # Verify the token against Google
            audience = settings.GCP_TASKS_WORKER_URL
            id_token.verify_oauth2_token(token, requests.Request(), audience=audience)
        except Exception as e:
            logger.error(f"OIDC token verification failed: {e}")
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
        cache.set(f"task_result:{task_id}", {"ready": True, "result": {"error": error_msg}, "state": "FAILURE"}, timeout=86400)
        return JsonResponse({"error": error_msg}, status=400)

    logger.info(f"Running task {task_name} (ID: {task_id}) via worker endpoint.")
    cache.set(f"task_result:{task_id}", {"ready": False, "result": None, "state": "RUNNING"}, timeout=86400)

    from animetix.telemetry import extract_trace_context
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    headers = {k.lower(): v for k, v in request.headers.items()}
    context = extract_trace_context(headers)
    tracer = trace.get_tracer("animetix.tasks.worker")

    with tracer.start_as_current_span(f"Task {task_name}", context=context) as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("task.name", task_name)
        try:
            res = task_func(*args, **kwargs)
            cache.set(f"task_result:{task_id}", {"ready": True, "result": res, "state": "SUCCESS"}, timeout=86400)
            span.set_status(Status(StatusCode.OK))
            return JsonResponse({"status": "success", "task_id": task_id})
        except Exception as run_err:
            logger.exception(f"Error running task {task_name} (ID: {task_id})")
            cache.set(f"task_result:{task_id}", {"ready": True, "result": {"error": str(run_err)}, "state": "FAILURE"}, timeout=86400)
            span.record_exception(run_err)
            span.set_status(Status(StatusCode.ERROR, description=str(run_err)))
            # Return 500 so Google Cloud Tasks knows to retry
            return JsonResponse({"error": str(run_err)}, status=500)


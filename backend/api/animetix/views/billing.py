import base64
import json

from animetix_project.logging_config import get_logger
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from animetix.services import shutdown_brain_service

logger = get_logger("animetix." + __name__)


@csrf_exempt
def billing_alert_webhook(request):
    """
    Webhook triggered by Pub/Sub billing alerts. Scales the animetix-brain
    service to 0 if the budget is reached.
    """
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
            from google.auth.transport import requests  # noqa: E402
            from google.oauth2 import id_token  # noqa: E402

            # Verify token signature against the exact webhook URL audience (STATIC from settings)
            audience = settings.GCP_BILLING_WEBHOOK_URL
            id_token.verify_oauth2_token(token, requests.Request(), audience=audience)
        except Exception as e:
            logger.error(f"OIDC token verification failed for Billing Webhook: {e}")
            return JsonResponse({"error": "Invalid OIDC token"}, status=403)

    try:
        payload = json.loads(request.body)
        message = payload.get("message", {})
        pubsub_data_b64 = message.get("data")
        if not pubsub_data_b64:
            return JsonResponse(
                {"error": "No pubsub data found in message"}, status=400
            )

        decoded_bytes = base64.b64decode(pubsub_data_b64)
        billing_alert = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as parse_err:
        logger.error(f"Failed to parse billing alert payload: {parse_err}")
        return JsonResponse({"error": "Invalid JSON or base64 payload"}, status=400)

    cost_amount = billing_alert.get("costAmount", 0.0)
    budget_amount = billing_alert.get("budgetAmount", 0.0)
    budget_name = billing_alert.get("budgetDisplayName", "unknown")

    logger.info(
        f"Billing Alert received from '{budget_name}': costAmount={cost_amount}, budgetAmount={budget_amount}"
    )

    # Enforce cap if budget is reached or exceeded
    if budget_amount > 0 and cost_amount >= budget_amount:
        logger.warning(
            f"Budget Cap Exceeded ({cost_amount} >= {budget_amount})! Initiating shutdown."
        )
        success, info = shutdown_brain_service()
        if success:
            return JsonResponse({"status": "shutdown_triggered", "info": info})
        else:
            return JsonResponse(
                {"status": "shutdown_failed", "error": info}, status=500
            )

    return JsonResponse(
        {"status": "ignored", "cost": cost_amount, "budget": budget_amount}
    )

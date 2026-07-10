import contextvars
import json
import logging
from typing import Any, Optional

from asgiref.sync import iscoroutinefunction
from dependency_injector.wiring import Provide, inject
from django.core.cache import cache

from .containers import Container

logger = logging.getLogger("animetix.middleware.personalization")

# Namespace unique garanti par le garde backend/__init__.py + ruff TID251
# (voir docs/plans/2026-07-05-unify-import-namespace-design.md) : plus besoin
# de synchroniser les contextvars entre doubles identités du module.
user_id_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "user_id", default=None
)
user_tier_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "user_tier", default="free"
)


def get_current_user_id():
    return user_id_var.get()


def get_current_user_tier():
    return user_tier_var.get()


class UserTrackingMiddleware:
    """
    Middleware that stores the current user ID in context-local storage
    for domain-level observability (e.g. token tracking).
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)

        user_id = request.user.id if request.user.is_authenticated else None
        token = user_id_var.set(user_id)
        try:
            return self.get_response(request)
        finally:
            user_id_var.reset(token)

    async def __acall__(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        token = user_id_var.set(user_id)
        try:
            return await self.get_response(request)
        finally:
            user_id_var.reset(token)


class UserTierMiddleware:
    """
    Middleware that extracts the user's tier from their profile and
    attaches it to the request object as 'user_tier', and stores it in context locals.
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)

        tier = "free"
        if request.user.is_authenticated:
            # Profile is automatically created on user creation via signals
            profile = getattr(request.user, "profile", None)
            tier = getattr(profile, "tier", "free") if profile else "free"
            request.user_tier = tier
        else:
            request.user_tier = "free"

        token = user_tier_var.set(tier)
        try:
            return self.get_response(request)
        finally:
            user_tier_var.reset(token)

    async def __acall__(self, request):
        tier = "free"
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            tier = getattr(profile, "tier", "free") if profile else "free"
            request.user_tier = tier
        else:
            request.user_tier = "free"

        token = user_tier_var.set(tier)
        try:
            return await self.get_response(request)
        finally:
            user_tier_var.reset(token)


class PersonalizationMiddleware:
    """
    Middleware that injects visual personalization metadata into JSON responses.
    """

    sync_capable = True
    async_capable = False

    def __init__(self, get_response):
        self.get_response = get_response

    @inject
    def __call__(
        self, request, drift_service=Provide[Container.core.archetype_drift_service]
    ):
        response = self.get_response(request)

        if (
            response.has_header("Content-Type")
            and "application/json" in response["Content-Type"]
        ):
            if request.user.is_authenticated:
                try:
                    cache_key = f"personalization_drift_user_{request.user.id}"
                    cached_config = cache.get(cache_key)

                    if cached_config is not None:
                        config_dict = cached_config
                    else:
                        profile = getattr(request.user, "profile", None)
                        settings = profile.personalization_settings if profile else {}
                        config = drift_service.calculate_drift(
                            request.user.id, settings
                        )
                        config_dict = config.model_dump()
                        # Cache for 15 minutes (900 seconds)
                        cache.set(cache_key, config_dict, 900)

                    data = json.loads(response.content)
                    if isinstance(data, dict):
                        data["meta"] = data.get("meta", {})
                        data["meta"]["visual_config"] = config_dict
                        response.content = json.dumps(data)
                        # Update Content-Length if present
                        if response.has_header("Content-Length"):
                            response["Content-Length"] = str(len(response.content))
                except Exception as e:
                    logger.error(f"PersonalizationMiddleware error: {e}")
                    pass
        return response


class TracingMiddleware:
    """
    Middleware that wraps incoming HTTP requests in an OpenTelemetry span.
    Propagates trace contexts if headers are present (e.g. from Cloud Tasks).
    """

    sync_capable = True
    async_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        from opentelemetry import trace  # noqa: E402

        self.tracer = trace.get_tracer("animetix.web.request")

    def __call__(self, request):
        from opentelemetry.trace import Status, StatusCode  # noqa: E402

        from animetix.telemetry import extract_trace_context  # noqa: E402

        # Convert request META headers to dictionary for extraction
        headers = {}
        for key, value in request.META.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").lower()
                headers[header_name] = value
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                headers[key.replace("_", "-").lower()] = value

        context = extract_trace_context(headers)
        span_name = f"HTTP {request.method} {request.path}"

        with self.tracer.start_as_current_span(span_name, context=context) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", request.build_absolute_uri())

            try:
                response = self.get_response(request)
                span.set_attribute("http.status_code", response.status_code)
                if response.status_code >= 400:
                    span.set_status(
                        Status(
                            StatusCode.ERROR, description=f"HTTP {response.status_code}"
                        )
                    )
                else:
                    span.set_status(Status(StatusCode.OK))
                return response
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                raise e


class MaintenanceModeMiddleware:
    """Mode maintenance global (flag ``SiteConfiguration.maintenance_mode``).

    Quand le flag est ON, les requêtes ``/api/…`` reçoivent 503
    ``{"maintenance": true}`` pour que le frontend bascule sur la page dédiée.
    Exemptions : l'endpoint de config (le poll de sortie doit passer), le
    monitoring (health checks) et le staff — session admin ou token Firebase.
    Hors ``/api/`` (SPA, statiques, /admin/), rien n'est bloqué : le gating UX
    est fait côté frontend.
    """

    sync_capable = True
    async_capable = True

    EXEMPT_PREFIXES = (
        "/api/v1/config/",
        "/api/monitoring/",
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

    # --- Helpers (sync : appelés via sync_to_async en mode ASGI) ---

    def _guarded(self, request) -> bool:
        path = request.path
        if not path.startswith("/api/"):
            return False
        return not path.startswith(self.EXEMPT_PREFIXES)

    @staticmethod
    def _maintenance_on() -> bool:
        """Fail-open : la maintenance est un état DÉCLARÉ, jamais l'effet de
        bord d'une panne. Base indisponible (tests sans ``django_db``, outage)
        → mode OFF ; les vraies erreurs DB surgiront des vues elles-mêmes.
        """
        from .models import SiteConfiguration

        try:
            return SiteConfiguration.get_solo().maintenance_mode
        except Exception:
            return False

    @staticmethod
    def _is_staff(request) -> bool:
        """Session admin, ou token Firebase d'un compte staff.

        L'authentification DRF n'est tentée que sur le chemin bloquant (mode
        ON + non exempt) : coût nul en fonctionnement normal.
        """
        if getattr(request, "user", None) is not None and request.user.is_staff:
            return True
        try:
            from .auth import GoogleIdentityAuthentication

            result = GoogleIdentityAuthentication().authenticate(request)
            return bool(result and result[0].is_staff)
        except Exception:
            return False

    @staticmethod
    def _blocked_response():
        from django.http import JsonResponse

        return JsonResponse(
            {
                "detail": "Animetix est en maintenance. Réessayez dans quelques instants.",
                "maintenance": True,
            },
            status=503,
        )

    def _should_block(self, request) -> bool:
        return (
            self._guarded(request)
            and self._maintenance_on()
            and not self._is_staff(request)
        )

    # --- Entrées sync / async ---

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)
        if self._should_block(request):
            return self._blocked_response()
        return self.get_response(request)

    async def __acall__(self, request):
        from asgiref.sync import sync_to_async

        if await sync_to_async(self._should_block)(request):
            return self._blocked_response()
        return await self.get_response(request)

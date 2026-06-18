from animetix import api_views
from animetix.api.monitoring import PipelineControlView
from animetix.api.observability import ObservabilityView  # noqa: E402
from animetix.tasks_views import (
    eventarc_gcs_upload_view,  # noqa: E402
    poll_workflow_view,
    run_task_view,
)
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView  # noqa: E402
from rest_framework import routers

# REST Router
router = routers.DefaultRouter()
router.register(r"profiles", api_views.ProfileViewSet, basename="profiles")
router.register(
    r"daily-challenges", api_views.DailyChallengeViewSet, basename="daily-challenges"
)
router.register(r"achievements", api_views.AchievementViewSet, basename="achievements")
router.register(r"fusions", api_views.CreativeFusionViewSet, basename="fusions")
router.register(r"curation", api_views.DataCurationTicketViewSet, basename="curation")


from animetix.api.admin_api import AdEventLoggingAPIView  # noqa: E402
from animetix.api.mlops import AdaptersView, DPOFeedbackLoopView  # noqa: E402
from django.contrib.admin.views.decorators import staff_member_required  # noqa: E402
from django_prometheus import exports as prometheus_exports  # noqa: E402
from drf_spectacular.views import (  # noqa: E402
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("favicon.ico", RedirectView.as_view(url="/static/animetix/img/logo/logo.png")),
    path(
        "i18n/",
        include("django.conf.urls.i18n"),  # noqa: E402
    ),  # Permet le switch de langue via POST
    # --- PROFESSIONNALISATION : API REST (Headless) ---
    path("api/v1/", include(router.urls)),
    path("api/v1/", include("animetix.urls.api")),
    path("api/v1/search/", api_views.MediaSearchView.as_view(), name="api_search"),
    path("api/v1/session/", api_views.GameSessionView.as_view(), name="api_session"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # --- DOCUMENTATION API (Spectacular) - Restreint au Staff ---
    path(
        "api/schema/",
        staff_member_required(SpectacularAPIView.as_view()),
        name="schema",
    ),
    path(
        "api/schema/swagger-ui/",
        staff_member_required(SpectacularSwaggerView.as_view(url_name="schema")),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        staff_member_required(SpectacularRedocView.as_view(url_name="schema")),
        name="redoc",
    ),
    # --- OBSERVABILITÉ : PROMETHEUS - Restreint au Staff ---
    path(
        "metrics/",
        staff_member_required(prometheus_exports.ExportToDjangoView),
        name="prometheus-django-metrics",
    ),
    path("api/observability/", ObservabilityView.as_view(), name="observability"),
    # --- MLOps API (Restricted to Staff) ---
    path(
        "api/mlops/dpo-loop/",
        staff_member_required(DPOFeedbackLoopView.as_view()),
        name="mlops-dpo-loop",
    ),
    path(
        "api/mlops/adapters/",
        staff_member_required(AdaptersView.as_view()),
        name="mlops-adapters",
    ),
    # --- IMAGE PROXY (Global, no i18n) ---
    path("cdn-proxy/", api_views.image_proxy_view, name="cdn_proxy"),
    # --- CLOUD TASKS WORKER VIEW ---
    path(
        "api/tasks/run/",
        include(
            [
                path(
                    "", RedirectView.as_view(url="/"), name="run_task_view_redirect"
                ),  # fallback
            ]
        ),
    ),
    path(
        "api/monitoring/<str:action>/",
        PipelineControlView.as_view(),
        name="pipeline-control",
    ),
    path("api/tasks/run/", run_task_view, name="run_task_view"),
    path("api/tasks/poll-workflow/", poll_workflow_view, name="poll-workflow"),
    path(
        "api/events/gcs-upload/", eventarc_gcs_upload_view, name="eventarc-gcs-upload"
    ),
    # --- BILLING ENDPOINTS ---
    path(
        "billing/log_ad_event/",
        AdEventLoggingAPIView.as_view(),
        name="api_log_ad_event",
    ),
]


# URLs traduites
urlpatterns += i18n_patterns(
    path("", include("animetix.urls")),
)

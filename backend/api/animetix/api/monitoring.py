import logging
import os

from dependency_injector.wiring import Provide, inject
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView

from ..containers import Container

logger = logging.getLogger("animetix.monitoring")


@method_decorator(staff_member_required, name="dispatch")
class PipelineControlView(APIView):
    def post(self, request, action):
        if action == "run_scraper":
            try:
                call_command("run_scrapers")
                return Response({"status": "Scrapers triggered"})
            except Exception:
                logger.exception("Failed to trigger scrapers")
                return Response({"error": "Internal server error"}, status=500)
        elif action == "sync_neo4j":
            try:
                call_command("sync_catalog")
                return Response({"status": "Neo4j sync triggered"})
            except Exception:
                logger.exception("Failed to trigger Neo4j sync")
                return Response({"error": "Internal server error"}, status=500)
        elif action == "run_beam_ingestion":
            try:
                # Trigger the Beam pipeline (lore_ingestion_beam.py)
                # In production, this would use DataflowRunner
                import subprocess  # noqa: E402

                from django.conf import settings  # noqa: E402

                # Check if we should use Dataflow or DirectRunner
                runner = "DirectRunner"
                if not settings.DEBUG:
                    runner = "DataflowRunner"

                # Simple async trigger (using subprocess for simplicity in this staff-only view)
                pipeline_path = os.path.join(
                    settings.PROJECT_ROOT,
                    "backend",
                    "pipeline",
                    "mlops",
                    "lore_ingestion_beam.py",
                )
                cmd = [
                    "python",
                    pipeline_path,
                    f"--runner={runner}",
                    f"--pubsub_subscription=projects/{getattr(settings, 'GCP_PROJECT_ID', 'animetix')}/subscriptions/lore-ingestion-sub",
                    f"--database_url={getattr(settings, 'DATABASE_URL', '')}",
                    f"--django_env={'production' if not settings.DEBUG else 'development'}",
                ]
                subprocess.Popen(cmd)  # nosec B603
                return Response(
                    {"status": f"Beam pipeline ({runner}) triggered in background"}
                )
            except Exception:
                logger.exception("Failed to trigger Beam ingestion")
                return Response({"error": "Internal server error"}, status=500)
        return Response({"error": "Invalid action"}, status=400)


@method_decorator(staff_member_required, name="dispatch")
class ClusterHealthView(APIView):
    """
    GET /api/monitoring/cluster-health/
    Returns real-time health status for all cluster components:
    NVIDIA H100 GPUs, Ollama Inference, Neo4j Knowledge Graph.
    """

    @inject
    def __init__(
        self,
        health_service=Provide[Container.core.health_dashboard_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.health_service = health_service

    def get(self, request):
        try:
            data = self.health_service.get_cluster_health()
            return Response(data)
        except Exception:
            logger.exception("Cluster health check failed")
            return Response(
                {"error": "Cluster health check failed"},
                status=500,
            )

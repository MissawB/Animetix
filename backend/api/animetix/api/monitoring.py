import os

from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView


@method_decorator(staff_member_required, name="dispatch")
class PipelineControlView(APIView):
    def post(self, request, action):
        if action == "run_scraper":
            try:
                call_command("run_scrapers")
                return Response({"status": "Scrapers triggered"})
            except Exception as e:
                return Response({"error": str(e)}, status=500)
        elif action == "sync_neo4j":
            try:
                call_command("sync_catalog")
                return Response({"status": "Neo4j sync triggered"})
            except Exception as e:
                return Response({"error": str(e)}, status=500)
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
            except Exception as e:
                return Response({"error": str(e)}, status=500)
        return Response({"error": "Invalid action"}, status=400)


@method_decorator(staff_member_required, name="dispatch")
class ClusterHealthView(APIView):
    """
    GET /api/monitoring/cluster-health/
    Returns real-time health status for all cluster components:
    NVIDIA H100 GPUs, Ollama Inference, Neo4j Knowledge Graph.
    """

    def get(self, request):
        from dependency_injector.wiring import Provide

        from animetix.containers.main import ApplicationContainer

        try:
            container = ApplicationContainer()
            health_service = container.core_services.health_dashboard_service()
            data = health_service.get_cluster_health()
            return Response(data)
        except Exception as e:
            return Response(
                {"error": f"Cluster health check failed: {str(e)}"},
                status=500,
            )


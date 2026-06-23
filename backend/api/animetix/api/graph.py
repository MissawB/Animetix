import logging

from core.ports.graph_persistence_port import GraphPersistencePort
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..containers import Container

logger = logging.getLogger("animetix.graph")


class GraphNeighborsView(APIView):
    """
    API view to retrieve neighbors of a media item in the knowledge graph.
    Available to all authenticated users (costs Berrix per exploration).
    """

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        graph_manager: GraphPersistencePort = Provide[
            Container.persistence.graph_persistence_port
        ],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.graph_manager = graph_manager

    def get(self, request):
        # Déduction des Bx (10 Bx pour exploration de graphe profonde)
        from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

        from animetix.api.billing import deduct_berrix  # noqa: E402

        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["graph_exploration"],
            "Exploration du Knowledge Graph",
        )

        item_id = request.query_params.get("id")
        media_type = request.query_params.get("type")
        depth_str = request.query_params.get("depth", "1")

        if not item_id or not media_type:
            return Response(
                {"error": "Query parameters 'id' and 'type' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            depth = int(depth_str)
        except ValueError:
            return Response(
                {"error": "'depth' must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = self.graph_manager.get_neighborhood(item_id, media_type, depth)
            return Response(data)
        except Exception:
            logger.exception("Failed to retrieve graph data")
            return Response(
                {"error": "Failed to retrieve graph data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GraphWorldMapView(APIView):
    """
    Vue macroscopique du Knowledge Graph.
    Expose les communautés sémantiques (Leiden/Louvain) et leurs résumés.
    """

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(
        self, partitioner=Provide[Container.agentic.community_partitioner], **kwargs
    ):
        super().__init__(**kwargs)
        self.partitioner = partitioner

    def get(self, request):
        communities = self.partitioner.run_partitioning()
        return Response(communities)


class GraphDebuggerView(APIView):
    """
    Interface avancée pour le GraphHealerService.
    Permet de visualiser et corriger les conflits de lore.
    """

    permission_classes = [permissions.IsAdminUser]

    @inject
    def __init__(self, healer=Provide[Container.core.graph_healer_service], **kwargs):
        super().__init__(**kwargs)
        self.healer = healer

    def get(self, request):
        audit = self.healer.audit_graph_quality()
        return Response(audit)

    def post(self, request):
        action = request.data.get("action")
        media_id = request.data.get("media_id")

        if action == "cleanup":
            self.healer.check_and_fix_broken_relations()
            return Response(
                {"status": "success", "message": "Global cleanup cycle executed."}
            )

        if action == "merge_duplicates":
            merged = self.healer.merge_duplicate_entities()
            return Response(
                {"status": "success", "message": f"Merged {merged} duplicate entities."}
            )

        if action == "heal" and media_id:
            self.healer.heal_node(media_id)
            return Response(
                {"status": "success", "message": f"Node {media_id} healed."}
            )

        return Response({"error": "Invalid action or missing media_id"}, status=400)

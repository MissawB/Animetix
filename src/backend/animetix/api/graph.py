from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from dependency_injector.wiring import inject, Provide
from core.ports.graph_persistence_port import GraphPersistencePort
from ..containers import Container

class GraphNeighborsView(APIView):
    """
    API view to retrieve neighbors of a media item in the knowledge graph.
    Only available to Premium users.
    """
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(self, graph_manager: GraphPersistencePort = Provide[Container.graph_persistence_port], **kwargs):
        super().__init__(**kwargs)
        self.graph_manager = graph_manager

    def get(self, request):
        # Check premium tier
        if getattr(request, 'user_tier', 'free') != 'premium':
            return Response(
                {"error": "Localized Graph Visualizer is a Premium feature."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        item_id = request.query_params.get('id')
        media_type = request.query_params.get('type')
        depth_str = request.query_params.get('depth', '1')

        if not item_id or not media_type:
            return Response(
                {"error": "Query parameters 'id' and 'type' are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            depth = int(depth_str)
        except ValueError:
            return Response(
                {"error": "'depth' must be an integer."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = self.graph_manager.get_neighborhood(item_id, media_type, depth)
            return Response(data)
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve graph data: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

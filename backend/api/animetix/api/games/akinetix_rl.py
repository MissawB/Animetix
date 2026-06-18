from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ...containers import Container
from animetix.api.dependencies import get_session_service
from core.ports.usage_port import UsagePort

# --- AKINETIX RL (EXPERT MODE) ---


class AkinetixRLStateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def get(
        self, request, akinetix_expert_service=Provide[Container.core.akinetix_service]
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_expert_service.get_state(port)
        if not state.current_q:
            return Response(
                {"error": "No RL session in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(state.model_dump() if hasattr(state, "model_dump") else state)


class AkinetixRLStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_expert_service=Provide[Container.core.akinetix_service],
        usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
    ):
        session_service = get_session_service(request)
        port = session_service.port

        # Quota Check
        tier = getattr(request, "user_tier", "free")
        if not usage_port.check_quota(request.user.id, tier):
            return Response(
                {"error": "Daily AI quota exceeded."}, status=status.HTTP_403_FORBIDDEN
            )

        media_type = request.data.get("media_type", port.get("media_type", "Anime"))
        port.set("media_type", media_type)

        catalog = catalog_service.load_data(media_type)
        if not catalog:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        state = akinetix_expert_service.start_new_game(catalog["db"])
        akinetix_expert_service.save_state(port, state)

        # Log usage (simulations are expensive)
        usage_port.log_usage(
            engine="akinetix-rl-agent", units=10, user_id=request.user.id
        )

        return Response(state.model_dump() if hasattr(state, "model_dump") else state)


class AkinetixRLAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        akinetix_expert_service=Provide[Container.core.akinetix_service],
        usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
    ):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_expert_service.get_state(port)
        if not state.current_q:
            return Response(
                {"error": "No RL session in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Quota Check
        tier = getattr(request, "user_tier", "free")
        if not usage_port.check_quota(request.user.id, tier):
            return Response(
                {"error": "Daily AI quota exceeded."}, status=status.HTTP_403_FORBIDDEN
            )

        answer = request.data.get("answer")
        media_type = port.get("media_type", "Anime")

        catalog = catalog_service.load_data(media_type)
        if not catalog:
            return Response(
                {"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND
            )

        new_state = akinetix_expert_service.process_answer(catalog["db"], state, answer)
        akinetix_expert_service.save_state(port, new_state)

        # Log usage
        usage_port.log_usage(
            engine="akinetix-rl-agent", units=5, user_id=request.user.id
        )

        return Response(
            new_state.model_dump() if hasattr(new_state, "model_dump") else new_state
        )

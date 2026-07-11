import logging
import secrets

from adapters.persistence.django_usage_adapter import DjangoUsageAdapter
from asgiref.sync import async_to_sync
from dependency_injector.wiring import Provide, inject
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.auth import DeveloperApiKeyAuthentication

from ..containers import Container

logger = logging.getLogger("animetix.api.developer")


async def _collect_rag_events(agent, query: str, media_type: str, user_id: str):
    """Drain the async RAG stream into a list (this endpoint is one-shot: it
    only returns the final answer, so nothing is lost by not streaming)."""
    return [
        event
        async for event in agent.aplan_and_solve_stream(
            query, media_type, user_id=user_id
        )
    ]


class DeveloperRAGView(APIView):
    """
    Developer B2B API endpoint to query the Animetix RAG engine.
    Requires authentication via X-API-Key header.
    """

    authentication_classes = [DeveloperApiKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @inject
    def __init__(
        self,
        agentic_rag=Provide[Container.agentic.agentic_rag],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.agentic_rag = agentic_rag

    def post(self, request):
        query = request.data.get("query")
        media_type = request.data.get("media_type", "Anime")

        if not query:
            return Response({"error": "No query provided"}, status=400)

        user_id = str(request.user.id)
        try:
            agent = self.agentic_rag

            # Run the agentic RAG stream internally (single async implementation)
            events = async_to_sync(_collect_rag_events)(
                agent, query, media_type, user_id
            )

            # Find the final result event
            final_answer = ""
            for event in events:
                if event.get("type") == "result":
                    final_answer = event.get("content", "")
                    break

            # Fallback if no result event was explicitly emitted
            if not final_answer and events:
                for event in reversed(events):
                    if event.get("type") not in ("error", "status"):
                        final_answer = event.get("content", "")
                        break

            # 1. Log usage (Pro tier is free/manual — no external billing report)
            usage_adapter = DjangoUsageAdapter()
            usage_adapter.log_usage(
                engine="agentic_rag", units=1, user_id=request.user.id
            )

            return Response(
                {
                    "query": query,
                    "media_type": media_type,
                    "answer": final_answer,
                    "status": "success",
                }
            )

        except Exception:
            logger.exception("Error in DeveloperRAGView:")
            return Response({"error": "Internal server error"}, status=500)


class DeveloperApiKeyView(APIView):
    """
    API endpoint for developers to view API key metadata and generate/regenerate keys.
    Requires session authentication (browser logged-in user).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        has_key = bool(profile.api_key_hash)

        return Response(
            {
                "tier": profile.tier,
                "has_api_key": has_key,
                "api_key_prefix": "ax_pro_" if has_key else None,
            }
        )

    def post(self, request):
        profile = request.user.profile

        if profile.tier != "pro":
            return Response(
                {"error": "API Key generation is restricted to Pro tier developers."},
                status=403,
            )

        # Generate a new raw key: ax_pro_<profile_id>_<secret>
        secret_token = secrets.token_hex(24)
        raw_key = f"ax_pro_{profile.id}_{secret_token}"

        # Save hashed key
        profile.set_api_key(raw_key)
        profile.save()

        # Return the raw key to the user (ONLY ONCE)
        return Response(
            {
                "api_key": raw_key,
                "warning": "Please copy this API key now. You will not be able to see it again!",
            },
            status=201,
        )


class DeveloperSubscriptionMockView(APIView):
    """Active le tier Pro (gratuit/manuel — plus de facturation Stripe)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        profile.tier = "pro"
        profile.save(update_fields=["tier"])
        return Response({"status": "subscribed", "tier": profile.tier})

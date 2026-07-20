import random

from animetix_project.logging_config import get_logger
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from animetix.api.dependencies import get_session_service

from ...containers import Container
from ...models import CreativeFusion
from .base import CpuGameAPIView

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402

from ...serializers import ArchetypistFusionSerializer  # noqa: E402

# ... (rest of imports unchanged)


# --- ARCHETYPIST / CREATIVE FUSION ---


class ArchetypistStartFusionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def post(
        self,
        request,
        catalog_service=Provide[Container.core.catalog_service],
        guardrail_service: GuardrailService = Provide[Container.core.guardrail_service],
        usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
    ):

        serializer = ArchetypistFusionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Déduction des Bx (50 Bx pour marge minimale)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["creative_fusion"],
            "Forge de Creative Fusion",
        )

        data = serializer.validated_data
        session_service = get_session_service(request)
        port = session_service.port
        media_type = port.get("media_type", "Anime")

        title_A = data.get("title_A")
        title_B = data.get("title_B")
        media_A = data.get("media_type_A", media_type)
        media_B = data.get("media_type_B", media_type)

        chaos_level = data.get("chaos_level")
        universe_balance = data.get("universe_balance")
        art_style = data.get("art_style")
        parent_id = data.get("parent_id")

        # 1. Guardrail Check on Art Style and Titles
        check_text = f"Titles: {title_A or ''} x {title_B or ''}. Style: {art_style}"
        guard_input = guardrail_service.validate_input(check_text)
        if not guard_input.get("is_safe", True):
            return Response(
                {"error": f"Security violation: {guard_input.get('reason')}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_cat = catalog_service.load_data(media_type)
        data_A = (
            catalog_service.load_data(media_A) if media_A != media_type else data_cat
        )
        data_B = (
            catalog_service.load_data(media_B) if media_B != media_type else data_cat
        )

        if not data_A or not data_B:
            return Response(
                {"error": "Catalog data missing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        valid_A = [
            t
            for t in data_A.get("titles", [])
            if t in data_A.get("title_to_full_data", {})
        ]
        valid_B = [
            t
            for t in data_B.get("titles", [])
            if t in data_B.get("title_to_full_data", {})
        ]

        t1 = title_A if title_A else random.choice(valid_A[:500])  # nosec B311
        t2 = title_B if title_B else random.choice(valid_B[:500])  # nosec B311

        item1 = data_A["title_to_full_data"].get(t1)
        item2 = data_B["title_to_full_data"].get(t2)

        if not item1 or not item2:
            return Response(
                {"error": "Items not found"}, status=status.HTTP_404_NOT_FOUND
            )

        parent_fusion = None
        if parent_id:
            try:
                parent_fusion = CreativeFusion.objects.get(id=parent_id)
            except (CreativeFusion.DoesNotExist, ValueError) as e:
                logger.warning(f"Handled error in ArchetypistStartFusionView: {e}")

        fusion = CreativeFusion.objects.create(
            title_a=t1,
            title_b=t2,
            media_type_a=media_A,
            media_type_b=media_B,
            chaos_level=chaos_level,
            universe_balance=universe_balance,
            art_style=art_style,
            creator=request.user if request.user.is_authenticated else None,
            parent=parent_fusion,
            scenario_text="Génération en cours...",
        )
        from animetix.tasks_client import enqueue_task  # noqa: E402

        language = port.get("language", "Français")

        task_id = enqueue_task(
            "generate_fusion_flow_task",
            media_type,
            item1,
            item2,
            language,
            chaos_level=chaos_level,
            universe_balance=universe_balance,
            art_style=art_style,
        )

        # Log Usage (Heavy task trigger)
        usage_port.log_usage(
            engine="archetypist-fusion-engine", units=30, user_id=request.user.id
        )

        return Response(
            {
                "fusion_id": fusion.id,
                "task_id": task_id,
                "title_a": t1,
                "title_b": t2,
                "item_a_image": item1.get("image"),
                "item_b_image": item2.get("image"),
            }
        )


class ArchetypistTaskStatusView(CpuGameAPIView):
    def get(self, request):
        task_id = request.query_params.get("task_id")
        fusion_id = request.query_params.get("fusion_id")

        if not task_id or not fusion_id:
            return Response(
                {"error": "task_id and fusion_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.core.cache import cache  # noqa: E402

        task_data = cache.get(f"task_result:{task_id}")

        status_msg = "En cours..."
        state = "PENDING"
        ready = False
        result = None

        if task_data:
            state = task_data.get("state", "PENDING")
            ready = task_data.get("ready", False)
            result = task_data.get("result")
            if state == "PENDING":
                status_msg = "En attente de traitement..."
            elif state == "FAILURE":
                status_msg = "Erreur de traitement"
                if isinstance(result, dict) and "error" in result:
                    status_msg = result["error"]

        response_data = {"state": state, "status": status_msg}

        if ready:
            try:
                fusion = CreativeFusion.objects.get(id=fusion_id)

                # Enregistrement des résultats de la tâche asynchrone dans la BDD
                if (
                    fusion.scenario_text == "Génération en cours..."
                    or not fusion.image_url
                ):
                    if isinstance(result, dict):
                        scenario = result.get("scenario") or result.get(
                            "content", {}
                        ).get("scenario")
                        image_url_val = result.get("fusion_image") or result.get(
                            "image_url"
                        )

                        if scenario:
                            fusion.scenario_text = scenario

                        if image_url_val:
                            if image_url_val.startswith("data:image/"):
                                try:
                                    import base64  # noqa: E402
                                    import time  # noqa: E402

                                    from django.core.files.base import (  # noqa: E402
                                        ContentFile,
                                    )
                                    from django.core.files.storage import (  # noqa: E402
                                        default_storage,
                                    )

                                    header, base64_data = image_url_val.split(
                                        ";base64,"
                                    )
                                    ext = header.split("/")[-1]
                                    image_bytes = base64.b64decode(base64_data)

                                    file_name = f"fusions/fusion_{fusion_id}_{int(time.time())}.{ext}"
                                    saved_path = default_storage.save(
                                        file_name, ContentFile(image_bytes)
                                    )
                                    fusion.image_url = default_storage.url(saved_path)
                                except Exception as upload_err:
                                    logger.error(
                                        f"Failed to upload fusion image to storage: {upload_err}"
                                    )
                                    fusion.image_url = image_url_val[:500]
                            else:
                                fusion.image_url = image_url_val

                        fusion.save()

                response_data["scenario"] = fusion.scenario_text
                response_data["image_url"] = fusion.image_url
                response_data["completed"] = True
            except CreativeFusion.DoesNotExist:
                return Response(
                    {"error": "Fusion not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            response_data["completed"] = False

        return Response(response_data)

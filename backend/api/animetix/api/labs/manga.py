"""Manga labs: cleaning, translation and GCP-orchestrated dubbing."""

import base64

from adapters.inference.workflows_client import GCPWorkflowsClient
from animetix_project.logging_config import get_logger
from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ...containers import get_container  # noqa: E402

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402


class MangaLabDataView(APIView):
    """Metadata for the Manga Lab tools."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "active",
                "tools": [
                    {
                        "id": "clean",
                        "name": "Manga Cleaner",
                        "description": "Remove text bubbles from manga pages.",
                        "endpoint": "/api/v1/labs/manga-lab/clean/",
                    },
                    {
                        "id": "translate",
                        "name": "Manga Translator",
                        "description": "Translate manga bubbles to target language.",
                        "endpoint": "/api/v1/labs/manga-lab/translate/",
                    },
                    {
                        "id": "voice",
                        "name": "Manga Voice Lab",
                        "description": "Generate voices for manga characters (Dubbing).",
                        "endpoint": "/api/v1/labs/manga-voice/",
                    },
                ],
            }
        )


@method_decorator(
    ratelimit(key="user_or_ip", rate="5/m", method="POST", block=True), name="dispatch"
)
class MangaVoiceLabView(APIView):
    """Traduction de manga + synthèse vocale orchestrée via GCP Workflows."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "gpu"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        import uuid  # noqa: E402

        from django.core.cache import cache  # noqa: E402

        image = request.data.get("image")
        reference_audio = request.data.get("reference_audio")
        target_lang = request.data.get("target_lang", "French")

        if not image or not reference_audio:
            return Response(
                {"error": "Missing image or reference_audio in payload"}, status=400
            )

        # Déduction des Berrix (200 Bx pour orchestration GCP + Audio)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["manga_voice"],
            "Manga Voice Lab (Doublage IA)",
        )

        task_id = str(uuid.uuid4())
        filename = f"manga_voice_{task_id}.wav"

        # Initialisation du cache
        cache.set(
            f"task_result:{task_id}",
            {"ready": False, "status": "pending"},
            timeout=3600,
        )

        is_prod = getattr(settings, "IS_PRODUCTION", False)
        if is_prod:
            try:
                client = GCPWorkflowsClient()
                execution_name = client.trigger_pipeline(
                    image, reference_audio, target_lang, filename
                )

                # Cloud Task pour le polling
                client.enqueue_polling_task(execution_name, task_id)
                return Response({"task_id": task_id}, status=202)
            except Exception as e:
                cache.set(
                    f"task_result:{task_id}",
                    {"ready": True, "status": "failed", "error": str(e)},
                    timeout=3600,
                )
                logger.exception("Failed to start workflow")
                return Response({"error": "Failed to start workflow"}, status=500)
        else:
            # Fallback local dev synchrone simulé
            cache.set(
                f"task_result:{task_id}",
                {
                    "ready": True,
                    "status": "success",
                    "result": {
                        "translated_text": "[Local Dev Fallback] Traduction simulée.",
                        "audio_url": f"http://localhost:8000/media/mock_{filename}",
                    },
                },
                timeout=3600,
            )
            return Response({"task_id": task_id}, status=202)


class MangaCleanLabView(APIView):
    """Nettoie (inpaint) les bulles de texte d'une planche de manga."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get("image")

        if not image_file:
            return Response({"error": "Image file is required."}, status=400)

        # Déduction des Berrix (20 Bx pour inpainting de planche)
        deduct_berrix(
            request.user, FEATURE_BX_COSTS["manga_clean"], "Manga Cleaner (Planche)"
        )

        try:
            image_bytes = image_file.read()
            inference_engine = container.inference.inference_engine()

            # Un nettoyage simple équivaut à un inpainting avec une liste de bulles vide.
            cleaned_bytes = inference_engine.inpaint_text_bubbles(image_bytes, [])

            b64_img = base64.b64encode(cleaned_bytes).decode("utf-8")
            return Response({"status": "success", "image": b64_img})
        except Exception:
            logger.exception("Error in MangaCleanLabView")
            return Response({"error": "Internal server error"}, status=500)


class MangaTranslateLabView(APIView):
    """Traduit les bulles de texte d'une planche de manga."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        image_file = request.FILES.get("image")
        target_lang = request.data.get("target_lang", "French")

        if not image_file:
            return Response({"error": "Image file is required."}, status=400)

        # Déduction des Berrix (20 Bx pour inpainting + traduction)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["manga_translate"],
            f"Manga Translator: {target_lang}",
        )

        try:
            image_bytes = image_file.read()
            manga_flow_service = container.core.manga_flow_service()

            translated_bytes = manga_flow_service.translate_manga_page(
                image_bytes, target_lang
            )

            b64_img = base64.b64encode(translated_bytes).decode("utf-8")
            return Response({"status": "success", "image": b64_img})
        except Exception:
            logger.exception("Error in MangaTranslateLabView")
            return Response({"error": "Internal server error"}, status=500)

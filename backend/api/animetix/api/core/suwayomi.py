"""Suwayomi/Tachidesk (Mihon) integration: proxy, sources, search, import, extensions."""

import base64

from animetix_project.logging_config import get_logger
from core.utils.security import safe_http_request
from dependency_injector.wiring import Provide, inject
from django.http import HttpResponse  # noqa: E402
from django_ratelimit.decorators import ratelimit  # noqa: E402
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...containers import Container, get_container

logger = get_logger("animetix.api")


@ratelimit(key="ip", rate="120/m", method="GET", block=True)
def suwayomi_image_proxy(request):
    """
    Proxy pour les images de Suwayomi/Tachidesk afin de contourner le CORS et l'authentification.
    """
    from core.config import settings

    encoded_url = request.GET.get("page_url")
    if not encoded_url:
        return HttpResponse("Missing page_url", status=400)
    try:
        url = base64.b64decode(encoded_url).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decode Suwayomi proxy URL: {e}")
        return HttpResponse("Invalid encoded URL", status=400)

    suwayomi_base = settings.SUWAYOMI_URL.rstrip("/")
    if not url.startswith("http"):
        url = f"{suwayomi_base}/{url.lstrip('/')}"
    else:
        if not url.startswith(suwayomi_base):
            logger.warning(
                f"Blocked unauthorized external URL in Suwayomi proxy: {url}"
            )
            return HttpResponse(
                "Forbidden: URL must point to the configured Suwayomi instance",
                status=403,
            )

    headers = {}
    if settings.SUWAYOMI_PASSWORD:
        headers["Authorization"] = f"Bearer {settings.SUWAYOMI_PASSWORD}"

    try:
        response = safe_http_request("GET", url, headers=headers, timeout=15)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "image/jpeg")
            return HttpResponse(response.content, content_type=content_type)
        else:
            logger.error(
                f"Suwayomi proxy failed with status {response.status_code} for URL: {url}"
            )
            return HttpResponse(status=response.status_code)
    except Exception as e:
        logger.error(f"Error proxying Suwayomi image {url}: {e}", exc_info=True)
        return HttpResponse(status=500)


class SuwayomiSourcesView(APIView):
    """Liste des sources de mangas installées dans Suwayomi."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def get(self, request):
        if not self.suwayomi_adapter:
            return Response(
                {"error": "Suwayomi integration not configured"}, status=500
            )
        sources = self.suwayomi_adapter.get_sources()
        return Response(sources)


class SuwayomiSearchView(APIView):
    """Recherche des mangas dans une source spécifique Suwayomi."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def get(self, request):
        source_id = request.query_params.get("source_id")
        query = request.query_params.get("q", "")
        if not source_id:
            return Response({"error": "Missing source_id parameter"}, status=400)
        if not self.suwayomi_adapter:
            return Response(
                {"error": "Suwayomi integration not configured"}, status=500
            )
        results = self.suwayomi_adapter.search_manga(source_id, query)
        return Response(results)


class SuwayomiImportView(APIView):
    """Importe un manga depuis Suwayomi dans le catalogue local."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def post(self, request):
        from ...models import MediaItem

        source_id = request.data.get("source_id")
        suwayomi_manga_id = request.data.get("suwayomi_manga_id")

        if not source_id or not suwayomi_manga_id:
            return Response(
                {"error": "Missing source_id or suwayomi_manga_id"}, status=400
            )

        if not self.suwayomi_adapter:
            return Response(
                {"error": "Suwayomi integration not configured"}, status=500
            )

        manga_details = self.suwayomi_adapter.get_manga_details(suwayomi_manga_id)
        if not manga_details:
            return Response(
                {"error": "Failed to fetch manga details from Suwayomi"}, status=404
            )

        external_id = f"suwayomi:{source_id}:{suwayomi_manga_id}"

        thumbnail_url = manga_details.get("thumbnailUrl")
        image_url = None
        if thumbnail_url:
            encoded_thumb = base64.b64encode(thumbnail_url.encode("utf-8")).decode(
                "utf-8"
            )
            image_url = f"/api/v1/media/Manga/suwayomi-image/?page_url={encoded_thumb}"

        media_item, created = MediaItem.objects.update_or_create(
            external_id=external_id,
            media_type="Manga",
            defaults={
                "title": manga_details.get("title", "Unknown Title"),
                "description": manga_details.get("description", ""),
                "synopsis_en": manga_details.get("description", ""),
                "image_url": image_url,
                "metadata": {
                    "source_id": source_id,
                    "suwayomi_id": suwayomi_manga_id,
                    "author": manga_details.get("author", ""),
                    "artist": manga_details.get("artist", ""),
                    "status": manga_details.get("status", ""),
                },
            },
        )

        container = get_container()
        manga_service = container.core.manga_service()
        manga_service.get_chapters(external_id)

        return Response(
            {
                "success": True,
                "media_item": {
                    "id": media_item.id,
                    "external_id": media_item.external_id,
                    "title": media_item.title,
                    "image_url": media_item.image_url,
                },
            }
        )


class SuwayomiExtensionsListView(APIView):
    """Liste des extensions installées et disponibles dans Suwayomi/Mihon.

    Lecture seule sur une page publique (/explore/tachidesk/) : accessible en
    anonyme comme les sources et la recherche. Les actions (installation /
    mise à jour) et l'import restent réservés aux utilisateurs authentifiés.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def get(self, request):
        if not self.suwayomi_adapter:
            return Response(
                {"error": "Suwayomi integration not configured"}, status=500
            )
        try:
            extensions = self.suwayomi_adapter.get_extensions()
            return Response(extensions)
        except Exception:
            logger.exception("Failed to fetch Suwayomi extensions")
            return Response({"error": "Internal server error"}, status=500)


class SuwayomiExtensionsActionView(APIView):
    """Effectue une action (installation, désinstallation, mise à jour) sur une extension Suwayomi."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def post(self, request):
        ids = request.data.get("ids")
        action = request.data.get("action")

        if not ids or not isinstance(ids, list) or not action:
            return Response(
                {
                    "error": "Missing or invalid parameters: 'ids' (list) and 'action' (string)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in ["install", "uninstall", "update"]:
            return Response(
                {
                    "error": "Invalid action. Must be 'install', 'uninstall', or 'update'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not self.suwayomi_adapter:
            return Response(
                {"error": "Suwayomi integration not configured"}, status=500
            )

        try:
            results = self.suwayomi_adapter.update_extensions(ids, action)
            return Response(results)
        except Exception:
            logger.exception("Failed to update Suwayomi extensions")
            return Response({"error": "Internal server error"}, status=500)

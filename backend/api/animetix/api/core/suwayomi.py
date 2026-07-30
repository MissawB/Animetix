"""Suwayomi/Tachidesk (Mihon) integration: proxy, sources, search, import, extensions."""

import base64

from adapters.persistence.suwayomi_adapter import SuwayomiUnavailableError
from animetix_project.logging_config import get_logger
from core.utils.security import safe_http_request
from dependency_injector.wiring import Provide, inject
from django.core.cache import cache  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django_ratelimit.decorators import ratelimit  # noqa: E402
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...containers import Container

logger = get_logger("animetix.api")

SUWAYOMI_UNREACHABLE_MSG = (
    "Serveur Suwayomi injoignable. Démarre Suwayomi-Server sur "
    "http://127.0.0.1:4567 (valeur de SUWAYOMI_URL), puis réessaie."
)


def _suwayomi_unreachable_response():
    """Réponse 503 explicite : le serveur Suwayomi n'est pas joignable (au lieu
    d'une liste vide muette qui laisse croire qu'il n'y a rien à afficher)."""
    return Response(
        {"error": "suwayomi_unreachable", "message": SUWAYOMI_UNREACHABLE_MSG},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


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
        # allow_internal=True : Suwayomi tourne en local (127.0.0.1:4567) ; sans ça
        # le garde-fou SSRF bloque l'URL et le proxy renvoie 500 -> aucune image.
        # L'URL est déjà validée ci-dessus comme pointant vers l'instance Suwayomi.
        response = safe_http_request(
            "GET", url, headers=headers, timeout=15, allow_internal=True
        )
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
        try:
            sources = self.suwayomi_adapter.get_sources()
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
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
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        if not source_id:
            return Response({"error": "Missing source_id parameter"}, status=400)
        if not self.suwayomi_adapter:
            return Response(
                {"error": "Suwayomi integration not configured"}, status=500
            )
        try:
            results = self.suwayomi_adapter.search_manga(source_id, query, page)
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
        # {"mangas": [...], "hasNextPage": bool} — le front pagine dessus.
        return Response(results)


def _cached_last_page(adapter, source_id, query):
    """Numéro de dernière page (mis en cache 10 min : le seek coûte ~10 requêtes,
    et le catalogue « populaire » d'une source ne bouge que lentement)."""
    cache_key = f"suwayomi:lastpage:{source_id}:{query}"
    last_page = cache.get(cache_key)
    if last_page is None:
        last_page = adapter.find_last_page(source_id, query)
        cache.set(cache_key, last_page, 600)
    return last_page


class SuwayomiLastPageView(APIView):
    """Numéro de la dernière page du catalogue d'une source (permet « aller à la
    fin » et de borner le saut de page côté UI)."""

    permission_classes = [permissions.AllowAny]

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
        try:
            last_page = _cached_last_page(self.suwayomi_adapter, source_id, query)
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
        return Response({"lastPage": last_page})


class SuwayomiSeekLetterView(APIView):
    """Page où commence une lettre donnée (le catalogue Suwayomi est trié
    alphabétiquement) — pour naviguer par ordre alphabétique."""

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def get(self, request):
        source_id = request.query_params.get("source_id")
        query = request.query_params.get("q", "")
        letter = request.query_params.get("letter", "")
        if not source_id or not letter:
            return Response(
                {"error": "Missing source_id or letter parameter"}, status=400
            )
        try:
            last_page = _cached_last_page(self.suwayomi_adapter, source_id, query)
            page = self.suwayomi_adapter.find_page_for_letter(
                source_id, query, letter, last_page
            )
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
        return Response({"page": page, "lastPage": last_page})


class SuwayomiMangaDetailsView(APIView):
    """Fiche complète d'un manga source (titre, description, auteur, genres,
    statut) — pour la popup de détail. Lecture seule, publique."""

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def get(self, request):
        manga_id = request.query_params.get("suwayomi_manga_id")
        if not manga_id:
            return Response(
                {"error": "Missing suwayomi_manga_id parameter"}, status=400
            )
        try:
            details = self.suwayomi_adapter.fetch_manga_details(manga_id)
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
        return Response(details)


class SuwayomiMangaChaptersView(APIView):
    """Chapitres d'un manga source, lus DIRECTEMENT depuis Suwayomi (pour la
    popup). Découplé de l'import : on n'importe le manga dans le catalogue local
    qu'au moment de la lecture. Lecture seule, publique."""

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(
        self, suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter], **kwargs
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter

    def get(self, request):
        manga_id = request.query_params.get("suwayomi_manga_id")
        if not manga_id:
            return Response(
                {"error": "Missing suwayomi_manga_id parameter"}, status=400
            )
        try:
            chapters = self.suwayomi_adapter.get_chapters(manga_id)
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
        return Response(chapters)


class SuwayomiImportView(APIView):
    """Importe un manga depuis Suwayomi dans le catalogue local."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        suwayomi_adapter=Provide[Container.persistence.suwayomi_adapter],
        manga_service=Provide[Container.core.manga_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.suwayomi_adapter = suwayomi_adapter
        self.manga_service = manga_service

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

        # Pré-synchro des chapitres : best-effort. Si Suwayomi est injoignable,
        # l'import du manga reste valide (les chapitres se resynchronisent à la
        # lecture) plutôt que de faire échouer tout l'import.
        try:
            self.manga_service.get_chapters(external_id)
        except SuwayomiUnavailableError:
            logger.warning(
                "Pré-synchro des chapitres ignorée pour %s : Suwayomi injoignable.",
                external_id,
            )

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
        except SuwayomiUnavailableError:
            return _suwayomi_unreachable_response()
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

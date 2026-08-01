"""Manga chapters, favorites and third-party tracker sync (AniList/MAL)."""

import base64

from adapters.persistence.suwayomi_adapter import SuwayomiUnavailableError
from animetix_project.logging_config import get_logger
from dependency_injector.wiring import Provide, inject
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...containers import Container
from ...serializers import MangaChapterSerializer
from ...services.tracker_sync import push_manga_progress_to_trackers
from .suwayomi import suwayomi_unreachable_response

logger = get_logger("animetix.api")

# Un corps form-encoded (ou un client qui sérialise ses booléens à la main)
# livre des chaînes : `bool("false")` vaut True, ce qui inverse silencieusement
# la demande — un « marquer non lu » deviendrait un « marquer lu ».
_FALSY_STRINGS = frozenset({"false", "0", "", "none", "null", "off", "no"})


def parse_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() not in _FALSY_STRINGS
    return bool(value)


class MangaChapterListView(APIView):
    """Liste des chapitres d'un manga."""

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(self, manga_service=Provide[Container.core.manga_service], **kwargs):
        super().__init__(**kwargs)
        self.manga_service = manga_service

    def get(self, request, media_id):
        try:
            chapters = self.manga_service.get_chapters(media_id)
        except SuwayomiUnavailableError:
            return suwayomi_unreachable_response()
        serializer = MangaChapterSerializer(chapters, many=True)
        return Response(serializer.data)


class MangaChapterDetailView(APIView):
    """Détails d'un chapitre (incluant les pages)."""

    permission_classes = [permissions.AllowAny]

    @inject
    def __init__(self, manga_service=Provide[Container.core.manga_service], **kwargs):
        super().__init__(**kwargs)
        self.manga_service = manga_service

    def get(self, request, media_id, chapter_number):
        # Suwayomi injoignable != chapitre inexistant : sans ce garde-fou la vue
        # renvoyait une 500 opaque, que le lecteur traduisait en « chapitre
        # indisponible hors-ligne » — message trompeur pour un serveur éteint.
        try:
            chapter = self.manga_service.get_chapter_details(
                media_id, float(chapter_number)
            )
        except SuwayomiUnavailableError:
            return suwayomi_unreachable_response()

        if chapter:
            serializer = MangaChapterSerializer(chapter)
            return Response(serializer.data)
        return Response(
            {"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND
        )


class MangaProgressView(APIView):
    """Progression de lecture de l'utilisateur sur tous les chapitres d'un manga."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        progress_service=Provide[Container.core.manga_progress_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.progress_service = progress_service

    def get(self, request, media_id):
        payload = self.progress_service.get_manga_progress(request.user, media_id)
        if payload is None:
            # Manga jamais importé dans le catalogue : rien n'a pu être lu.
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(payload)


class MangaChapterProgressView(APIView):
    """Enregistre la page courante / l'état lu d'un chapitre."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        progress_service=Provide[Container.core.manga_progress_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.progress_service = progress_service

    def put(self, request, media_id, chapter_number):
        try:
            number = float(chapter_number)
            last_page_read = int(request.data.get("last_page_read", 0))
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid chapter number or page index"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if last_page_read < 0:
            return Response(
                {"error": "Invalid chapter number or page index"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_read = parse_bool(request.data.get("is_read"), False)

        result = self.progress_service.record_progress(
            request.user, media_id, number, last_page_read, is_read
        )
        if result is None:
            return Response(
                {"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if result["chapter_completed"]:
            self._push_to_trackers(request.user, media_id, number)
        return Response(result)

    def _push_to_trackers(self, user, media_id, number):
        from ...models import MediaItem

        try:
            manga = MediaItem.objects.get(external_id=media_id, media_type="Manga")
        except MediaItem.DoesNotExist:
            return
        try:
            push_manga_progress_to_trackers(user, manga, media_id, int(number))
        except Exception:
            # La progression est déjà enregistrée : un tracker HS ne doit pas
            # transformer une lecture réussie en erreur côté lecteur.
            logger.warning("Push trackers échoué pour %s ch.%s", media_id, number)


class MangaProgressMarkReadView(APIView):
    """Marque un ou plusieurs chapitres comme lus / non lus."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        progress_service=Provide[Container.core.manga_progress_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.progress_service = progress_service

    def post(self, request, media_id):
        raw = request.data.get("chapter_numbers")
        if not isinstance(raw, list) or not raw:
            return Response(
                {"error": "chapter_numbers must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            numbers = [float(value) for value in raw]
        except (TypeError, ValueError):
            return Response(
                {"error": "chapter_numbers must contain numbers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = self.progress_service.set_read(
            request.user,
            media_id,
            numbers,
            parse_bool(request.data.get("is_read"), True),
        )
        return Response({"updated": updated})


class FavoriteMangaToggleView(APIView):
    """Permet de s'abonner / désabonner (favoris) à un manga."""

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

    def post(self, request, media_id):
        from ...models import FavoriteManga, MediaItem

        # 1. Récupération ou auto-import du manga
        try:
            manga = MediaItem.objects.get(external_id=media_id, media_type="Manga")
        except MediaItem.DoesNotExist:
            source_id = request.data.get("source_id")
            suwayomi_manga_id = request.data.get("suwayomi_manga_id")

            if not source_id or not suwayomi_manga_id:
                return Response(
                    {
                        "error": "Manga non trouvé et source_id/suwayomi_manga_id manquants pour l'import automatique."
                    },
                    status=400,
                )

            # Import automatique depuis Suwayomi
            if not self.suwayomi_adapter:
                return Response(
                    {"error": "Intégration Suwayomi non configurée."}, status=500
                )

            manga_details = self.suwayomi_adapter.get_manga_details(suwayomi_manga_id)
            if not manga_details:
                return Response(
                    {"error": "Impossible de charger les détails du manga."}, status=404
                )

            thumbnail_url = manga_details.get("thumbnailUrl")
            image_url = None
            if thumbnail_url:
                encoded_thumb = base64.b64encode(thumbnail_url.encode("utf-8")).decode(
                    "utf-8"
                )
                image_url = (
                    f"/api/v1/media/Manga/suwayomi-image/?page_url={encoded_thumb}"
                )

            manga = MediaItem.objects.create(
                external_id=media_id,
                media_type="Manga",
                title=manga_details.get("title", "Unknown Title"),
                description=manga_details.get("description", ""),
                synopsis_en=manga_details.get("description", ""),
                image_url=image_url,
                metadata={
                    "source_id": source_id,
                    "suwayomi_id": suwayomi_manga_id,
                    "author": manga_details.get("author", ""),
                    "artist": manga_details.get("artist", ""),
                    "status": manga_details.get("status", ""),
                },
            )

            # Synchronisation initiale des chapitres
            self.manga_service.get_chapters(media_id)

        # 2. Toggle or set status
        status_payload = request.data.get("status")
        if status_payload:
            if status_payload not in ["reading", "completed", "plan_to_read"]:
                return Response({"error": "Invalid status"}, status=400)
            favorite, created = FavoriteManga.objects.get_or_create(
                user=request.user, manga=manga
            )
            favorite.status = status_payload
            favorite.save()
            is_favorite = True
        else:
            favorite, created = FavoriteManga.objects.get_or_create(
                user=request.user, manga=manga
            )
            if not created:
                favorite.delete()
                is_favorite = False
            else:
                is_favorite = True

        status_val = favorite.status if is_favorite else None
        return Response(
            {"success": True, "is_favorite": is_favorite, "status": status_val}
        )

    def get(self, request, media_id):
        from ...models import FavoriteManga

        try:
            fav = FavoriteManga.objects.get(
                user=request.user, manga__external_id=media_id
            )
            return Response({"is_favorite": True, "status": fav.status})
        except FavoriteManga.DoesNotExist:
            return Response({"is_favorite": False, "status": None})


class FavoriteMangaListView(APIView):
    """Liste tous les mangas favoris de l'utilisateur."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery
        from django.db.models.functions import Coalesce

        from ...models import FavoriteManga, MangaChapter, MangaReadingProgress
        from ...serializers import FavoriteMangaSerializer

        # Use a correlated subquery to avoid N+1 query per FavoriteManga in the list
        unread_chapters_subquery = (
            MangaChapter.objects.filter(
                manga=OuterRef("manga"), number__gt=OuterRef("last_read_chapter")
            )
            .values("manga")
            .annotate(count=Count("id"))
            .values("count")
        )
        read_chapters_subquery = (
            MangaChapter.objects.filter(
                manga=OuterRef("manga"),
                progress__user=OuterRef("user"),
                progress__is_read=True,
            )
            .values("manga")
            .annotate(count=Count("id"))
            .values("count")
        )
        total_chapters_subquery = (
            MangaChapter.objects.filter(manga=OuterRef("manga"))
            .values("manga")
            .annotate(count=Count("id"))
            .values("count")
        )
        # « Lecture commencée » : un chapitre entamé compte, pas seulement
        # terminé — sinon la carte n'offre aucun « Reprendre » à quelqu'un au
        # milieu du chapitre 1, là où la fiche œuvre et la popup en affichent un.
        started_subquery = MangaReadingProgress.objects.filter(
            Q(is_read=True) | Q(last_page_read__gt=0),
            user=OuterRef("user"),
            chapter__manga=OuterRef("manga"),
        )

        favorites = (
            FavoriteManga.objects.filter(user=request.user)
            .select_related("manga")
            .annotate(
                unread_chapters_count_annotated=Coalesce(
                    Subquery(unread_chapters_subquery, output_field=IntegerField()), 0
                ),
                read_count_annotated=Coalesce(
                    Subquery(read_chapters_subquery, output_field=IntegerField()), 0
                ),
                total_chapters_annotated=Coalesce(
                    Subquery(total_chapters_subquery, output_field=IntegerField()), 0
                ),
                has_started_annotated=Exists(started_subquery),
            )
        )
        serializer = FavoriteMangaSerializer(favorites, many=True)
        return Response(serializer.data)


class TrackerConnectionListView(APIView):
    """Lists all active tracker connections of the current user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from ...models import TrackerConnection
        from ...serializers import TrackerConnectionSerializer

        connections = TrackerConnection.objects.filter(user=request.user)
        serializer = TrackerConnectionSerializer(connections, many=True)
        return Response(serializer.data)


class TrackerConnectionLinkView(APIView):
    """Links or updates a tracker connection."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from ...models import TrackerConnection

        tracker = request.data.get("tracker")
        username = request.data.get("username")
        token = request.data.get("token")

        if not tracker or not username or not token:
            return Response(
                {"error": "tracker, username and token are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tracker not in ["myanimelist", "anilist"]:
            return Response(
                {"error": "invalid tracker type"}, status=status.HTTP_400_BAD_REQUEST
            )

        connection, created = TrackerConnection.objects.update_or_create(
            user=request.user,
            tracker=tracker,
            defaults={"username": username, "token": token},
        )

        return Response({"success": True, "created": created})


class TrackerConnectionUnlinkView(APIView):
    """Unlinks a tracker connection."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from ...models import TrackerConnection

        tracker = request.data.get("tracker")

        if not tracker:
            return Response(
                {"error": "tracker parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count, _ = TrackerConnection.objects.filter(
            user=request.user, tracker=tracker
        ).delete()

        return Response({"success": True, "deleted": deleted_count > 0})


def _serialize_link(link) -> dict:
    return {
        "tracker": link.tracker,
        "status": link.status,
        "remote_id": link.remote_id,
        "remote_title": link.remote_title,
        "remote_progress": link.remote_progress,
    }


class MangaTrackerLinksView(APIView):
    """Liaisons de l'œuvre pour l'utilisateur, en proposant celles qui manquent."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, tracker_service=Provide[Container.core.manga_tracker_service], **kwargs
    ):
        super().__init__(**kwargs)
        self.tracker_service = tracker_service

    def get(self, request, media_id):
        from ...models import MediaItem

        if not MediaItem.objects.filter(
            external_id=media_id, media_type="Manga"
        ).exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Ne cherche que pour les trackers connectés encore sans liaison ; les
        # propositions déjà en base ne sont pas re-cherchées.
        self.tracker_service.suggest(request.user, media_id)
        links = self.tracker_service.list_links(request.user, media_id)
        return Response(
            {
                "links": [_serialize_link(link) for link in links],
                # Indispensable pour que l'UI distingue « aucun tracker connecté »
                # (on n'affiche rien) de « connecté mais aucune correspondance
                # trouvée » (on affiche l'invitation à chercher manuellement).
                # Sans ce champ, les deux cas donnent `links: []`.
                "connected": self.tracker_service.connected_trackers(request.user),
            }
        )


class MangaTrackerSearchView(APIView):
    """Recherche manuelle d'une correspondance chez un tracker donné."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, tracker_service=Provide[Container.core.manga_tracker_service], **kwargs
    ):
        super().__init__(**kwargs)
        self.tracker_service = tracker_service

    def post(self, request, media_id):
        tracker = request.data.get("tracker")
        query = request.data.get("query")
        if not tracker or not query:
            return Response(
                {"error": "tracker and query are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        results = self.tracker_service.search(request.user, tracker, query)
        return Response({"results": results})


class MangaTrackerLinkView(APIView):
    """Confirme une liaison (proposée ou choisie manuellement)."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, tracker_service=Provide[Container.core.manga_tracker_service], **kwargs
    ):
        super().__init__(**kwargs)
        self.tracker_service = tracker_service

    def post(self, request, media_id):
        tracker = request.data.get("tracker")
        remote_id = request.data.get("remote_id")
        if not tracker or not remote_id:
            return Response(
                {"error": "tracker and remote_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        link = self.tracker_service.confirm(request.user, media_id, tracker, remote_id)
        if link is None:
            return Response(
                {"error": "Manga or tracker not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_serialize_link(link))


class MangaTrackerUnlinkView(APIView):
    """Supprime une liaison confirmée ou proposée."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, tracker_service=Provide[Container.core.manga_tracker_service], **kwargs
    ):
        super().__init__(**kwargs)
        self.tracker_service = tracker_service

    def delete(self, request, media_id, tracker):
        success = self.tracker_service.unlink(request.user, media_id, tracker)
        return Response({"success": success})


class TrackerLinkListView(APIView):
    """Toutes les liaisons de l'utilisateur, tous mangas confondus (profil)."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self, tracker_service=Provide[Container.core.manga_tracker_service], **kwargs
    ):
        super().__init__(**kwargs)
        self.tracker_service = tracker_service

    def get(self, request):
        links = self.tracker_service.list_all_links(request.user)
        return Response(
            [
                {
                    **_serialize_link(link),
                    "manga_id": link.manga.external_id,
                    "manga_title": link.manga.title,
                }
                for link in links
            ]
        )


class MangaChapterSyncView(APIView):
    """Synchronizes manga progress to linked third-party trackers (AniList, MyAnimeList)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, media_id, chapter_number):
        from ...models import FavoriteManga, MangaChapter, MediaItem

        # 1. Fetch the manga
        try:
            manga = MediaItem.objects.get(external_id=media_id, media_type="Manga")
        except MediaItem.DoesNotExist:
            return Response(
                {"error": "Manga not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Parse chapter number
        try:
            progress = int(float(chapter_number))
            progress_float = float(chapter_number)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid chapter number format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1.5 Update or create FavoriteManga record and handle auto-transitions
        favorite, created = FavoriteManga.objects.get_or_create(
            user=request.user, manga=manga
        )
        favorite.last_read_chapter = max(favorite.last_read_chapter, progress_float)

        # Check if there are any chapters with a number strictly greater than progress_float
        has_future_chapters = MangaChapter.objects.filter(
            manga=manga, number__gt=progress_float
        ).exists()

        if not has_future_chapters:
            favorite.status = "completed"
        elif favorite.status == "plan_to_read":
            favorite.status = "reading"

        favorite.save()

        from ...services.tracker_sync import push_manga_progress_to_trackers

        results = push_manga_progress_to_trackers(
            request.user, manga, media_id, progress
        )
        if not results:
            return Response({"success": True, "message": "No trackers connected."})
        return Response({"success": True, "results": results})

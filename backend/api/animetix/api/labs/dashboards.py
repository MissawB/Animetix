"""Labs dashboards: daily challenge hub and latent-space explorer data."""

import datetime
import json
import os

from animetix_project.logging_config import get_logger
from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import DailyChallenge  # noqa: E402
from ...serializers import DailyChallengeSerializer  # noqa: E402

logger = get_logger("animetix." + __name__)


class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyChallenge.objects.all()
    serializer_class = DailyChallengeSerializer
    permission_classes = [permissions.AllowAny]


class LatentSpaceDataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        media = request.query_params.get("media", "anime").lower()
        type_param = request.query_params.get("type", "thematic").lower()
        mapping = {
            ("anime", "thematic"): "latent_space_anime_thematic.json",
            ("anime", "visual"): "latent_space_anime_visual_vibe.json",
            ("anime", "scenario"): "latent_space_anime_plot.json",
            ("manga", "thematic"): "latent_space_manga_thematic.json",
            ("manga", "visual"): "latent_space_manga_visual_vibe.json",
            ("manga", "scenario"): "latent_space_manga_plot.json",
            ("character", "thematic"): "latent_space_character_vibe.json",
            ("character", "visual"): "latent_space_character_visual_vibe.json",
        }
        filename = mapping.get((media, type_param), "latent_space_3d.json")
        project_root = settings.BASE_DIR.parent.parent
        file_path = project_root / "data" / "artifacts" / filename
        if not os.path.exists(file_path):
            file_path = project_root / "data" / "artifacts" / "latent_space_3d.json"
            if not os.path.exists(file_path):
                return Response([], status=status.HTTP_404_NOT_FOUND)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Response(data)
        except Exception:
            logger.exception("Error loading latent space artifact")
            return Response({"error": "Internal server error"}, status=500)


class DailyChallengeDataView(APIView):
    permission_classes = [permissions.AllowAny]

    # How far back past challenges stay replayable.
    MAX_BACK_DAYS = 30

    def get(self, request):
        today = datetime.date.today()
        day = today
        raw_date = request.query_params.get("date")
        if raw_date:
            try:
                parsed = datetime.date.fromisoformat(raw_date)
                if parsed <= today and (today - parsed).days <= self.MAX_BACK_DAYS:
                    day = parsed
            except ValueError:
                pass

        modes = [
            {
                "id": "anime",
                "media_type": "Anime",
                "brush1": "ANIME",
                "brush2": "DU JOUR",
                "description": "Devine la série animée mystère du jour.",
                "gradient": "from-blue-600 to-indigo-900",
                "icon": "/static/img/modes/classic.png",
            },
            {
                "id": "manga",
                "media_type": "Manga",
                "brush1": "MANGA",
                "brush2": "DU JOUR",
                "description": "Devine l'œuvre papier mystère du jour.",
                "gradient": "from-rose-500 to-red-900",
                "icon": "/static/img/modes/covertest.png",
            },
            {
                "id": "character",
                "media_type": "Character",
                "brush1": "PERSO",
                "brush2": "DU JOUR",
                "description": "Devine le personnage mystère du jour.",
                "gradient": "from-purple-600 to-fuchsia-900",
                "icon": "/static/img/modes/akinetix.png",
            },
        ]

        # Attach this user's saved score per universe for the requested day.
        results = {}
        if request.user.is_authenticated:
            from ...models import DailyResult  # noqa: E402

            for r in DailyResult.objects.filter(user=request.user, date=day):
                results[r.media_type] = {"score": r.score, "attempts": r.attempts}
        for m in modes:
            res = results.get(m["media_type"])
            m["completed"] = bool(res)
            m["score"] = res["score"] if res else None

        prev_day = day - datetime.timedelta(days=1)
        can_prev = (today - prev_day).days <= self.MAX_BACK_DAYS
        return Response(
            {
                "date": day.isoformat(),
                "is_today": day == today,
                "prev_date": prev_day.isoformat() if can_prev else None,
                "next_date": (
                    None
                    if day >= today
                    else (day + datetime.timedelta(days=1)).isoformat()
                ),
                "total_score": sum(r["score"] for r in results.values()),
                "modes": modes,
            }
        )

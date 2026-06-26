import datetime
import json

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from pydantic import ValidationError

from animetix.api.dependencies import get_session_service

from ..schemas import OfflineSyncSchema
from .common import logger


def get_task_status(request, task_id):
    """Checks the status of a task from cache and returns a result fragment if ready."""
    session = get_session_service(request)
    try:
        task_data = cache.get(f"task_result:{task_id}")
        if task_data and task_data.get("ready"):
            result = task_data.get("result")
            if isinstance(result, dict) and "scenario" in result:
                return render(
                    request,
                    "animetix/archetypist/archetypist_result_fragment.html",
                    {
                        "reasoning": result.get("reasoning"),
                        "scenario": result.get("scenario"),
                        "fusion_image": result.get("fusion_image"),
                        "item_A": session.get("temp_item_A"),
                        "item_B": session.get("temp_item_B"),
                        "fusion_id": session.get("last_fusion_id"),
                    },
                )
            return JsonResponse({"ready": True, "result": result})
    except Exception as e:
        logger.error(f"⚠️ Tasks Cache Status Error: {e}")
        return HttpResponse(status=204)
    return HttpResponse(status=204)


@ratelimit(key="user", rate="1/5m", block=True)
def sync_offline_data(request):
    """
    Synchronizes offline game results with the server profile.
    Secured with rate limiting and daily XP caps to prevent abuse.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Pydantic validation
        try:
            schema = OfflineSyncSchema.model_validate(json.loads(request.body))
        except ValidationError as ve:
            return JsonResponse({"error": ve.errors()}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Track daily gain in cache (persistence = 24h)
        today = datetime.date.today().isoformat()
        cache_key = f"offline_xp_limit_{request.user.id}_{today}"
        daily_gain = cache.get(cache_key, 0)

        MAX_DAILY_OFFLINE_XP = (
            200  # Limite de 200 XP (~20 victoires) par jour via offline sync
        )

        if daily_gain >= MAX_DAILY_OFFLINE_XP:
            return JsonResponse(
                {"error": "Daily offline XP limit reached. Play online for more!"},
                status=403,
            )

        xp_gained = 0
        synced_count = 0

        for game in schema.root:
            if daily_gain + xp_gained >= MAX_DAILY_OFFLINE_XP:
                break  # On arrête l'attribution si le plafond est atteint

            if game.score == 100:
                request.user.profile.add_win(
                    is_daily=False,
                    game_mode=game.game_mode,
                    media_type=game.media_type,
                    attempts=game.attempts,
                )
                xp_gained += 10
                synced_count += 1

        if xp_gained > 0:
            request.user.profile.xp += xp_gained
            request.user.profile.save()
            # On met à jour le cache avec le nouveau total
            cache.set(cache_key, daily_gain + xp_gained, 60 * 60 * 24)

        return JsonResponse(
            {
                "status": "success",
                "synced_items": synced_count,
                "xp_gained": xp_gained,
                "daily_total": daily_gain + xp_gained,
            }
        )

    except Exception as e:
        logger.error(f"❌ Offline Sync Error: {e}")
        return JsonResponse(
            {"error": "An internal error occurred during synchronization."}, status=400
        )

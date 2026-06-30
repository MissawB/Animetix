from django.core.cache import cache
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

__all__ = ["UndercoverPublicRoomsView"]

# Must match the index/room keys written by the Undercover WS consumer.
INDEX_KEY = "undercover_room_index"


class UndercoverPublicRoomsView(APIView):
    """Lists the currently-open *public* Undercover rooms so players can browse and
    join them. Private rooms stay hidden (reachable only by code/URL).

    CPU/no-login game → AllowAny and throttle-exempt (browsing must not hit the
    anon day cap). The cache can't enumerate keys, so the consumer keeps an index
    of room codes; we resolve each to its live room here and prune dead ones.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = []

    def get(self, request):
        codes = cache.get(INDEX_KEY) or []
        rooms = []
        alive = []
        for code in codes:
            room = cache.get(f"undercover_room_{code}")
            if not room:
                continue  # stale entry → drop from the index
            alive.append(code)
            players = room.get("players") or {}
            if room.get("visibility") != "public" or not players:
                continue
            host = players.get(room.get("host")) or {}
            rooms.append(
                {
                    "code": code,
                    "name": room.get("name") or "",
                    "players": len(players),
                    "state": room.get("state", "lobby"),
                    "host": host.get("name", ""),
                    "num_undercovers": room.get("num_undercovers", 1),
                    "num_mrwhites": room.get("num_mrwhites", 0),
                }
            )
        if len(alive) != len(codes):
            cache.set(INDEX_KEY, alive, timeout=86400)
        # Joinable (lobby) rooms first, then by crowd size.
        rooms.sort(key=lambda r: (r["state"] != "lobby", -r["players"]))
        return Response({"rooms": rooms})

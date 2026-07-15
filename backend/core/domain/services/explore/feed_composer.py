"""Compose le feed personnalisé de la page Explorer par cascade de couches."""

TARGET_ROWS = 8
MAX_SEED_ROWS = 3
MIN_ROW_ITEMS = 4
ROW_ITEM_LIMIT = 20

_ITEM_KEYS = (
    "id",
    "title",
    "media_type",
    "image",
    "synopsis_fr",
    "year",
    "popularity",
    "rating",
    "genres",
)


class FeedComposer:
    def __init__(self, catalog_service, graph_port):
        self._catalog_service = catalog_service
        self._graph_port = graph_port

    def compose(self, user, media_type: str) -> dict:
        catalog = self._catalog_service.get_catalog(media_type)
        rows: list[dict] = []
        seen_ids: set[str] = set()
        personalized = False

        ai_row = self._ai_reco_row(user, media_type, catalog, seen_ids)
        if ai_row:
            rows.append(ai_row)
            personalized = True

        byl_rows = self._because_you_liked_rows(user, media_type, catalog, seen_ids)
        if byl_rows:
            rows.extend(byl_rows)
            personalized = True

        rows.extend(self._cold_start_rows(catalog, seen_ids))
        return {"rows": rows[:TARGET_ROWS], "personalized": personalized}

    def _ai_reco_row(self, user, media_type, catalog, seen_ids):
        if user is None or not getattr(user, "is_authenticated", False):
            return None
        from animetix.models import UserRecommendation  # noqa: E402

        recs = (
            UserRecommendation.objects.filter(
                user=user, media_item__media_type=media_type
            )
            .select_related("media_item")
            .order_by("rank")
        )
        index = catalog.get("id_to_full_data", {})
        items = []
        for rec in recs:
            item = index.get(str(rec.media_item.external_id))
            if item:
                items.append(item)
        picked = self._take(items, seen_ids)
        if not picked:
            return None
        return {
            "kind": "ai_reco",
            "title": "Choisi pour vous par l'IA",
            "reason": "Recommandation personnalisée",
            "seed": None,
            "items": picked,
        }

    def _seeds(self, user, media_type):
        if user is None or not getattr(user, "is_authenticated", False):
            return []
        from animetix.models import DuelRoom, FavoriteManga  # noqa: E402
        from django.db.models import Q  # noqa: E402

        seeds, seen = [], set()

        favs = (
            FavoriteManga.objects.filter(user=user)
            .select_related("manga")
            .order_by("-created_at")
        )
        for fav in favs:
            key = str(fav.manga.external_id)
            if key not in seen:
                seen.add(key)
                seeds.append(
                    {"id": key, "title": fav.manga.title, "media_type": "Manga"}
                )

        duels = (
            DuelRoom.objects.filter(Q(player1=user) | Q(player2=user), is_finished=True)
            .exclude(secret_title="")
            .order_by("-created_at")
        )
        for room in duels:
            if room.secret_title not in seen:
                seen.add(room.secret_title)
                seeds.append(
                    {
                        "id": None,
                        "title": room.secret_title,
                        "media_type": room.media_type,
                    }
                )

        return seeds[:MAX_SEED_ROWS]

    def _neighbor_ids(self, neighborhood):
        ids = []
        for node in neighborhood.get("nodes", []):
            nid = (node.get("properties") or {}).get("id")
            if nid is not None:
                ids.append(str(nid))
        return ids

    def _because_you_liked_rows(self, user, media_type, catalog, seen_ids):
        index = catalog.get("id_to_full_data", {})
        title_index = catalog.get("title_to_full_data", {})
        rows = []
        for seed in self._seeds(user, media_type):
            seed_id = seed["id"]
            # Un seed issu d'un duel n'a pas d'id : on le résout par titre.
            if seed_id is None:
                resolved = title_index.get(seed["title"])
                seed_id = str(resolved["id"]) if resolved else None
            if seed_id is None:
                continue
            neighborhood = self._graph_port.get_neighborhood(
                seed_id, seed["media_type"], 1
            )
            neighbor_items = [
                index[nid] for nid in self._neighbor_ids(neighborhood) if nid in index
            ]
            picked = self._take(neighbor_items, seen_ids)
            if len(picked) >= MIN_ROW_ITEMS:
                rows.append(
                    {
                        "kind": "because_you_liked",
                        "title": f"Parce que tu as aimé {seed['title']}",
                        "reason": "Basé sur tes favoris et tes duels",
                        "seed": {"id": seed["id"] or seed_id, "title": seed["title"]},
                        "items": picked,
                    }
                )
        return rows

    def _serialize(self, item: dict) -> dict:
        out = {k: item.get(k) for k in _ITEM_KEYS}
        out["genres"] = item.get("genres", []) or []
        return out

    def _take(self, items, seen_ids: set) -> list[dict]:
        """Sérialise, déduplique via seen_ids, limite à ROW_ITEM_LIMIT."""
        picked = []
        for it in items:
            key = str(it.get("id"))
            if key in seen_ids:
                continue
            seen_ids.add(key)
            picked.append(self._serialize(it))
            if len(picked) >= ROW_ITEM_LIMIT:
                break
        return picked

    def _cold_start_rows(self, catalog, seen_ids: set) -> list[dict]:
        """Plancher garanti : rangées top_rated + new.

        Chaque rangée ne dédoublonne que contre les items déjà servis par
        les couches précédentes (seen_ids reçu en entrée) : top_rated et
        new ne se dédoublonnent pas l'une contre l'autre, sinon un petit
        catalogue (moins de ROW_ITEM_LIMIT titres) verrait la première
        rangée épuiser tout le stock et laisser la seconde vide.
        """
        db = catalog.get("db", [])
        rows = []

        by_rating = sorted(db, key=lambda i: (i.get("rating") or 0), reverse=True)
        top_seen = set(seen_ids)
        top_items = self._take(by_rating, top_seen)
        if top_items:
            rows.append(
                {
                    "kind": "top_rated",
                    "title": "Les mieux notés",
                    "reason": "Populaire en ce moment",
                    "seed": None,
                    "items": top_items,
                }
            )

        by_year = sorted(db, key=lambda i: (i.get("year") or 0), reverse=True)
        new_seen = set(seen_ids)
        new_items = self._take(by_year, new_seen)
        if new_items:
            rows.append(
                {
                    "kind": "new",
                    "title": "Nouveautés",
                    "reason": "Ajouts récents",
                    "seed": None,
                    "items": new_items,
                }
            )

        seen_ids.update(top_seen)
        seen_ids.update(new_seen)
        return rows

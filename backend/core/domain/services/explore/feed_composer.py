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

        # (les couches personnalisées seront insérées ici par les tâches suivantes)

        rows.extend(self._cold_start_rows(catalog, seen_ids))
        return {"rows": rows[:TARGET_ROWS], "personalized": personalized}

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

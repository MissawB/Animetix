"""Backfill Akinetix question data to make questions less repetitive.

Two data fixes (the engine/formatter already support the question types):
  * purge polluted ``micro_tags``/``tags`` — the offline tagging pipeline ran
    without a compute unit and stored its error message as a tag, which the tag
    filter then drops, leaving almost no usable tags;
  * backfill ``metadata['studios']`` from AniList (the field was empty for every
    work), unlocking "C'est signé X ?" style questions.

``MediaItem.external_id`` is the AniList media id, so studios are fetched in
batches of 50 through the AniList GraphQL API.

Note: ``themes`` are intentionally NOT backfilled — AniList has no separate
"themes" concept; its thematic signal lives in ``tags``, already wired into the
engine.

Usage:
    python manage.py backfill_akinetix_attributes
    python manage.py backfill_akinetix_attributes --media-type Anime --limit 2000
    python manage.py backfill_akinetix_attributes --no-studios   # only purge tags
"""

import time

import requests
from core.domain.services.akinetix.question_formatter import is_valid_micro_tag
from django.core.management.base import BaseCommand

from animetix.models import MediaItem

ANILIST_URL = "https://graphql.anilist.co"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Animetix/1.0 (akinetix backfill)",
}
STUDIOS_QUERY = """
query ($ids: [Int], $type: MediaType) {
  Page(perPage: 50) {
    media(id_in: $ids, type: $type) {
      id
      studios(isMain: true) { nodes { name } }
    }
  }
}
"""


def _fetch_studios(ids, anilist_type, max_retries=4):
    """Fetch main studios for a batch of ids, retrying on AniList rate limits."""
    for attempt in range(max_retries):
        resp = requests.post(
            ANILIST_URL,
            json={
                "query": STUDIOS_QUERY,
                "variables": {"ids": ids, "type": anilist_type},
            },
            headers=HEADERS,
            timeout=30,
        )
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60)) + 1
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    else:
        raise RuntimeError("AniList rate limit: retries exhausted")
    media = resp.json().get("data", {}).get("Page", {}).get("media", []) or []
    out = {}
    for m in media:
        names = [
            n["name"]
            for n in (m.get("studios", {}).get("nodes") or [])
            if n.get("name")
        ]
        out[int(m["id"])] = names
    return out


class Command(BaseCommand):
    help = "Backfill Akinetix question data (purge polluted tags + AniList studios)."

    def add_arguments(self, parser):
        parser.add_argument("--media-type", default="Anime")
        parser.add_argument("--limit", type=int, default=2000)
        parser.add_argument(
            "--no-studios", action="store_true", help="Only purge polluted tags."
        )

    def handle(self, *args, **opts):
        media_type = opts["media_type"]
        anilist_type = "MANGA" if media_type == "Manga" else "ANIME"

        items = list(
            MediaItem.objects.filter(media_type=media_type).order_by("-popularity")[
                : opts["limit"]
            ]
        )
        self.stdout.write(f"{len(items)} {media_type} items to process.")

        # 1. Fetch studios from AniList in batches of 50.
        studios_by_id = {}
        if not opts["no_studios"]:
            # Only fetch works that don't already have studios → idempotent re-runs
            # converge quickly and don't waste the AniList rate budget.
            ids = [
                int(it.external_id)
                for it in items
                if str(it.external_id).isdigit()
                and not (it.metadata or {}).get("studios")
            ]
            self.stdout.write(f"  {len(ids)} works still missing studios.")
            for i in range(0, len(ids), 50):
                batch = ids[i : i + 50]
                try:
                    studios_by_id.update(_fetch_studios(batch, anilist_type))
                except Exception as e:  # best-effort per batch
                    self.stderr.write(f"  AniList batch {i // 50} failed: {e}")
                time.sleep(2.0)  # AniList's degraded limit is ~30 req/min
            self.stdout.write(f"  studios fetched for {len(studios_by_id)} ids.")

        # 2. Apply: purge polluted tags + set studios.
        purged = studios_set = 0
        for it in items:
            meta = it.metadata or {}
            changed = item_purged = False

            for key in ("micro_tags", "tags"):
                vals = meta.get(key)
                if isinstance(vals, list):
                    clean = [t for t in vals if is_valid_micro_tag(t)]
                    if len(clean) != len(vals):
                        meta[key] = clean
                        changed = item_purged = True

            if str(it.external_id).isdigit():
                names = studios_by_id.get(int(it.external_id))
                if names and meta.get("studios") != names:
                    meta["studios"] = names
                    changed = True
                    studios_set += 1

            if item_purged:
                purged += 1
            if changed:
                it.metadata = meta
                it.save(update_fields=["metadata"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Tags purged on {purged} items, "
                f"studios set on {studios_set} items."
            )
        )

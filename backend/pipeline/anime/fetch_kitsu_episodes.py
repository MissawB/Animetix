# backend/pipeline/anime/fetch_kitsu_episodes.py
"""Episode titles and plot summaries, from Kitsu, for the World Boss quiz.

AniList carries no per-episode plot and neither does Jikan's episode list. Kitsu
does: /anime/{id}/episodes returns `canonicalTitle` AND `synopsis` per episode. The
join key is the MAL id, which the catalogue holds for the whole top 300.

Idempotent: works already present in the output file are skipped, so a rerun only
fetches what is missing. Kitsu asks for ~1 request/second; we oblige.
"""

import json
import logging
import os
import sys
import time

logger = logging.getLogger("animetix." + __name__)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "backend"))
from core.utils.security import safe_http_request  # noqa: E402

CATALOG_FILE = os.path.join(BASE_DIR, "data", "processed", "clean_root_animes.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "anime_episodes.json")

KITSU = "https://kitsu.io/api/edge"
HEADERS = {"Accept": "application/vnd.api+json"}
TOP_N = 300  # The quiz never asks a plot question outside the top 300.
PAGE_SIZE = 20
THROTTLE_SECONDS = 1.0


def kitsu_id_from_mapping(payload):
    """The `included` block holds the Kitsu anime the MAL id maps to."""
    for entry in (payload or {}).get("included", []):
        if entry.get("type") == "anime":
            return str(entry["id"])
    return None


def episodes_from_payload(payload):
    """Keep episodes that carry a title or a plot; drop the empty shells."""
    episodes = []
    for entry in (payload or {}).get("data", []):
        attrs = entry.get("attributes") or {}
        number = attrs.get("number")
        title = (attrs.get("canonicalTitle") or "").strip()
        synopsis = (attrs.get("synopsis") or "").strip()
        if number is None or (not title and not synopsis):
            continue
        episodes.append({"number": int(number), "title": title, "synopsis": synopsis})
    return sorted(episodes, key=lambda e: e["number"])


class KitsuHTTPError(Exception):
    """A Kitsu request came back non-200. Distinct from a legitimate empty
    result (e.g. a work with no Kitsu mapping), which is not an error."""


def _get(url, params):
    response = safe_http_request("GET", url, params=params, headers=HEADERS, timeout=20)
    if response.status_code != 200:
        logger.warning("Kitsu %s -> HTTP %s", url, response.status_code)
        raise KitsuHTTPError(f"{url} -> HTTP {response.status_code}")
    return response.json()


def fetch_episodes(id_mal):
    """Raises KitsuHTTPError if any request fails. A failed page must never be
    mistaken for a short final page, so the caller (run()) must treat a failed
    work as wholly unfetched this run -- not partially persisted -- and retry
    it from scratch next time."""
    mapping = _get(
        f"{KITSU}/mappings",
        {
            "filter[externalSite]": "myanimelist/anime",
            "filter[externalId]": str(id_mal),
            "include": "item",
        },
    )
    kitsu_id = kitsu_id_from_mapping(mapping)
    if not kitsu_id:
        return []  # no Kitsu mapping for this work: a legitimate empty result

    time.sleep(THROTTLE_SECONDS)  # close the gap before the first episodes request

    episodes, offset = [], 0
    while True:
        page = _get(
            f"{KITSU}/anime/{kitsu_id}/episodes",
            {"page[limit]": PAGE_SIZE, "page[offset]": offset},
        )
        batch = episodes_from_payload(page)
        episodes.extend(batch)
        if len(page.get("data") or []) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(THROTTLE_SECONDS)
    return sorted(episodes, key=lambda e: e["number"])


def run():
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    top = sorted(catalog, key=lambda a: a.get("popularity") or 0, reverse=True)[:TOP_N]

    out = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            out = json.load(f)

    for i, anime in enumerate(top, 1):
        id_mal = anime.get("idMal")
        if not id_mal or str(id_mal) in out:
            continue
        logger.info("[%d/%d] %s (MAL %s)...", i, len(top), anime.get("title"), id_mal)
        try:
            episodes = fetch_episodes(id_mal)
        except Exception as e:  # a single unreachable work must not lose the run
            logger.warning("Kitsu failed for MAL %s: %s", id_mal, e)
            episodes = []
        if episodes:
            out[str(id_mal)] = episodes
        time.sleep(THROTTLE_SECONDS)

        if i % 25 == 0:  # checkpoint: the run takes ~15 min, do not lose it
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    with_plot = sum(1 for eps in out.values() if any(e["synopsis"] for e in eps))
    logger.info("%d works with episodes, %d with plot summaries.", len(out), with_plot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run()

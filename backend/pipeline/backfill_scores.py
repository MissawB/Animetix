# Fix path for internal imports
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import time  # noqa: E402

from core.utils.security import safe_http_request  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

logger = logging.getLogger("animetix.pipeline.backfill_scores")
logging.basicConfig(level=logging.INFO, format="%(message)s")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

PROCESSED_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "processed")

ANILIST_URL = "https://graphql.anilist.co"
TMDB_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Les notes IGDB des jeux sont déjà stockées sur 0-100 (ex. 96.1) : AniList
# (averageScore, déjà 0-100) est repris tel quel et TMDB (vote_average, 0-10)
# est multiplié par 10 pour que toute la base partage la même échelle.
ANILIST_BATCH = 50
ANILIST_SLEEP = 2.5  # limite dégradée AniList: 30 req/min
TMDB_SLEEP = 0.05

ANILIST_QUERY = """
query ($ids: [Int], $type: MediaType) {
  Page(perPage: 50) {
    media(id_in: $ids, type: $type) {
      id
      averageScore
      meanScore
    }
  }
}
"""


def _load(filename):
    path = os.path.join(PROCESSED_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return path, json.load(f)


def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _anilist_scores(ids, media_type):
    """Retourne {anilist_id: score 0-100} pour un lot d'ids."""
    for attempt in range(3):
        try:
            res = safe_http_request(
                "POST",
                ANILIST_URL,
                json={
                    "query": ANILIST_QUERY,
                    "variables": {"ids": ids, "type": media_type},
                },
                timeout=30,
            )
            if res.status_code == 429:
                wait = int(res.headers.get("Retry-After", 60))
                logger.warning(f"   AniList rate limit, attente {wait}s...")
                time.sleep(wait)
                continue
            res.raise_for_status()
            media = res.json()["data"]["Page"]["media"]
            return {
                m["id"]: m.get("averageScore") or m.get("meanScore")
                for m in media
                if m.get("averageScore") or m.get("meanScore")
            }
        except Exception as e:
            logger.warning(f"   AniList batch en erreur (essai {attempt + 1}/3): {e}")
            time.sleep(5)
    return {}


def backfill_anilist(filename, media_type, force=False):
    path, items = _load(filename)
    todo = [it for it in items if force or not it.get("score")]
    logger.info(f"[{media_type}] {len(todo)}/{len(items)} items sans note")

    updated = 0
    for start in range(0, len(todo), ANILIST_BATCH):
        batch = todo[start : start + ANILIST_BATCH]
        ids = [int(it["id"]) for it in batch if it.get("id")]
        scores = _anilist_scores(ids, media_type)
        for it in batch:
            score = scores.get(int(it["id"])) if it.get("id") else None
            if score:
                it["score"] = float(score)
                updated += 1
        done = min(start + ANILIST_BATCH, len(todo))
        logger.info(f"   {done}/{len(todo)} traités ({updated} notes récupérées)")
        _save(path, items)  # sauvegarde incrémentale: un crash ne perd rien
        time.sleep(ANILIST_SLEEP)

    logger.info(f"[{media_type}] terminé: {updated} notes écrites dans {filename}")


def backfill_tmdb(force=False):
    if not TMDB_API_KEY:
        logger.error("TMDB_API_KEY absent du .env")
        return
    path, items = _load("clean_root_movies.json")
    todo = [it for it in items if force or not it.get("score")]
    logger.info(f"[Movies/TMDB] {len(todo)}/{len(items)} items sans note")

    updated = 0
    for i, it in enumerate(todo):
        endpoint = "movie" if it.get("format") == "MOVIE" else "tv"
        try:
            res = safe_http_request(
                "GET",
                f"{TMDB_URL}/{endpoint}/{it['id']}",
                params={"api_key": TMDB_API_KEY},
                timeout=20,
            )
            if res.status_code == 429:
                time.sleep(10)
                continue
            if res.status_code == 200:
                data = res.json()
                vote_average = data.get("vote_average") or 0
                vote_count = data.get("vote_count") or 0
                # une note fondée sur une poignée de votes n'est pas une note
                if vote_average and vote_count >= 50:
                    it["score"] = round(float(vote_average) * 10, 1)
                    it["vote_count"] = vote_count
                    updated += 1
        except Exception as e:
            logger.warning(f"   TMDB {endpoint}/{it['id']} en erreur: {e}")
        if (i + 1) % 100 == 0:
            logger.info(f"   {i + 1}/{len(todo)} traités ({updated} notes récupérées)")
            _save(path, items)
        time.sleep(TMDB_SLEEP)

    _save(path, items)
    logger.info(
        f"[Movies/TMDB] terminé: {updated} notes écrites dans clean_root_movies.json"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill des notes (score 0-100) dans les clean_root_*.json. "
        "Lancer ensuite `manage.py sync_catalog` pour pousser en base."
    )
    parser.add_argument(
        "--only",
        choices=["anime", "manga", "movies"],
        default=None,
        help="Ne traiter qu'une source (défaut: les trois)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Réécrit aussi les notes déjà présentes",
    )
    args = parser.parse_args()

    if args.only in (None, "anime"):
        backfill_anilist("clean_root_animes.json", "ANIME", force=args.force)
    if args.only in (None, "manga"):
        backfill_anilist("clean_root_mangas.json", "MANGA", force=args.force)
    if args.only in (None, "movies"):
        backfill_tmdb(force=args.force)

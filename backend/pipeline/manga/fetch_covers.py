# Fix path for internal imports
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

from core.utils.security import safe_http_request  # noqa: E402

logger = logging.getLogger("animetix.pipeline." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Racine du repo (PROJECT_ROOT remonte depuis le DOSSIER du module, pas le fichier :
# un dirname de moins atterrissait sur backend/ et le script ne trouvait plus data/).
BASE_DIR = PROJECT_ROOT
INPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "clean_root_mangas.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "manga_covers.json")
# Cache négatif : mangas sans mapping MangaDex ou sans aucune cover ja/fr.
# Sans lui, chaque re-run retente les mêmes échecs (1 appel + 1 s perdus chacun).
FAILURES_FILE = os.path.join(
    BASE_DIR, "data", "processed", "manga_covers_failures.json"
)

MANGADEX_API_URL = "https://api.mangadex.org"
MALSYNC_API_URL = "https://api.malsync.moe/mal/manga"

# Locales jouables : la cover doit être dans une langue qui ne donne pas la réponse.
COVER_LOCALES = ("ja", "fr")
# Taille de page maximale de l'endpoint /cover de MangaDex.
PAGE_SIZE = 100
# Garde-fou anti-boucle si l'API renvoyait un `total` incohérent (100 pages = 10k covers).
MAX_PAGES = 100

# MAL-Sync throttle agressivement : sans backoff, un run à 2 req/s prend un 429
# quasi systématique. Un 429/5xx est TRANSITOIRE — il ne doit jamais être confondu
# avec « ce manga n'existe pas sur MangaDex », sous peine d'empoisonner le cache
# négatif avec des échecs définitifs qui n'en sont pas.
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_RETRIES = 5
BACKOFF_START = 2.0
# Au-delà, l'API nous throttle durablement : on arrête plutôt que de la marteler.
MAX_CONSECUTIVE_TRANSIENT = 8


class TransientAPIError(RuntimeError):
    """Échec réseau/quota récupérable : à retenter, jamais à mettre en cache négatif."""


def _request(method: str, url: str, **kwargs) -> Any:
    """Appel HTTP avec backoff exponentiel sur les statuts récupérables.

    Raises:
        TransientAPIError: si l'API throttle ou tombe au-delà de MAX_RETRIES.
    """
    wait = BACKOFF_START
    last_reason = "unknown"

    for attempt in range(1, MAX_RETRIES + 1):
        response = None
        try:
            response = safe_http_request(method, url, timeout=15, **kwargs)
        except Exception as e:  # timeout, DNS, connexion coupée...
            last_reason = f"{type(e).__name__}: {e}"
        else:
            if response.status_code not in RETRYABLE_STATUS:
                return response
            last_reason = f"HTTP {response.status_code}"

        if attempt == MAX_RETRIES:
            break

        # Le serveur sait mieux que nous combien de temps attendre.
        retry_after = None
        if response is not None:
            try:
                retry_after = float(response.headers.get("Retry-After"))
            except (TypeError, ValueError, AttributeError):
                retry_after = None

        pause = max(retry_after or 0.0, wait)
        logger.warning(
            f"⏳ {last_reason} sur {url} — retry {attempt}/{MAX_RETRIES - 1} dans {pause:.0f}s"
        )
        time.sleep(pause)
        wait *= 2

    raise TransientAPIError(f"{last_reason} après {MAX_RETRIES} tentatives sur {url}")


def get_mangadex_id(mal_id: int) -> str | None:
    """Récupère l'ID MangaDex à partir de l'ID MAL via MAL-Sync.

    Args:
        mal_id: L'identifiant MyAnimeList.

    Returns:
        L'ID MangaDex (UUID), ou None si MAL-Sync ne connaît pas ce manga
        (absence RÉELLE — un throttle lève TransientAPIError à la place).

    Raises:
        TransientAPIError: quota/panne côté MAL-Sync.
    """
    url = f"{MALSYNC_API_URL}/{mal_id}"
    response = _request("GET", url)
    if response.status_code != 200:
        return None

    try:
        data = response.json()
        # Dans MAL-Sync, les sites sont des clés dans un dictionnaire
        mangadex_entries = data.get("Sites", {}).get("Mangadex", {})
        if mangadex_entries:
            # On prend la première entrée (la clé est l'ID MangaDex)
            return list(mangadex_entries.keys())[0]
        return None
    except Exception as e:
        logger.error(f"❌ Error mapping MAL ID {mal_id} to MangaDex: {e}")
        return None


def fetch_covers(mangadex_id: str) -> dict:
    """Récupère **toutes** les covers japonaises et françaises pour un ID MangaDex.

    L'endpoint /cover plafonne à 100 résultats par page : une série longue
    (One Piece, Detective Conan…) dépasse largement ce seuil, d'où la pagination.

    Args:
        mangadex_id: L'UUID MangaDex.

    Returns:
        Un dictionnaire {locale: [{url, volume}, ...]} couvrant tous les volumes.
    """
    covers: dict[str, list[dict[str, Any]]] = {loc: [] for loc in COVER_LOCALES}
    url = f"{MANGADEX_API_URL}/cover"
    offset = 0

    try:
        for _ in range(MAX_PAGES):
            params = {
                "manga[]": [mangadex_id],
                "locales[]": list(COVER_LOCALES),
                "limit": PAGE_SIZE,
                "offset": offset,
            }
            response = _request("GET", url, params=params)
            if response.status_code != 200:
                break

            payload = response.json()
            data = payload.get("data", [])
            for item in data:
                attr = item.get("attributes", {})
                locale = attr.get("locale")
                file_name = attr.get("fileName")

                if locale in covers and file_name:
                    covers[locale].append(
                        {
                            "url": f"https://uploads.mangadex.org/covers/{mangadex_id}/{file_name}",
                            "volume": attr.get("volume"),
                        }
                    )

            offset += len(data)
            # `total` absent (ou page incomplète) => on a tout vu.
            if not data or offset >= payload.get("total", offset):
                break

        return covers
    except TransientAPIError:
        raise  # surtout pas de cache négatif sur un throttle
    except Exception as e:
        logger.error(f"❌ Error fetching covers for MangaDex ID {mangadex_id}: {e}")
        return covers


def fetch_manga_details(mangadex_id: str) -> dict:
    """Récupère l'auteur et les titres alternatifs d'un manga MangaDex.

    Ces champs alimentent l'autocomplétion du Covertest : ils permettent de
    chercher une série par son nom anglais/coréen/arabe, pas seulement par le
    romaji. Sans eux, toute entrée nouvellement ingérée serait introuvable
    autrement que par son titre exact.

    Args:
        mangadex_id: L'UUID MangaDex.

    Returns:
        Un dictionnaire {author, synonyms}. Champs vides si l'appel échoue.
    """
    details: dict[str, Any] = {"author": None, "synonyms": []}
    try:
        url = f"{MANGADEX_API_URL}/manga/{mangadex_id}"
        response = _request("GET", url, params={"includes[]": ["author"]})
        if response.status_code != 200:
            return details

        data = response.json().get("data", {}) or {}
        attributes = data.get("attributes", {}) or {}

        synonyms = []
        for alt in attributes.get("altTitles", []) or []:
            for value in (alt or {}).values():
                if value and value not in synonyms:
                    synonyms.append(value)
        details["synonyms"] = synonyms

        for relation in data.get("relationships", []) or []:
            if relation.get("type") == "author":
                name = (relation.get("attributes") or {}).get("name")
                if name:
                    details["author"] = name
                    break

        return details
    except TransientAPIError:
        raise  # surtout pas de cache négatif sur un throttle
    except Exception as e:
        logger.error(f"❌ Error fetching details for MangaDex ID {mangadex_id}: {e}")
        return details


def _load_json(path: str, default: Any) -> Any:
    """Charge un JSON en tolérant l'absence et la corruption du fichier."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Erreur lors du chargement de {path}: {e}")
        return default


def _save_json(path: str, payload: Any) -> None:
    """Écrit un JSON UTF-8, en créant le dossier parent si besoin."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def run_fetching(
    limit: int | None = None, delay: float = 1.0, retry_failed: bool = False
) -> str:
    """Ingère les covers de MangaDex pour le catalogue manga.

    Reprend là où le précédent run s'est arrêté : les mangas déjà en base et
    ceux du cache négatif ne consomment ni appel réseau ni quota `limit`.

    Args:
        limit: Nombre maximum de mangas **effectivement interrogés** (None = tous).
        delay: Pause entre deux mangas, pour rester sous le rate limit MangaDex.
        retry_failed: Retente les mangas du cache négatif (mapping introuvable
            ou aucune cover ja/fr au run précédent).

    Returns:
        Message de statut.
    """
    if not os.path.exists(INPUT_FILE):
        return f"❌ Input file not found: {INPUT_FILE}"

    mangas = _load_json(INPUT_FILE, [])
    covers_data = _load_json(OUTPUT_FILE, {})
    failures: dict[str, str] = {} if retry_failed else _load_json(FAILURES_FILE, {})

    todo = [
        m
        for m in mangas
        if m.get("idMal")
        and str(m.get("id")) not in covers_data
        and str(m.get("id")) not in failures
    ]
    if limit is not None:
        todo = todo[:limit]

    logger.info(
        f"🚀 Fetching Manga Covers — {len(todo)} à traiter "
        f"({len(covers_data)} déjà en base, {len(failures)} en échec connu)..."
    )

    count = 0
    skipped = 0
    consecutive_transient = 0
    aborted = False

    for index, manga in enumerate(todo, start=1):
        manga_id = str(manga.get("id"))
        logger.info(f"   - [{index}/{len(todo)}] Processing: {manga.get('title')}")

        try:
            md_id = get_mangadex_id(manga["idMal"])
            if not md_id:
                failures[manga_id] = "no_mangadex_mapping"
            else:
                covers = fetch_covers(md_id)
                if any(covers.get(loc) for loc in COVER_LOCALES):
                    details = fetch_manga_details(md_id)
                    covers_data[manga_id] = {
                        "title": manga.get("title"),
                        "mangadex_id": md_id,
                        "covers": covers,
                        "author": details.get("author"),
                        # Les titres alternatifs viennent du catalogue (AniList) ET de
                        # MangaDex : les deux sources se complètent pour l'autocomplétion.
                        "title_english": manga.get("title_english"),
                        "title_native": manga.get("title_native"),
                        "synonyms": details.get("synonyms", []),
                    }
                    count += 1
                else:
                    failures[manga_id] = "no_cover_in_locales"
            consecutive_transient = 0
        except TransientAPIError as e:
            # Le manga n'est PAS en échec : c'est l'API qui flanche. On le laisse
            # hors du cache négatif pour que le prochain run le reprenne.
            skipped += 1
            consecutive_transient += 1
            logger.warning(
                f"⏭️  Reporté (API indisponible) : {manga.get('title')} — {e}"
            )
            if consecutive_transient >= MAX_CONSECUTIVE_TRANSIENT:
                logger.error(
                    f"🛑 Arrêt : {consecutive_transient} échecs transitoires d'affilée. "
                    "L'API nous throttle — relancer plus tard (le run reprendra ici)."
                )
                aborted = True
                break

        time.sleep(delay)  # Respect rate limits

        if count > 0 and count % 10 == 0:
            _save_json(OUTPUT_FILE, covers_data)
            _save_json(FAILURES_FILE, failures)

    _save_json(OUTPUT_FILE, covers_data)
    _save_json(FAILURES_FILE, failures)

    status = (
        f"{'🛑 Aborted' if aborted else '✅ Finished'}! Added covers for {count} mangas. "
        f"Total in DB: {len(covers_data)}. Reportés (API): {skipped}."
    )
    logger.info(status)
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest manga covers from MangaDex.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre max de mangas à interroger (défaut : tout le catalogue).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Pause entre deux mangas, en secondes (défaut : 1.0).",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retente les mangas du cache négatif.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print(run_fetching(args.limit, args.delay, args.retry_failed))

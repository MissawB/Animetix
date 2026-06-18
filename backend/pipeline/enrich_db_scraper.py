# -*- coding: utf-8 -*-
"""
Pipeline d'enrichissement sémantique et de scraping.
Scrape l'API Jikan pour les métadonnées et utilise l'API Gemini pour générer des synopsis français.
"""

import os  # noqa: E402
import sys  # noqa: E402
import argparse  # noqa: E402
import time  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
from core.utils.security import safe_http_request  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# Détection de la racine et configuration des chemins
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PIPELINE_DIR))

# Fix path for internal imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

# Configuration Django
import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
try:
    django.setup()
    from animetix.models import MediaItem  # noqa: E402
except Exception as e:
    import logging
    logger = logging.getLogger("animetix.pipeline")
    logger.warning(f"Django setup warning: {e}. Running in offline JSON mode.")
    MediaItem = None

# Logger
# logging.basicConfig moved to main guard to avoid overriding global logging config
logger = logging.getLogger("animetix.pipeline.enrich_scraper")

# Charger .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Google GenAI setup
try:
    from google import genai  # noqa: E402

    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logger.warning(
        f"Failed to load Google GenAI SDK: {e}. Translations will be simulated."
    )
    gemini_client = None


def fetch_jikan_details(mal_id: str, media_type: str = "anime") -> dict:
    """Récupère les détails depuis Jikan API avec respect du rate limit (retry si 429)."""
    type_path = "anime" if media_type.lower() == "anime" else "manga"
    url = f"https://api.jikan.moe/v4/{type_path}/{mal_id}/full"

    try:
        response = safe_http_request("GET", url, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", {})
        elif response.status_code == 429:
            logger.warning(
                f"⚠️ Rate limit Jikan pour {media_type} MAL ID {mal_id}. Pause de 10s..."
            )
            time.sleep(10)
            return fetch_jikan_details(mal_id, media_type)
        else:
            logger.debug(
                f"ℹ️ Aucun détail trouvé pour {media_type} {mal_id} (Code: {response.status_code})"
            )
            return {}
    except Exception as e:
        logger.error(f"❌ Erreur Jikan API pour {media_type} {mal_id}: {e}")
        return {}


def translate_synopsis_via_gemini(title: str, english_synopsis: str) -> str:
    """Traduit et enrichit le synopsis en français avec Gemini."""
    if not english_synopsis:
        return ""

    if not gemini_client:
        logger.info(f"🧪 [Simulation] Traduction pour '{title}'")
        return f"[TRADUCTION SIMULÉE] {english_synopsis[:100]}..."

    prompt = f"""Tu es un traducteur et scénariste littéraire expert en japanimation, mangas et culture geek.
Traduis fidèlement, avec style, richesse et de façon fluide le synopsis/description suivant en français.
Conserve le ton mystérieux, dramatique ou d'action de l'œuvre d'origine. 
N'ajoute absolument aucun commentaire ou métadonnée, retourne UNIQUEMENT la traduction fluide et propre en français.

Titre de l'œuvre : {title}
Synopsis en anglais :
{english_synopsis}
"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Erreur de génération Gemini pour '{title}': {e}")
        return ""


def update_json_file(file_path: str, external_id: str, updates: dict):
    """Met à jour un élément spécifique dans le fichier JSON pour rester synchronisé."""
    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        updated = False
        for item in items:
            # Vérifier l'ID par rapport à id, idMal, mal_id
            item_id = str(item.get("id", ""))
            item_id_mal = str(item.get("idMal", ""))
            item_mal_id = str(item.get("mal_id", ""))

            if external_id in (item_id, item_id_mal, item_mal_id):
                item.update(updates)
                updated = True
                break

        if updated:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            logger.debug(
                f"📝 JSON mis à jour pour {external_id} dans {os.path.basename(file_path)}"
            )
    except Exception as e:
        logger.error(f"❌ Erreur d'écriture JSON pour {file_path}: {e}")


def run_enrichment(limit: int = 20, dry_run: bool = False):
    """Exécute l'enrichissement sémantique sur la base de données SQLite et les fichiers JSON."""
    logger.info(
        f"🚀 Lancement de l'enrichisseur sémantique (Limite: {limit}, Simulation: {dry_run})"
    )

    if not MediaItem:
        logger.error(
            "❌ Django MediaItem n'est pas disponible. Impossible de procéder."
        )
        return

    # On sélectionne les items Anime/Manga qui n'ont pas de synopsis en français
    items_to_enrich = MediaItem.objects.filter(
        media_type__in=["Anime", "Manga"], synopsis_fr__isnull=True
    ) | MediaItem.objects.filter(media_type__in=["Anime", "Manga"], synopsis_fr="")

    # On filtre les items qui ont au moins une description anglaise ou un synopsis anglais
    items_to_enrich = items_to_enrich.exclude(description="").order_by("-popularity")[
        :limit
    ]

    total_count = len(items_to_enrich)
    logger.info(
        f"📊 Trouvé {total_count} items éligibles pour l'enrichissement sémantique."
    )

    if total_count == 0:
        logger.info(
            "ℹ️ Aucun élément à enrichir. La base de données est déjà complète !"
        )
        return

    processed_count = 0

    # Chemins des JSON sources
    anime_json_path = os.path.join(
        PROJECT_ROOT, "data", "processed", "clean_root_animes.json"
    )
    manga_json_path = os.path.join(
        PROJECT_ROOT, "data", "processed", "clean_root_mangas.json"
    )

    for item in items_to_enrich:
        logger.info(
            f"🔮 [{processed_count + 1}/{total_count}] Enrichissement de '{item.title}' (ID: {item.external_id})"
        )

        # 1. Obtenir la description anglaise
        desc_en = item.synopsis_en or item.description

        # 2. Scraping complémentaire Jikan si nécessaire
        jikan_data = {}
        if item.media_type in ["Anime", "Manga"] and item.external_id.isdigit():
            # Si on n'a pas encore de themes ou background dans les metadatas
            if (
                not item.metadata
                or "themes" not in item.metadata
                or "background" not in item.metadata
            ):
                logger.info(
                    f"   🕸️ Récupération des infos Jikan pour MAL ID {item.external_id}..."
                )
                jikan_data = fetch_jikan_details(item.external_id, item.media_type)
                time.sleep(1.2)  # Jikan limit friendly

        # 3. Génération/Traduction du synopsis en français
        synopsis_fr = translate_synopsis_via_gemini(item.title, desc_en)

        if dry_run:
            logger.info(f"🧪 [Dry-Run] Traduction FR : {synopsis_fr[:120]}...")
            if jikan_data:
                logger.info(
                    f"🧪 [Dry-Run] Thèmes trouvés : {jikan_data.get('themes', [])}"
                )
            processed_count += 1
            continue

        # 4. Enregistrement en base de données
        updates = {}
        if synopsis_fr:
            item.synopsis_fr = synopsis_fr
            updates["synopsis_fr"] = synopsis_fr

        if not item.synopsis_en and desc_en:
            item.synopsis_en = desc_en
            updates["synopsis_en"] = desc_en

        # Enrichissement métadonnées depuis Jikan
        if jikan_data:
            metadata = item.metadata or {}

            # Thèmes
            themes = [
                t.get("name") for t in jikan_data.get("themes", []) if t.get("name")
            ]
            if themes:
                metadata["themes"] = list(set(metadata.get("themes", []) + themes))

            # Background
            bg = jikan_data.get("background")
            if bg:
                metadata["background"] = bg

            # Titres alternatifs
            titles = [
                t.get("title") for t in jikan_data.get("titles", []) if t.get("title")
            ]
            if titles:
                metadata["alternative_titles"] = list(
                    set(metadata.get("alternative_titles", []) + titles)
                )
                item.alternative_titles = list(set(item.alternative_titles + titles))
                updates["alternative_titles"] = item.alternative_titles

            # Recommandations
            recs = jikan_data.get("recommendations", [])
            if recs:
                clean_recs = []
                for r in recs[:5]:
                    entry = r.get("entry", {})
                    clean_recs.append(
                        {
                            "title": entry.get("title", "Unknown"),
                            "content": r.get("content", ""),
                        }
                    )
                metadata["recommendations_lore"] = clean_recs

            item.metadata = metadata
            updates["metadata"] = metadata

        item.save()
        logger.info("   ✅ Base SQLite mise à jour avec succès.")

        # 5. Synchronisation des JSON sources pour conserver la consistance du pipeline
        json_file = anime_json_path if item.media_type == "Anime" else manga_json_path
        update_json_file(json_file, item.external_id, updates)

        # 6. Propagation optionnelle dans le graphe Neo4j
        try:
            from pipeline.neo4j_client import neo4j_manager  # noqa: E402

            if neo4j_manager and neo4j_manager.driver:
                with neo4j_manager.driver.session() as session:
                    session.run(
                        "MATCH (m:Media {id: $id}) SET m.synopsis_fr = $synopsis_fr",
                        id=item.external_id,
                        synopsis_fr=synopsis_fr,
                    )
                logger.info("   🕸️ Graphe Neo4j mis à jour.")
        except Exception as e:
            logger.debug(f"Neo4j sync skipped or failed: {e}")

        processed_count += 1

    logger.info(f"✨ Fin de l'enrichissement. {processed_count} éléments enrichis.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape et enrichit le catalogue avec des synopsis français et infos complexes."
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Nombre max d'œuvres à enrichir."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule l'indexation sans écrire en base.",
    )
    args = parser.parse_args()

    run_enrichment(limit=args.limit, dry_run=args.dry_run)

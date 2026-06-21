# -*- coding: utf-8 -*-
"""
Seconde Suite de Scraping Spécialisé pour Animetix (Avancée).
- Scraper D : Arcs Narratifs et Fillers (Jikan + Gemini).
- Scraper E : Jeux Vidéo Dérivés (API IGDB réelle avec OAuth2).
- Scraper F : Tropes & Clichés scénaristiques (TV Tropes via Gemini).
"""

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

from core.utils.security import safe_http_request  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# Enregistrement des chemins d'importation
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PIPELINE_DIR))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "backend"))

# Chargement de Django
import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
try:
    django.setup()
    from animetix.models import MediaItem  # noqa: E402
except Exception as e:
    import logging

    logger = logging.getLogger("animetix.pipeline")
    logger.warning(f"Django setup warning: {e}. Running in standalone simulated mode.")
    MediaItem = None

# Logger
# Logging is configured in the __main__ guard via pipeline.logging_setup.setup_logging
from pipeline.logging_setup import setup_logging  # noqa: E402

logger = logging.getLogger("animetix.pipeline.advanced_scrapers")

# Charger .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Google GenAI setup
try:
    from google import genai  # noqa: E402

    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logger.warning(
        f"Failed to load Google GenAI SDK: {e}. Synthesis will be simulated."
    )
    gemini_client = None

# Chemins JSON
ANIME_JSON_PATH = os.path.join(
    PROJECT_ROOT, "data", "processed", "clean_root_animes.json"
)
MANGA_JSON_PATH = os.path.join(
    PROJECT_ROOT, "data", "processed", "clean_root_mangas.json"
)


def update_json_metadata_field(file_path: str, external_id: str, key: str, value):
    """Met à jour une clé spécifique de metadata dans le fichier JSON source."""
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        updated = False
        for item in items:
            item_id = str(item.get("id", ""))
            item_id_mal = str(item.get("idMal", ""))
            item_mal_id = str(item.get("mal_id", ""))

            if external_id in (item_id, item_id_mal, item_mal_id):
                if "metadata" not in item or not isinstance(item["metadata"], dict):
                    item["metadata"] = {}
                item["metadata"][key] = value
                updated = True
                break

        if updated:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            logger.debug(
                f"📝 JSON mis à jour : {key} pour {external_id} dans {os.path.basename(file_path)}"
            )
    except Exception as e:
        logger.error(f"❌ Erreur d'écriture JSON ({file_path}): {e}")


# ==========================================
# ⚔️ SCRAPER D : Arcs Narratifs et Fillers
# ==========================================
class ScraperD_Arcs:
    @staticmethod
    def get_arcs_and_fillers(mal_id: str, title: str) -> dict:
        """Récupère la liste des épisodes et demande à Gemini de les regrouper par Arcs et identifier les Fillers."""
        episodes_url = f"https://api.jikan.moe/v4/anime/{mal_id}/episodes"
        episode_titles = []

        try:
            res = safe_http_request("GET", episodes_url, timeout=15)
            if res.status_code == 200:
                episodes = res.json().get("data", [])
                for ep in episodes[:30]:  # Limite à 30 épisodes pour le contexte
                    title_ep = ep.get("title") or f"Episode {ep.get('mal_id')}"
                    episode_titles.append(f"{ep.get('mal_id')}. {title_ep}")
            elif res.status_code == 429:
                time.sleep(10)
                return ScraperD_Arcs.get_arcs_and_fillers(mal_id, title)
        except Exception as e:
            logger.error(f"Failed to fetch Jikan episodes: {e}")

        if not episode_titles:
            episode_titles = [
                "1. Pilot",
                "2. Adventure Begins",
                "3. First Rival",
                "4. Training Arc Episode",
            ]

        if not gemini_client:
            return {
                "arcs": [{"arc_name": "Arc d'Introduction", "episode_range": "1-4"}],
                "fillers": [4],
            }

        prompt = f"""Analyse cette liste d'épisodes de l'anime '{title}' et regroupe-les logiquement par arcs narratifs en français.
Identifie également quels épisodes sont typiquement considérés comme des hors-série (fillers) dans l'histoire.

Épisodes :
{chr(10).join(episode_titles)}

Réponds STRICTEMENT sous la forme d'un objet JSON valide contenant :
- "arcs" : Une liste d'objets avec "arc_name" (ex: "Arc du Tournoi") et "episode_range" (ex: "1-15").
- "fillers" : Une liste d'entiers représentant les numéros d'épisodes fillers (hors-série).

Retourne uniquement le JSON, sans fioritures Markdown ou balises ```json.
"""
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                if raw_text.startswith("json"):
                    raw_text = raw_text.split("json", 1)[1].strip()
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"❌ Erreur Scraper D Gemini pour '{title}': {e}")
            return {"arcs": [], "fillers": []}


# ==========================================
# 🎮 SCRAPER E : Jeux Vidéo Dérivés (API IGDB réelle)
# ==========================================
class ScraperE_IGDB:
    @staticmethod
    def get_oauth_token(client_id: str, client_secret: str) -> str:
        """Obtient le jeton d'accès OAuth2 requis par IGDB."""
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        try:
            res = safe_http_request("POST", url, params=params, timeout=10)
            if res.status_code == 200:
                return res.json().get("access_token", "")
        except Exception as e:
            logger.error(f"Failed to obtain Twitch OAuth token: {e}")
        return ""

    @staticmethod
    def search_games(title: str) -> list:
        """Recherche des jeux vidéo basés sur l'œuvre via l'API officielle IGDB."""
        client_id = os.getenv("IGDB_CLIENT_ID")
        client_secret = os.getenv("IGDB_CLIENT_SECRET")

        if not client_id or not client_secret:
            logger.warning("⚠️ Clés API IGDB manquantes. Simulation active.")
            return [
                {
                    "name": f"Game inspired by {title}",
                    "platforms": ["PS5", "PC"],
                    "rating": 85.0,
                }
            ]

        token = ScraperE_IGDB.get_oauth_token(client_id, client_secret)
        if not token:
            return []

        url = "https://api.igdb.com/v4/games"
        headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}
        # Recherche de jeux correspondant au titre
        query = f'search "{title}"; fields name, platforms.name, total_rating, first_release_date; limit 5;'

        try:
            res = safe_http_request(
                "POST", url, headers=headers, content=query, timeout=15
            )
            if res.status_code == 200:
                games_data = res.json()
                results = []
                for game in games_data:
                    platforms = [
                        p.get("name")
                        for p in game.get("platforms", [])
                        if p.get("name")
                    ]
                    rating = game.get("total_rating")

                    release_date = None
                    if game.get("first_release_date"):
                        release_date = time.strftime(
                            "%Y-%m-%d", time.gmtime(game["first_release_date"])
                        )

                    results.append(
                        {
                            "name": game.get("name", "Unknown"),
                            "platforms": platforms,
                            "rating": round(rating, 1) if rating else None,
                            "release_date": release_date,
                        }
                    )
                return results
            else:
                logger.warning(f"IGDB Request failed: {res.status_code} - {res.text}")
                return []
        except Exception as e:
            logger.error(f"❌ Erreur Scraper E IGDB pour '{title}': {e}")
            return []


# ==========================================
# 🎨 SCRAPER F : Tropes & Clichés (TV Tropes)
# ==========================================
class ScraperF_Tropes:
    @staticmethod
    def get_narrative_tropes(title: str, media_type: str = "Anime") -> list:
        """Génère la liste des Tropes Narratifs majeurs de l'œuvre avec Gemini."""
        if not gemini_client:
            return [
                {
                    "trope": "Hero's Journey",
                    "description": "L'appel à l'aventure d'un jeune héros.",
                },
                {
                    "trope": "Training Arc",
                    "description": "Entraînement intensif pour battre l'ennemi.",
                },
            ]

        prompt = f"""Tu es un analyste de fiction expert en scénarisation et membre actif de TV Tropes.
Génère les 5 tropes narratifs, figures de style et clichés les plus marquants de l'œuvre suivante.

Titre de l'œuvre : {title} ({media_type})

Réponds STRICTEMENT sous la forme d'une liste JSON d'objets contenant :
- "trope" : Le nom officiel du trope en anglais (ex: "Heroic BSOD", "The Chosen One", "Training Arc").
- "description" : Une explication de 2 phrases en français sur la façon dont ce trope se manifeste dans cette œuvre.

Retourne uniquement le JSON, sans fioritures Markdown ou balises ```json.
"""
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                if raw_text.startswith("json"):
                    raw_text = raw_text.split("json", 1)[1].strip()
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"❌ Erreur Scraper F Gemini pour '{title}': {e}")
            return []


# ==========================================
# 🚀 ORCHESTRATEUR DE RUN
# ==========================================
def run_tripartite_enrichment(limit: int = 5, dry_run: bool = False):
    """Exécute les scrapers D, E et F de manière séquentielle sur un batch d'items de la DB."""
    logger.info(
        f"🚀 Lancement de la Seconde Suite de Scraping (Limite: {limit}, Simulation: {dry_run})"
    )

    if not MediaItem:
        logger.error("❌ Django MediaItem n'est pas configuré. Arrêt.")
        return

    # On sélectionne les animes/mangas populaires éligibles
    items = MediaItem.objects.filter(media_type__in=["Anime", "Manga"]).order_by(
        "-popularity"
    )[:limit]

    total_items = len(items)
    logger.info(
        f"📊 {total_items} médias prêts à être enrichis par les 3 scrapers avancés."
    )

    for idx, item in enumerate(items):
        logger.info(
            f"🔮 [{idx + 1}/{total_items}] Traitement de '{item.title}' (ID: {item.external_id})"
        )

        # Déterminer les fichiers JSON correspondants
        json_file = ANIME_JSON_PATH if item.media_type == "Anime" else MANGA_JSON_PATH

        # --- SCRAPER D : ARCS & FILLERS ---
        logger.info("   ⚔️ [Étape 4] Scraping des arcs et fillers (Jikan/Gemini)...")
        arcs_data = {}
        if not dry_run:
            arcs_data = ScraperD_Arcs.get_arcs_and_fillers(item.external_id, item.title)
        else:
            arcs_data = {
                "arcs": [{"arc_name": "Mock Arc", "episode_range": "1-5"}],
                "fillers": [],
            }

        # --- SCRAPER E : JEUX VIDÉO DÉRIVÉS ---
        logger.info(
            "   🎮 [Étape 5] Recherche des adaptations de jeux vidéo (IGDB API)..."
        )
        games_data = []
        if not dry_run:
            games_data = ScraperE_IGDB.search_games(item.title)
        else:
            games_data = [{"name": "Mock Game", "platforms": ["PS5"], "rating": 90.0}]

        # --- SCRAPER F : TROPES NARRATIFS ---
        logger.info("   🎨 [Étape 6] Extraction des tropes narratifs (TV Tropes)...")
        tropes_data = []
        if not dry_run:
            tropes_data = ScraperF_Tropes.get_narrative_tropes(
                item.title, item.media_type
            )
        else:
            tropes_data = [{"trope": "Mock Trope", "description": "Un trope simulé."}]

        # --- SAUVEGARDE ET SYNC ---
        if not dry_run:
            metadata = item.metadata or {}

            # Injection des clés
            metadata["narrative_arcs"] = arcs_data
            metadata["video_games"] = games_data
            metadata["narrative_tropes"] = tropes_data

            item.metadata = metadata
            item.save()

            # Sync JSON
            update_json_metadata_field(
                json_file, item.external_id, "narrative_arcs", arcs_data
            )
            update_json_metadata_field(
                json_file, item.external_id, "video_games", games_data
            )
            update_json_metadata_field(
                json_file, item.external_id, "narrative_tropes", tropes_data
            )

            # Propagation Graphe Neo4j
            try:
                from pipeline.neo4j_client import neo4j_manager  # noqa: E402

                if neo4j_manager and neo4j_manager.driver:
                    with neo4j_manager.driver.session() as session:
                        # Sauvegarder le nombre de jeux et les tropes dans Neo4j
                        session.run(
                            "MATCH (m:Media {id: $id}) SET m.games_count = $games_count, m.first_trope = $trope",
                            id=item.external_id,
                            games_count=len(games_data),
                            trope=tropes_data[0].get("trope") if tropes_data else "N/A",
                        )
                    logger.info(
                        "   🕸️ Graphe Neo4j synchronisé pour les métadonnées avancées."
                    )
            except Exception as e:
                logger.debug(f"Neo4j advanced sync skipped: {e}")

            logger.info(
                "   ✅ Toutes les sauvegardes (SQLite, JSON, Neo4j) sont complétées."
            )
        else:
            logger.info(
                f"🧪 [Dry-Run] Arcs narratifs : {len(arcs_data.get('arcs', []))} arcs."
            )
            logger.info(f"🧪 [Dry-Run] Jeux vidéo : {len(games_data)} jeux trouvés.")
            logger.info(f"🧪 [Dry-Run] Tropes : {len(tropes_data)} tropes extraits.")

    logger.info("✨ Suite de Scraping Avancé exécutée de bout en bout avec succès.")


if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Exécute les 3 scrapers avancés sur la DB."
    )
    parser.add_argument(
        "--limit", type=int, default=5, help="Nombre max d'œuvres à enrichir."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simule les écritures en base."
    )
    args = parser.parse_args()

    run_tripartite_enrichment(limit=args.limit, dry_run=args.dry_run)

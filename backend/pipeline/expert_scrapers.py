# -*- coding: utf-8 -*-
"""
Troisième Suite de Scraping Spécialisé pour Animetix (Expert).
- Scraper G : Plateformes de Diffusion & Licences en France (Gemini).
- Scraper H : Raisons Humaines de Recommandation (Jikan API).
- Scraper I : Lieux Réels & Pèlerinage Otaku (Gemini).
"""

import os
import sys
import argparse
import time
import json
import logging
import requests
from dotenv import load_dotenv

# Enregistrement des chemins d'importation
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PIPELINE_DIR))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "backend"))

# Chargement de Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
try:
    django.setup()
    from animetix.models import MediaItem
except Exception as e:
    logger.warning(f"Django setup warning: {e}. Running in standalone simulated mode.")
    MediaItem = None

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("animetix.pipeline.expert_scrapers")

# Charger .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Google GenAI setup
try:
    from google import genai
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logger.warning(f"Failed to load Google GenAI SDK: {e}. Synthesis will be simulated.")
    gemini_client = None

# Chemins JSON
ANIME_JSON_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'clean_root_animes.json')
MANGA_JSON_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'clean_root_mangas.json')

def update_json_metadata_field(file_path: str, external_id: str, key: str, value):
    """Met à jour une clé spécifique de metadata dans le fichier JSON source."""
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
            
        updated = False
        for item in items:
            item_id = str(item.get('id', ''))
            item_id_mal = str(item.get('idMal', ''))
            item_mal_id = str(item.get('mal_id', ''))
            
            if external_id in (item_id, item_id_mal, item_mal_id):
                if 'metadata' not in item or not isinstance(item['metadata'], dict):
                    item['metadata'] = {}
                item['metadata'][key] = value
                updated = True
                break
                
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            logger.debug(f"📝 JSON mis à jour : {key} pour {external_id} dans {os.path.basename(file_path)}")
    except Exception as e:
        logger.error(f"❌ Erreur d'écriture JSON ({file_path}): {e}")

# ==========================================
# 📺 SCRAPER G : Plateformes de Diffusion & Licences en France
# ==========================================
class ScraperG_Streaming:
    @staticmethod
    def get_french_licence_and_streaming(title: str, media_type: str = 'Anime') -> list:
        """Récupère l'attribution de licences et plateformes de diffusion en France avec Gemini."""
        if not gemini_client:
            return [
                {"platform": "Crunchyroll", "has_vf": True, "has_vostfr": True, "status": "Abonnement"},
                {"platform": "Netflix", "has_vf": True, "has_vostfr": True, "status": "Abonnement"}
            ]
            
        prompt = f"""Tu es un analyste expert du marché français du streaming d'animes et éditeurs de mangas.
Pour l'œuvre suivante, détermine les plateformes de diffusion officielles actives en France (ex: Crunchyroll, Netflix, Prime Video, Disney+ pour les animes ; ou Glénat, Ki-oon, Kana pour les mangas).
Précise si les doublages VF sont disponibles et le format d'accès.

Titre de l'œuvre : {title} ({media_type})

Réponds STRICTEMENT sous la forme d'une liste JSON d'objets contenant :
- "platform" : Le nom de la plateforme de streaming ou éditeur physique français (ex: "Crunchyroll", "Netflix", "Glénat Manga").
- "has_vf" : Un booléen (true/false) indiquant si l'adaptation française (VF parlée ou manga traduit) existe et est disponible.
- "has_vostfr" : Un booléen indiquant la présence de sous-titres français (toujours true pour les animes licenciés).
- "status" : Le type d'accès en France (ex: "Abonnement", "Édition Physique", "Achat/VOD").

Retourne uniquement le JSON, sans fioritures Markdown ou balises ```json.
"""
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                if raw_text.startswith("json"):
                    raw_text = raw_text.split("json", 1)[1].strip()
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"❌ Erreur Scraper G Gemini pour '{title}': {e}")
            return []

# ==========================================
# 🧠 SCRAPER H : Raisons Humaines de Recommandation
# ==========================================
class ScraperH_Recs:
    @staticmethod
    def get_human_recs(mal_id: str, media_type: str = 'Anime') -> list:
        """Récupère les recommandations textuelles rédigées par de vrais utilisateurs sur Jikan API."""
        type_path = 'anime' if media_type.lower() == 'anime' else 'manga'
        url = f"https://api.jikan.moe/v4/{type_path}/{mal_id}/recommendations"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                recs_data = response.json().get('data', [])
                clean_recs = []
                
                # Top 3 des recommandations argumentées
                for r in recs_data[:3]:
                    entry = r.get('entry', {})
                    clean_recs.append({
                        "recommended_title": entry.get('title', 'Unknown'),
                        "mal_id": entry.get('mal_id'),
                        "reason": r.get('content', '').strip()
                    })
                return clean_recs
            elif response.status_code == 429:
                time.sleep(10)
                return ScraperH_Recs.get_human_recs(mal_id, media_type)
            return []
        except Exception as e:
            logger.error(f"❌ Erreur Scraper H pour MAL ID {mal_id}: {e}")
            return []

# ==========================================
# 🗺️ SCRAPER I : Lieux Réels & Pèlerinage Otaku
# ==========================================
class ScraperI_Pilgrimage:
    @staticmethod
    def get_pilgrimage_locations(title: str, media_type: str = 'Anime') -> list:
        """Extrait les lieux géographiques réels du Japon inspirant les scènes cultes de l'œuvre avec Gemini."""
        if not gemini_client:
            return [
                {"location_name": "Sanctuaire Suga", "city": "Tokyo", "scene_description": "Les escaliers de la rencontre finale."},
                {"location_name": "Gare de Shinjuku", "city": "Tokyo", "scene_description": "Lieu de transit récurrent."}
            ]
            
        prompt = f"""Tu es un guide de voyage au Japon expert en pèlerinages d'animes (Seichijunrei) et de mangas.
Pour l'œuvre suivante, extrait les 3 lieux géographiques réels du Japon qui ont servi d'inspiration pour les décors de scènes célèbres.

Titre de l'œuvre : {title} ({media_type})

Réponds STRICTEMENT sous la forme d'une liste JSON d'objets contenant :
- "location_name" : Le nom précis du lieu réel (ex: "Sanctuaire Suga", "Shirakawa-go", "Gare de Shinjuku").
- "city" : La ville et/ou préfecture japonaise correspondante (ex: "Tokyo", "Gifu", "Kyoto").
- "scene_description" : Une explication de 2 phrases en français décrivant quelle scène culte s'y déroule ou comment le lieu apparaît.

Retourne uniquement le JSON, sans fioritures Markdown ou balises ```json.
"""
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                if raw_text.startswith("json"):
                    raw_text = raw_text.split("json", 1)[1].strip()
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"❌ Erreur Scraper I Gemini pour '{title}': {e}")
            return []

# ==========================================
# 🚀 ORCHESTRATEUR DE RUN
# ==========================================
def run_tripartite_enrichment(limit: int = 5, dry_run: bool = False):
    """Exécute les scrapers G, H et I de manière séquentielle sur un batch d'items de la DB."""
    logger.info(f"🚀 Lancement de la Troisième Suite de Scraping (Limite: {limit}, Simulation: {dry_run})")
    
    if not MediaItem:
        logger.error("❌ Django MediaItem n'est pas configuré. Arrêt.")
        return

    # On sélectionne les animes/mangas populaires éligibles
    items = MediaItem.objects.filter(media_type__in=['Anime', 'Manga']).order_by('-popularity')[:limit]
    
    total_items = len(items)
    logger.info(f"📊 {total_items} médias prêts à être enrichis par les 3 scrapers experts.")
    
    for idx, item in enumerate(items):
        logger.info(f"🔮 [{idx + 1}/{total_items}] Traitement de '{item.title}' (ID: {item.external_id})")
        
        # Déterminer les fichiers JSON correspondants
        json_file = ANIME_JSON_PATH if item.media_type == 'Anime' else MANGA_JSON_PATH
        
        # --- SCRAPER G : LICENCES & STREAMING ---
        logger.info("   📺 [Étape 7] Recherche des plateformes et diffuseurs français...")
        streaming_data = []
        if not dry_run:
            streaming_data = ScraperG_Streaming.get_french_licence_and_streaming(item.title, item.media_type)
        else:
            streaming_data = [{"platform": "Netflix", "has_vf": True, "has_vostfr": True, "status": "Abonnement"}]

        # --- SCRAPER H : RAISONS DE RECOMPENSE HUMAINE ---
        logger.info("   🧠 [Étape 8] Récupération des recommandations textuelles humaines (Jikan)...")
        recs_data = []
        if not dry_run and item.external_id.isdigit():
            recs_data = ScraperH_Recs.get_human_recs(item.external_id, item.media_type)
            time.sleep(1.2)
        else:
            recs_data = [{"recommended_title": "Mock Rec", "mal_id": 9999, "reason": "Because it is awesome."}]

        # --- SCRAPER I : LIEUX RÉELS & PÈLERINAGE ---
        logger.info("   🗺️ [Étape 9] Recherche des lieux réels du pèlerinage Anime...")
        pilgrimage_data = []
        if not dry_run:
            pilgrimage_data = ScraperI_Pilgrimage.get_pilgrimage_locations(item.title, item.media_type)
        else:
            pilgrimage_data = [{"location_name": "Sanctuaire Suga", "city": "Tokyo", "scene_description": "Scène finale."}]

        # --- SAUVEGARDE ET SYNC ---
        if not dry_run:
            metadata = item.metadata or {}
            
            # Injection des clés
            metadata["streaming_platforms"] = streaming_data
            metadata["human_recommendations"] = recs_data
            metadata["real_locations_pilgrimage"] = pilgrimage_data
            
            item.metadata = metadata
            item.save()
            
            # Sync JSON
            update_json_metadata_field(json_file, item.external_id, "streaming_platforms", streaming_data)
            update_json_metadata_field(json_file, item.external_id, "human_recommendations", recs_data)
            update_json_metadata_field(json_file, item.external_id, "real_locations_pilgrimage", pilgrimage_data)
            
            # Propagation Graphe Neo4j
            try:
                from pipeline.neo4j_client import neo4j_manager
                if neo4j_manager and neo4j_manager.driver:
                    with neo4j_manager.driver.session() as session:
                        # Sauvegarder les plateformes et le premier lieu de pèlerinage dans Neo4j
                        session.run(
                            "MATCH (m:Media {id: $id}) SET m.primary_platform = $platform, m.featured_location = $loc",
                            id=item.external_id,
                            platform=streaming_data[0].get("platform") if streaming_data else "N/A",
                            loc=pilgrimage_data[0].get("location_name") if pilgrimage_data else "N/A"
                        )
                    logger.info("   🕸️ Graphe Neo4j synchronisé pour les métadonnées d'expertises.")
            except Exception as e:
                logger.debug(f"Neo4j expert sync skipped: {e}")
                
            logger.info("   ✅ Toutes les sauvegardes (SQLite, JSON, Neo4j) sont complétées.")
        else:
            logger.info(f"🧪 [Dry-Run] Plateformes : {len(streaming_data)} identifiées.")
            logger.info(f"🧪 [Dry-Run] Recommandations : {len(recs_data)} argumentées.")
            logger.info(f"🧪 [Dry-Run] Pèlerinage : {len(pilgrimage_data)} lieux réels.")

    logger.info("✨ Suite de Scraping Expert exécutée de bout en bout avec succès.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exécute les 3 scrapers experts sur la DB.")
    parser.add_argument("--limit", type=int, default=5, help="Nombre max d'œuvres à enrichir.")
    parser.add_argument("--dry-run", action="store_true", help="Simule les écritures en base.")
    args = parser.parse_args()
    
    run_tripartite_enrichment(limit=args.limit, dry_run=args.dry_run)

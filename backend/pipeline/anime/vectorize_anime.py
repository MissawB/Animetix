import argparse
import json
import logging
import os
import sys
from io import BytesIO

from PIL import Image

# Setup logging
logger = logging.getLogger("animetix." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# backend/pipeline/anime/<ce fichier> : trois dirname remontent à backend/, pas à la
# racine. `core`/`animetix` s'importent depuis backend/ et backend/api ; les données
# vivent à la racine du dépôt (PROJECT_ROOT), un niveau au-dessus de BACKEND_DIR.
BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
# insert(0), pas append : un paquet tiers nommé `pipeline` est installé dans
# site-packages et masque `backend/pipeline` si notre racine passe en queue de
# sys.path -- `import pipeline.vector_client` échouait alors sur le mauvais paquet.
sys.path.insert(0, os.path.join(BACKEND_DIR, "api"))
sys.path.insert(0, BACKEND_DIR)
from core.utils.security import safe_http_request  # noqa: E402

INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "clean_root_animes.json")


# Initialisation différée
def get_repo():
    # Le conteneur est imbriqué depuis un moment : le dépôt vit sous `persistence`,
    # plus à la racine. Ce script demandait encore `container.repository` et mourait
    # sur AttributeError — il n'avait donc jamais tourné depuis ce refactor.
    from animetix.containers import get_container  # noqa: E402

    return get_container().persistence.repository()


def get_pipeline_resources():
    from pipeline.models_registry import models_registry  # noqa: E402
    from pipeline.neo4j_client import neo4j_manager  # noqa: E402

    return models_registry, neo4j_manager


BATCH_SIZE = 32


def run_vectorization(vector_res=None, neo4j_res=None, limit=None):
    """
    Pipeline de vectorisation Multimodale avec support Matryoshka (MRL).

    ``limit`` caps the number of catalog items processed (e.g. for a quick
    smoke run); ``None`` (the default) processes the entire catalog.
    """
    repo = get_repo()
    models_registry, neo4j_manager = get_pipeline_resources()

    logger.info("🚀 Starting SOTA 2026 Multimodal Vectorization (MRL Enabled)...")

    if not os.path.exists(INPUT_FILE):
        logger.error(f"❌ Error: Input file {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    # Le modèle de texte est la raison d'être du script : s'il ne charge pas, on
    # s'arrête. Le modèle de vision n'alimente qu'une collection secondaire —
    # perdre les vecteurs visuels ne doit pas coûter les vecteurs thématiques.
    text_model = models_registry.text_model
    try:
        vision_model = models_registry.vision_model
    except Exception as e:
        logger.warning(f"⚠️ Vision model unavailable ({e}) — text vectors only.")
        vision_model = None

    # On ne traite que les items non encore indexés (simulation simplifiée)
    new_items = items if limit is None else items[:limit]

    for i in range(0, len(new_items), BATCH_SIZE):
        batch = new_items[i : i + BATCH_SIZE]

        # --- PHASE 1 : TEXTE (Jina-v3 avec Matryoshka) ---
        # On génère des vecteurs de dimension 1024, optimisés MRL
        descriptions = [item.get("description", "") for item in batch]
        t_embeddings = text_model.encode(descriptions, convert_to_numpy=True)

        # --- PHASE 2 : VISION (SigLIP) ---
        v_embeddings = []
        for item in batch:
            img_url = item.get("image")
            try:
                if img_url and vision_model is not None:
                    response = safe_http_request("GET", img_url, timeout=10)
                    img = Image.open(BytesIO(response.content)).convert("RGB")
                    v_emb = vision_model.encode(img, convert_to_numpy=True)
                    v_embeddings.append(v_emb.tolist())
                else:
                    v_embeddings.append(None)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch or encode image for {item.get('title', 'Unknown')}: {e}"
                )
                v_embeddings.append(None)

        # --- PHASE 3 : UPSERT & SYNC ---
        for idx, item in enumerate(batch):
            # L'id doit être celui sous lequel le catalogue sert l'œuvre, sinon
            # personne ne retrouvera le vecteur. sync_catalog résout l'external_id
            # dans cet ordre (idMal d'abord) : un vecteur indexé sur l'id AniList
            # serait introuvable depuis un catalogue servi par la base.
            ext_id = str(item.get("idMal") or item.get("mal_id") or item["id"])

            # Upsert pgvector
            repo.upsert_items(
                "anime_thematic", [ext_id], [t_embeddings[idx].tolist()], [item]
            )
            if v_embeddings[idx]:
                repo.upsert_items(
                    "character_visual_vibe", [ext_id], [v_embeddings[idx]], [item]
                )

            # SYNC NEO4J AUTOMATIQUE (Celery Pipeline)
            try:
                neo4j_manager.sync_media_to_graph(item, "Anime")
            except Exception as e:
                logger.warning(f"⚠️ Neo4j Sync Error for {item['title']}: {e}")

        logger.info(
            f"   📦 Processed {min(i + BATCH_SIZE, len(new_items))}/{len(new_items)}..."
        )

    logger.info("✅ SOTA Vectorization & Neo4j Sync Complete.")
    return True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vectorize the anime catalog into pgvector (thematic + visual)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of catalog items to process (default: all items).",
    )
    return parser.parse_args()


def _bootstrap_django() -> None:
    """Le script écrit dans le dépôt de vecteurs via le conteneur Django : sans
    `django.setup()`, il meurt sur `ImproperlyConfigured` avant la première ligne
    utile. Appelé ici seulement — importer le module reste sans effet de bord."""
    import django  # noqa: E402

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
    django.setup()


if __name__ == "__main__":
    args = _parse_args()
    _bootstrap_django()
    run_vectorization(limit=args.limit)

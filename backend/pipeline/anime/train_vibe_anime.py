import json
import os
import sys
import time
import logging
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# Setup logging
logger = logging.getLogger("animetix." + __name__)

try:
    from hf_trackio import trackio  # noqa: E402
except ImportError:
    # Mock trackio if not available
    class MockTrackio:
        def log(self, *args, **kwargs):
            pass

        def start_run(self, *args, **kwargs):
            pass

        def end_run(self, *args, **kwargs):
            pass

    trackio = MockTrackio()

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "models", "anime-vibe-model")
BATCH_SIZE = 16
EPOCHS = 2


def run_training():
    logger.info("--- Début du Fine-Tuning des Embeddings (Vibe) ---")

    # Initialize Tracking
    tracker = trackio.init(
        project="animetix-vibe", job_name=f"anime-vibe-{int(time.time())}"
    )

    # 1. Chargement des données
    clean_db = os.path.join(BASE_DIR, "data", "processed", "clean_root_animes.json")
    try:
        with open(clean_db, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Erreur : {clean_db} introuvable.")
        tracker.finish(status="FAILED")
        return

    tracker.log_artifact("clean_db", clean_db)
    tracker.log_param("epochs", EPOCHS)
    tracker.log_param("batch_size", BATCH_SIZE)

    # 2. Préparation des exemples d'entraînement
    train_examples = []
    for anime in data:
        title = anime["title"]
        for review in anime.get("reviews", []):
            if len(review) > 20:
                train_examples.append(InputExample(texts=[review, title]))

    if len(train_examples) < 10:
        logger.warning("Pas assez de critiques pour un fine-tuning efficace.")
        tracker.finish(status="FAILED")
        return

    logger.info(f"Nombre d'exemples d'entraînement : {len(train_examples)}")
    tracker.log_metric("num_train_examples", len(train_examples))

    # 3. Chargement du modèle de base
    model = SentenceTransformer(MODEL_NAME)

    # 4. Configuration de l'entraînement
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    # 5. Entraînement
    logger.info(f"Entraînement en cours pour {EPOCHS} époques...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=EPOCHS,
        warmup_steps=100,
        output_path=OUTPUT_PATH,
        show_progress_bar=True,
    )

    tracker.log_artifact("final_model", OUTPUT_PATH)
    tracker.finish(status="COMPLETED")
    logger.info(f"✅ Modèle fine-tuné sauvegardé dans : {OUTPUT_PATH}")


if __name__ == "__main__":
    run_training()

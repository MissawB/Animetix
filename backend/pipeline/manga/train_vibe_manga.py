import json
import os
import sys
import logging
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

logger = logging.getLogger("animetix.pipeline." + __name__)

# Force UTF-8 for Windows output
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "models", "manga-vibe-model")
BATCH_SIZE = 16
EPOCHS = 2


def run_training():
    logger.info("--- Début du Fine-Tuning des Embeddings Manga (Vibe) ---")

    # 1. Chargement des données
    clean_db = os.path.join(BASE_DIR, "data", "processed", "clean_root_mangas.json")
    try:
        with open(clean_db, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Erreur : {clean_db} introuvable.")
        return

    # 2. Préparation des exemples d'entraînement
    train_examples = []
    for manga in data:
        title = manga["title"]
        # On crée des paires (Critique, Titre) pour que le modèle lie le ressenti au sujet
        for review in manga.get("reviews", []):
            if len(review) > 20:
                train_examples.append(InputExample(texts=[review, title]))

    if len(train_examples) < 10:
        logger.warning("Pas assez de critiques pour un fine-tuning efficace.")
        return

    logger.info(f"Nombre d'exemples d'entraînement : {len(train_examples)}")

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

    logger.info(f"✅ Modèle fine-tuné Manga sauvegardé dans : {OUTPUT_PATH}")


if __name__ == "__main__":
    run_training()

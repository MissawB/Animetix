import argparse
import logging
import os
import sys

import django

# --- Environment & Django Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "backend"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "animetix_project.settings")
django.setup()

# --- App Imports ---
from animetix.containers import get_container  # noqa: E402
from pipeline.neo4j_client import neo4j_manager  # noqa: E402

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("animetix.vision_quest.worker")

# --- Constants ---
MAX_MEMORY_SAFE_SIZE = 500 * 1024 * 1024  # 500MB


def process_video_for_combat_lore(media_id: str, video_path: str):
    """
    Processes a video file to extract combat-related lore using a Vision-Language Model (VLM).

    This function reads the video data, sends it to the VisionQuestService for
    lore extraction, and then synchronizes any detected combat events to the
    Neo4j graph database.

    Args:
        media_id (str): The unique identifier of the media (anime/movie) in the Neo4j database.
        video_path (str): The local filesystem path to the video file to be processed.

    Returns:
        None: Results are logged and synced to the database.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return

    # Memory Management: Check file size
    try:
        file_size = os.path.getsize(video_path)
        if file_size > MAX_MEMORY_SAFE_SIZE:
            logger.warning(
                f"⚠️ Video file is large ({file_size / (1024 * 1024):.2f}MB). "
                "Processing may consume significant memory."
            )
    except OSError as e:
        logger.error(f"Could not check file size for {video_path}: {e}")
        # Continue anyway as we check existence above

    logger.info(f"🚀 Processing video for Media {media_id}: {video_path}")

    container = get_container()
    video_service = container.video_quest_service

    try:
        with open(video_path, "rb") as f:
            video_data = f.read()

        # Extract lore using VLM
        combats = video_service.extract_combat_lore(video_data)

        if combats:
            logger.info(
                f"✨ Extracted {len(combats)} combat events. Syncing to Neo4j..."
            )
            neo4j_manager.sync_combat_lore(media_id, combats)
            logger.info("✅ Sync complete.")
        else:
            logger.info("ℹ️ No combat lore detected in this clip.")

    except Exception as e:
        logger.error(f"❌ Error during Vision-Quest processing: {e}")
        raise  # Re-raise to allow main block to handle exit code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process anime video for combat lore extraction."
    )
    parser.add_argument("--id", type=str, required=True, help="Media ID in Neo4j")
    parser.add_argument("--path", type=str, required=True, help="Path to video file")
    args = parser.parse_args()

    try:
        process_video_for_combat_lore(args.id, args.path)
    except Exception:
        # Final error boundary for CLI exit code
        sys.exit(1)

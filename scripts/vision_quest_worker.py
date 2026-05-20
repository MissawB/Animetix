import os
import sys
import django
import logging

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.containers import get_container
from pipeline.neo4j_client import neo4j_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("animetix.vision_quest.worker")

def process_video_for_combat_lore(media_id: str, video_path: str):
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return

    logger.info(f"🚀 Processing video for Media {media_id}: {video_path}")
    
    container = get_container()
    video_service = container.video_quest_service
    
    try:
        with open(video_path, 'rb') as f:
            video_data = f.read()
            
        # Extract lore using VLM
        combats = video_service.extract_combat_lore(video_data)
        
        if combats:
            logger.info(f"✨ Extracted {len(combats)} combat events. Syncing to Neo4j...")
            neo4j_manager.sync_combat_lore(media_id, combats)
            logger.info("✅ Sync complete.")
        else:
            logger.info("ℹ️ No combat lore detected in this clip.")
            
    except Exception as e:
        logger.error(f"❌ Error during Vision-Quest processing: {e}")

if __name__ == "__main__":
    # Example usage
    import argparse
    parser = argparse.ArgumentParser(description="Process anime video for combat lore extraction.")
    parser.add_argument("--id", type=str, required=True, help="Media ID in Neo4j")
    parser.add_argument("--path", type=str, required=True, help="Path to video file")
    args = parser.parse_args()
    
    process_video_for_combat_lore(args.id, args.path)

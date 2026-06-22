import sys
from pathlib import Path

# Setup Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

from pipeline.vector_client import vector_manager  # noqa: E402

collections = [
    "anime_thematic",
    "anime_visual_vibe",
    "manga_thematic",
    "manga_visual_vibe",
    "movie_thematic",
    "movie_plot",
    "movie_vibe",
    "character_vibe",
    "character_visual_vibe",
    "game_thematic",
    "game_plot",
    "game_vibe",
    "actor_thematic",
    "actor_vibe",
]

for coll_name in collections:
    try:
        coll = vector_manager.get_collection(coll_name)
        count = coll.count()
        print(f"Collection '{coll_name}': {count} items")
    except Exception as e:
        print(f"Collection '{coll_name}': Error {e}")

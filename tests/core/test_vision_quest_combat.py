import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Setup paths to ensure imports work correctly
# We use absolute paths based on the environment context
BASE_DIR = r"C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project"
SRC_PATH = os.path.join(BASE_DIR, "src")
BACKEND_PATH = os.path.join(BASE_DIR, "src", "backend")
SCRIPTS_PATH = os.path.join(BASE_DIR, "scripts")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)
if SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, SCRIPTS_PATH)

# Mock Django settings before any imports that might trigger it
import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        PROJECT_ROOT=BASE_DIR,
        CHROMA_DB_PATH=os.path.join(BASE_DIR, "data", "chroma_db"),
        MODELS_DIR=os.path.join(BASE_DIR, "data", "models"),
        DEBUG=True,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        INSTALLED_APPS=["animetix"],
        SECRET_KEY="dummy-secret-key",
    )
    django.setup()

from animetix.containers import get_container  # noqa: E402
from vision_quest_worker import process_video_for_combat_lore  # noqa: E402


@pytest.fixture
def mock_vlm_response():
    return {
        "combats": [
            {
                "technique": "Kamehameha",
                "character": "Goku",
                "visual_description": "Blue beam",
                "timestamp": "05:20",
            }
        ]
    }


def test_process_video_for_combat_lore_e2e(mock_vlm_response, tmp_path):
    # 1. Prepare dummy video file
    video_file = tmp_path / "test_video.mp4"
    video_file.write_bytes(b"dummy video content")

    media_id = "anime_123"

    # 2. Mock VLM Adapter
    container = get_container()
    # Reset container cache to ensure mocks are used
    container._cache = {}

    mock_v_service = MagicMock()
    mock_v_service.extract_combat_lore.return_value = mock_vlm_response["combats"]
    container.video_quest_service = mock_v_service

    # 3. Mock Neo4j Manager and run test
    with patch("vision_quest_worker.neo4j_manager") as mock_neo4j:
        # 4. Run the worker logic
        process_video_for_combat_lore(media_id, str(video_file))

        # 5. Verification
        expected_combats = mock_vlm_response["combats"]

        # Verify Neo4j sync was called with correct arguments
        mock_neo4j.sync_combat_lore.assert_called_once_with(media_id, expected_combats)

        print("\n✅ End-to-End Verification Successful!")


if __name__ == "__main__":
    # If run directly, execute with pytest
    pytest.main([__file__, "-v", "-s"])

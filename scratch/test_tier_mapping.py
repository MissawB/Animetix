import sys
from pathlib import Path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.core.domain.services.creative.vs_battle_service import VsBattleService
from unittest.mock import MagicMock

service = VsBattleService(fandom_port=MagicMock(), inference_engine=MagicMock(), prompt_manager=MagicMock())
test_cases = [
    "Tier 0", "Boundless", "1-A", "Outerversal", "High 1-B", "Complex Multiversal",
    "Low 2-C", "At least 7-B, likely 7-A", "Universe level", "Street level", "10-B", "Human level"
]
for tc in test_cases:
    print(f"'{tc}' -> {service._map_tier_to_value(tc)}")

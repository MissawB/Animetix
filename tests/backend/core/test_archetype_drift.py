import pytest
from unittest.mock import MagicMock
from core.domain.services.archetype_drift_service import ArchetypeDriftService
from core.domain.entities.personalization import VisualConfig

def test_calculate_drift_no_user():
    service = ArchetypeDriftService(feedback_port=MagicMock(), memory_service=MagicMock())
    config = service.calculate_drift(user_id=None)
    assert config.archetype_id == "default"
    assert config.primary_accent == "#FD7706"

def test_calculate_drift_with_user():
    service = ArchetypeDriftService(feedback_port=MagicMock(), memory_service=MagicMock())
    config = service.calculate_drift(user_id=1)
    # Based on hardcoded logic in current implementation:
    # recent_stats = {"shonen_hero": 0.8, "seinen_mystery": 0.2}
    # dominant is shonen_hero
    assert config.archetype_id == "shonen_hero"
    assert config.primary_accent == "#FF4500" # From ARCHETYPE_VISUAL_MAP
    assert config.aura_type == "fire"
    assert config.aura_intensity == 0.8

import pytest
from unittest.mock import MagicMock
from core.domain.services.archetype_drift_service import ArchetypeDriftService
from core.domain.entities.personalization import VisualConfig

def test_calculate_drift_no_user():
    service = ArchetypeDriftService(feedback_port=MagicMock(), memory_service=MagicMock(), repository=MagicMock())
    config = service.calculate_drift(user_id=None)
    assert config.archetype_id == "default"
    assert config.primary_accent == "#FD7706"

def test_calculate_drift_with_user():
    feedback_mock = MagicMock()
    feedback_mock.get_user_feedback.return_value = [
        {"is_positive": True, "input_context": "I love shonen", "output_text": ""}
    ]
    
    repo_mock = MagicMock()
    repo_mock.get_user_gameplay_history.return_value = []
    repo_mock.get_user_creative_history.return_value = []
    
    service = ArchetypeDriftService(feedback_port=feedback_mock, memory_service=MagicMock(), repository=repo_mock)
    config = service.calculate_drift(user_id=1)
    
    assert config.archetype_id == "shonen"
    assert config.primary_accent == "#FFA500" # From ARCHETYPE_VISUAL_MAP for "shonen"
    assert config.aura_type == "fire"
    assert config.aura_intensity == 1.0

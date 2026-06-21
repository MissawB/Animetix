import pytest
from core.domain.entities.personalization import ArchetypeScore, VisualConfig
from pydantic import ValidationError


def test_visual_config_valid():
    config = VisualConfig(
        archetype_id="shonen_hero",
        primary_accent="#FF4500",
        aura_type="fire",
        aura_intensity=0.8,
        font_vibe="brush",
    )
    assert config.archetype_id == "shonen_hero"
    assert config.aura_intensity == 0.8


def test_visual_config_invalid_intensity():
    with pytest.raises(ValidationError):
        VisualConfig(
            archetype_id="shonen_hero",
            primary_accent="#FF4500",
            aura_type="fire",
            aura_intensity=1.5,  # Out of range 0.0-1.0
            font_vibe="brush",
        )


def test_visual_config_invalid_aura_type():
    with pytest.raises(ValidationError):
        VisualConfig(
            archetype_id="shonen_hero",
            primary_accent="#FF4500",
            aura_type="invalid_aura",
            aura_intensity=0.8,
            font_vibe="brush",
        )


def test_archetype_score_valid():
    score = ArchetypeScore(scores={"shonen_hero": 0.5, "cyberpunk": 0.2})
    assert score.scores["shonen_hero"] == 0.5

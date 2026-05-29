from core.domain.entities.ai_schemas import CombatStats, CombatCharacter
import pytest

def test_combat_stats_tier_value():
    stats = CombatStats(
        tier="2-C",
        speed="MFTL+",
        durability="Multi-Galaxy",
        intelligence="Gifted",
        abilities=["Reality Warping"]
    )
    # Check default value
    assert stats.tier_value == 0
    
    # Check assignment
    stats_explicit = CombatStats(
        tier="2-C",
        speed="MFTL+",
        durability="Multi-Galaxy",
        intelligence="Gifted",
        abilities=["Reality Warping"],
        tier_value=85
    )
    assert stats_explicit.tier_value == 85

def test_combat_character_image_url():
    stats = CombatStats(tier="2-C", speed="X", durability="Y", intelligence="Z")
    char = CombatCharacter(
        name="Test Hero",
        wiki_url="https://example.com",
        stats=stats,
        summary="A test hero"
    )
    # Check default value
    assert char.image_url is None
    
    # Check assignment
    char_with_img = CombatCharacter(
        name="Test Hero",
        wiki_url="https://example.com",
        stats=stats,
        summary="A test hero",
        image_url="https://example.com/img.png"
    )
    assert char_with_img.image_url == "https://example.com/img.png"

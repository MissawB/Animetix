import pytest
import json
from unittest.mock import MagicMock, patch
from backend.core.domain.services.creative.vs_battle_service import VsBattleService
from backend.core.domain.entities.ai_schemas import (
    CombatCharacter, CombatStats, CombatResult, DebateTurn
)
from backend.core.ports.fandom_port import FandomPort
from backend.core.ports.inference_port import InferencePort
from backend.core.domain.services.prompt_manager import PromptManager

@pytest.fixture
def mock_fandom_port():
    return MagicMock(spec=FandomPort)

@pytest.fixture
def mock_inference_port():
    return MagicMock(spec=InferencePort)

@pytest.fixture
def mock_prompt_manager():
    return MagicMock(spec=PromptManager)

@pytest.fixture
def vs_battle_service(mock_fandom_port, mock_inference_port, mock_prompt_manager):
    return VsBattleService(
        fandom_port=mock_fandom_port,
        inference_engine=mock_inference_port,
        prompt_manager=mock_prompt_manager
    )

def test_fetch_and_parse_character(vs_battle_service, mock_fandom_port, mock_inference_port, mock_prompt_manager):
    # Setup
    character_name = "Naruto"
    mock_fandom_port.fetch_character_data.return_value = [{
        "name": "Naruto Uzumaki",
        "wikitext": "Raw wikitext content",
        "image_url": "https://example.com/naruto.jpg"
    }]
    
    expected_character_data = {
        "name": "Naruto Uzumaki",
        "wiki_url": "https://vsbattles.fandom.com/wiki/Naruto_Uzumaki",
        "stats": {
            "tier": "5-B",
            "speed": "Sub-Relativistic",
            "durability": "Planet level",
            "intelligence": "Gifted",
            "abilities": ["Shadow Clone", "Rasengan"]
        },
        "summary": "The Seventh Hokage"
    }
    
    mock_inference_port.generate.return_value = json.dumps(expected_character_data)
    mock_prompt_manager.get_prompt.return_value = ("Parser prompt", "Parser system")
    
    # Execute
    result = vs_battle_service.fetch_and_parse_character(character_name)
    
    # Verify
    mock_fandom_port.fetch_character_data.assert_any_call("Naruto profile VS Battles Wiki")
    mock_inference_port.generate.assert_called_once()
    assert result.name == "Naruto Uzumaki"
    assert result.stats.tier == "5-B"
    assert result.stats.tier_value == 46
    assert result.image_url == "https://example.com/naruto.jpg"

def test_tier_mapping(vs_battle_service):
    # Test high tiers
    assert vs_battle_service._map_tier_to_value("Tier 0") == 100
    assert vs_battle_service._map_tier_to_value("Boundless") == 100
    assert vs_battle_service._map_tier_to_value("1-A") == 95
    assert vs_battle_service._map_tier_to_value("Outerversal") == 95
    assert vs_battle_service._map_tier_to_value("High 1-B") == 92
    assert vs_battle_service._map_tier_to_value("Complex Multiversal") == 85
    
    # Test mid tiers
    assert vs_battle_service._map_tier_to_value("Low 2-C") == 70
    assert vs_battle_service._map_tier_to_value("At least 7-B, likely 7-A") == 36
    assert vs_battle_service._map_tier_to_value("Universe level") == 0
    
    # Test low tiers
    assert vs_battle_service._map_tier_to_value("Street level") == 20
    assert vs_battle_service._map_tier_to_value("10-B") == 10
    assert vs_battle_service._map_tier_to_value("Human level") == 10

    
    # Test unknown
    assert vs_battle_service._map_tier_to_value("Unknown") == 0
    assert vs_battle_service._map_tier_to_value("") == 0

def test_run_battle(vs_battle_service, mock_fandom_port, mock_inference_port, mock_prompt_manager):
    # Setup
    char_a_name = "Naruto"
    char_b_name = "Luffy"
    
    char_a = CombatCharacter(
        name="Naruto Uzumaki",
        wiki_url="url_a",
        stats=CombatStats(tier="5-B", speed="fast", durability="high", intelligence="mid", abilities=[]),
        summary="Naruto summary"
    )
    char_b = CombatCharacter(
        name="Monkey D. Luffy",
        wiki_url="url_b",
        stats=CombatStats(tier="6-A", speed="fast", durability="high", intelligence="mid", abilities=[]),
        summary="Luffy summary"
    )
    
    # Mock fetch_and_parse_character internally or mock the dependencies
    with patch.object(VsBattleService, 'fetch_and_parse_character') as mock_fetch:
        mock_fetch.side_effect = [char_a, char_b]
        
        mock_prompt_manager.get_prompt.side_effect = [
            ("Advocate A prompt", "System A"),
            ("Advocate B prompt", "System B"),
            ("Judge prompt", "System Judge")
        ]
        
        # Verdict data
        verdict_data = {
            "analysis": "Analysis...",
            "verdict": "Verdict...",
            "winner": "Naruto Uzumaki",
            "confidence": 0.9
        }

        mock_inference_port.generate.side_effect = [
            "Argument for Naruto",
            "Argument for Luffy",
            json.dumps(verdict_data)
        ]
        
        # Execute
        result = vs_battle_service.run_battle(char_a_name, char_b_name)
        
        # Verify
        assert isinstance(result, CombatResult)
        assert result.winner == "Naruto Uzumaki"
        assert len(result.debate_history) == 3 # Advocate A, Advocate B, Judge
        assert result.debate_history[0].agent == "Advocate_A"
        assert result.debate_history[1].agent == "Advocate_B"
        assert result.debate_history[2].agent == "Judge"

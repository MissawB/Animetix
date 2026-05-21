import logging
from typing import Dict, Any, List

from src.core.domain.entities.ai_schemas import (
    CombatCharacter, CombatStats, CombatResult, DebateTurn
)
from src.core.ports.fandom_port import FandomPort
from src.core.ports.inference_port import InferencePort
from src.core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.vs_battle")

class VsBattleService:
    """
    Service orchestrating VS Battles between characters using Fandom data and LLM debates.
    """
    def __init__(
        self, 
        fandom_port: FandomPort, 
        inference_engine: InferencePort, 
        prompt_manager: PromptManager
    ):
        self.fandom_port = fandom_port
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def fetch_and_parse_character(self, name: str) -> CombatCharacter:
        """
        Fetches character data from Fandom and parses it into a structured CombatCharacter entity.
        """
        logger.info(f"Fetching data for character: {name}")
        raw_data = self.fandom_port.fetch_character_data(name)
        wikitext = raw_data.get("wikitext", "")
        wiki_url = raw_data.get("url", f"https://vsbattles.fandom.com/wiki/{name.replace(' ', '_')}")
        image_url = raw_data.get("image_url")

        prompt, system = self.prompt_manager.get_prompt("vs_battle_parser", wikitext=wikitext)
        
        character = self.inference_engine.generate_structured(
            prompt=prompt,
            system_prompt=system,
            response_model=CombatCharacter
        )
        
        # Ensure name and URL are correctly set if LLM missed them or returned generic ones
        if not character.name or character.name == "Unknown":
            character.name = name
        character.wiki_url = wiki_url
        character.image_url = image_url
        
        # Normalize tier value
        if character.stats:
            character.stats.tier_value = self._map_tier_to_value(character.stats.tier)
            logger.info(f"Normalized tier '{character.stats.tier}' to value {character.stats.tier_value}")
        
        return character

    def _map_tier_to_value(self, tier_str: str) -> int:
        """
        Maps a VS Battles Wiki tier string to a numeric value (0-100).
        """
        if not tier_str:
            return 0
            
        t = tier_str.upper()
        
        # 1. Keywords (More specific than numbers)
        if "BOUNDLESS" in t: return 100
        if "OUTERVERSAL" in t: return 95
        if "HYPERVERSAL" in t: return 90
        if "COMPLEX MULTIVERSAL" in t: return 85
        if "MULTIVERSAL+" in t: return 80
        if "MULTIVERSAL" in t: return 75
        if "LOW MULTIVERSAL" in t: return 70
        if "UNIVERSAL" in t or "UNIVERSE" in t: return 65
        if "MULTI-GALAXY" in t: return 60
        if "MULTI-SOLAR SYSTEM" in t: return 55
        if "SOLAR SYSTEM" in t: return 50
        if "PLANET" in t: return 45
        if "CONTINENT" in t: return 40
        if "MOUNTAIN" in t: return 30
        if "URBAN" in t: return 20
        if "STREET" in t: return 10
        if "HUMAN" in t: return 5

        # 2. Tier labels (Alpha-numeric)
        if "1-A" in t: return 95
        if "1-B" in t: return 90
        if "1-C" in t: return 85
        if "2-A" in t: return 80
        if "2-B" in t: return 75
        if "2-C" in t: return 70
        if "3-A" in t: return 65
        if "3-B" in t: return 60
        if "4-A" in t: return 55
        if "4-B" in t: return 50
        
        # 3. Numeric tiers (using regex for word boundaries to avoid 5 in 15 etc.)
        import re
        if re.search(r"\b0\b", t): return 100
        if re.search(r"\b5\b", t): return 45
        if re.search(r"\b6\b", t): return 40
        if re.search(r"\b7\b", t): return 30
        if re.search(r"\b8\b", t): return 20
        if re.search(r"\b9\b", t): return 10
        if re.search(r"\b10\b", t): return 5
        
        return 0

    def run_battle(self, char_a_name: str, char_b_name: str, language: str = "Français") -> CombatResult:
        """
        Runs a full VS battle debate between two characters.
        """
        logger.info(f"Starting battle: {char_a_name} vs {char_b_name}")
        
        # 1. Fetch and Parse
        char_a = self.fetch_and_parse_character(char_a_name)
        char_b = self.fetch_and_parse_character(char_b_name)
        
        debate_history: List[DebateTurn] = []
        
        # 2. Advocate A Argument
        logger.info(f"Generating argument for {char_a.name}")
        prompt_a, system_a = self.prompt_manager.get_prompt(
            "vs_battle_advocate",
            character_name=char_a.name,
            opponent_name=char_b.name,
            character_stats=char_a.stats.model_dump_json(indent=2),
            opponent_stats=char_b.stats.model_dump_json(indent=2),
            language=language
        )
        arg_a = self.inference_engine.generate(prompt_a, system_prompt=system_a)
        debate_history.append(DebateTurn(agent="Advocate_A", content=arg_a))
        
        # 3. Advocate B Argument
        logger.info(f"Generating argument for {char_b.name}")
        prompt_b, system_b = self.prompt_manager.get_prompt(
            "vs_battle_advocate",
            character_name=char_b.name,
            opponent_name=char_a.name,
            character_stats=char_b.stats.model_dump_json(indent=2),
            opponent_stats=char_a.stats.model_dump_json(indent=2),
            language=language
        )
        arg_b = self.inference_engine.generate(prompt_b, system_prompt=system_b)
        debate_history.append(DebateTurn(agent="Advocate_B", content=arg_b))
        
        # 4. Final Verdict (Judge)
        logger.info("Generating final verdict")
        prompt_j, system_j = self.prompt_manager.get_prompt(
            "vs_battle_judge",
            character_a_name=char_a.name,
            character_b_name=char_b.name,
            character_a_stats=char_a.stats.model_dump_json(indent=2),
            character_b_stats=char_b.stats.model_dump_json(indent=2),
            advocate_a_argument=arg_a,
            advocate_b_argument=arg_b,
            language=language
        )
        
        # We need a separate schema for Judge output if we want strictly structured JSON from judge
        # But for now let's use generate_structured with a dynamic model or a simple Dict if supported.
        # Actually, let's define a small JudgeResult model locally or use an existing one.
        from pydantic import BaseModel
        class JudgeVerdict(BaseModel):
            analysis: str
            verdict: str
            winner: str
            confidence: float

        verdict_data = self.inference_engine.generate_structured(
            prompt=prompt_j,
            system_prompt=system_j,
            response_model=JudgeVerdict
        )
        
        debate_history.append(DebateTurn(agent="Judge", content=f"{verdict_data.analysis}\n\nVERDICT: {verdict_data.verdict}"))
        
        return CombatResult(
            character_a=char_a,
            character_b=char_b,
            debate_history=debate_history,
            winner=verdict_data.winner,
            verdict_summary=verdict_data.verdict
        )

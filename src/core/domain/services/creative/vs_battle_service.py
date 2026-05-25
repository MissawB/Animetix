import logging
import json
import re as _regex_module
import difflib
from typing import Dict, Any, List, Type, TypeVar, Optional

from pydantic import BaseModel
from src.core.domain.entities.ai_schemas import (
    CombatCharacter, CombatStats, CombatResult, DebateTurn
)
from src.core.ports.fandom_port import FandomPort
from src.core.ports.inference_port import InferencePort
from src.core.ports.web_search_port import WebSearchPort
from src.core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.vs_battle")

T = TypeVar('T', bound=BaseModel)

class VsBattleService:
    """
    Service orchestrating VS Battles between characters using Fandom data and LLM debates.
    """
    def __init__(
        self, 
        fandom_port: FandomPort, 
        inference_engine: InferencePort, 
        prompt_manager: PromptManager,
        web_search_port: Optional[WebSearchPort] = None
    ):
        self.fandom_port = fandom_port
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.web_search_port = web_search_port

    def _normalize_anime_name(self, name: str) -> str:
        """
        Normalizes common Japanese/English spelling variations in anime names.
        """
        n = name.lower()
        n = n.replace('ou', 'o').replace('uu', 'u')
        n = n.replace(' (anime)', '').replace(' (manga)', '')
        return n.strip()

    def _is_name_match(self, requested_name: str, found_title: str) -> bool:
        """
        Determines if a found wiki title belongs to the requested character using fuzzy logic.
        """
        req_norm = self._normalize_anime_name(requested_name)
        found_norm = self._normalize_anime_name(found_title)
        
        req_parts = req_norm.split()
        found_parts = found_norm.split()
        
        # Direct match or partial match
        if all(part in found_norm for part in req_parts) or all(part in req_norm for part in found_parts):
            return True
            
        # Fuzzy match for the first name
        if req_parts and found_parts:
            similarity = difflib.SequenceMatcher(None, req_parts[0], found_parts[0]).ratio()
            if similarity > 0.8: return True
                
        # Reversed names
        if len(req_parts) >= 2 and len(found_parts) >= 2:
            if req_parts[0] in found_parts and req_parts[-1] in found_parts:
                return True

        return False

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly extracts JSON from LLM output.
        """
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            match = _regex_module.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, _regex_module.DOTALL | _regex_module.IGNORECASE)
            if match:
                try: return json.loads(match.group(1))
                except json.JSONDecodeError: pass
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try: return json.loads(text[start:end+1])
                except json.JSONDecodeError: pass
            raise ValueError(f"Could not extract valid JSON from LLM response")

    def _safe_generate_structured(self, prompt: str, system_prompt: str, response_model: Type[T]) -> T:
        """
        Tries generate_structured, falls back to generate + manual parse on failure.
        """
        try:
            return self.inference_engine.generate_structured(
                prompt=prompt,
                system_prompt=system_prompt,
                response_model=response_model
            )
        except Exception as e:
            logger.warning(f"Structured generation failed ({e}), falling back to manual parsing.")
            raw_response = self.inference_engine.generate(prompt, system_prompt=system_prompt)
            json_data = self._extract_json(raw_response)
            return response_model.model_validate(json_data)

    def fetch_and_parse_character(self, name: str, franchise: Optional[str] = None) -> CombatCharacter:
        """
        Legacy method: Returns the strongest version.
        """
        versions = self.fetch_character_versions(name, franchise=franchise)
        if not versions:
            raise ValueError(f"Could not find any valid profile for '{name}'")
        return max(versions, key=lambda c: c.stats.tier_value if c.stats else -1)

    def fetch_character_versions(self, name: str, franchise: Optional[str] = None) -> List[CombatCharacter]:
        """
        Fetches ALL valid character versions from Fandom.
        """
        logger.info(f"🔍 Finding all Wiki versions for: {name}")
        all_raw_data = self.fandom_port.fetch_character_data(name, franchise=franchise)
        if not all_raw_data: return []

        parsed_versions = []
        for raw_data in all_raw_data:
            page_title = raw_data.get("name", name)
            if not self._is_name_match(name, page_title):
                logger.warning(f"⏩ Skipping unrelated candidate: {page_title}")
                continue

            try:
                wikitext = raw_data.get("wikitext", "")
                prompt, system = self.prompt_manager.get_prompt("vs_battle_parser", wikitext=wikitext[:5000])
                character = self._safe_generate_structured(prompt=prompt, system_prompt=system, response_model=CombatCharacter)
                
                character.name = page_title
                character.wiki_url = raw_data.get("url", "")
                character.image_url = raw_data.get("image_url") or character.image_url
                
                if character.stats:
                    best_tier_str = self._extract_max_tier(character.stats.tier)
                    character.stats.tier_value = self._map_tier_to_value(best_tier_str)
                    logger.info(f"✅ Parsed version: {character.name} (Value: {character.stats.tier_value})")
                    parsed_versions.append(character)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse '{page_title}': {e}")
                
        return parsed_versions

    def _map_tier_to_value(self, tier_str: str) -> int:
        """
        Maps a VS Battles Wiki tier string to a numeric value.
        """
        if not tier_str: return 0
        t = tier_str.upper()
        tier_patterns = [
            (r"\b0\b", 100), (r"\b1-A\b", 95), (r"OUTERVERSAL", 95),
            (r"HIGH 1-B", 92), (r"\b1-B\b", 90), (r"HYPERVERSAL", 90),
            (r"HIGH 1-C", 88), (r"\b1-C\b", 85), (r"COMPLEX MULTIVERSAL", 85),
            (r"HIGH 2-A", 82), (r"\b2-A\b", 80), (r"MULTIVERSAL\+", 80),
            (r"\b2-B\b", 75), (r"MULTIVERSAL", 75),
            (r"\b2-C\b", 70), (r"LOW MULTIVERSAL", 70),
            (r"HIGH 3-A", 68), (r"\b3-A\b", 65), (r"UNIVERSAL", 65),
            (r"\b3-B\b", 60), (r"MULTI-GALAXY", 60),
            (r"\b3-C\b", 58), (r"GALAXY", 58),
            (r"\b4-A\b", 55), (r"MULTI-SOLAR SYSTEM", 55),
            (r"\b4-B\b", 53), (r"SOLAR SYSTEM", 53),
            (r"\b4-C\b", 50), (r"STAR", 50),
            (r"\b5-A\b", 48), (r"LARGE PLANET", 48),
            (r"\b5-B\b", 46), (r"PLANET", 46),
            (r"LOW 5-B", 45), (r"\b5-C\b", 44), (r"MOON", 44),
            (r"\b6-A\b", 42), (r"LARGE CONTINENT", 42),
            (r"\b6-B\b", 40), (r"CONTINENT", 40),
            (r"HIGH 6-C", 39), (r"\b6-C\b", 38), (r"ISLAND", 38),
            (r"HIGH 7-A", 37), (r"\b7-A\b", 36), (r"LARGE MOUNTAIN", 36),
            (r"\b7-B\b", 34), (r"MOUNTAIN", 34),
            (r"\b7-C\b", 32), (r"TOWN", 32), (r"LOW 7-C", 31),
            (r"HIGH 8-A", 31), (r"\b8-A\b", 30), (r"MULTI-CITY BLOCK", 30),
            (r"\b8-B\b", 28), (r"CITY BLOCK", 28),
            (r"\b8-C\b", 26), (r"BUILDING", 26),
            (r"\b9-A\b", 24), (r"SMALL BUILDING", 24), (r"ROOM", 24),
            (r"\b9-B\b", 22), (r"WALL", 22),
            (r"\b9-C\b", 20), (r"STREET", 20),
            (r"10-A", 15), (r"ATHLETE", 15),
            (r"10-B", 10), (r"HUMAN", 10),
            (r"10-C", 5)
        ]
        for pattern, value in tier_patterns:
            if _regex_module.search(pattern, t): return value
        return 0

    def _extract_max_tier(self, tier_str: str) -> str:
        """
        Returns the strongest tier from a complex string.
        """
        parts = _regex_module.split(r'\||,|/|AND|OR', tier_str, flags=_regex_module.IGNORECASE)
        best_tier = tier_str
        max_val = -1
        for part in parts:
            part = part.strip()
            val = self._map_tier_to_value(part)
            if val > max_val:
                max_val = val
                best_tier = part
        return best_tier.strip()

    def run_battle(self, char_a_name: str, char_b_name: str, language: str = "Français") -> CombatResult:
        """
        Runs a full VS battle debate between two characters.
        """
        logger.info(f"Starting battle: {char_a_name} vs {char_b_name}")
        char_a = self.fetch_and_parse_character(char_a_name)
        char_b = self.fetch_and_parse_character(char_b_name)
        
        debate_history: List[DebateTurn] = []
        
        # Advocate A
        prompt_a, system_a = self.prompt_manager.get_prompt("vs_battle_advocate", character_name=char_a.name, opponent_name=char_b.name, character_stats=char_a.stats.model_dump_json(indent=2), opponent_stats=char_b.stats.model_dump_json(indent=2), language=language)
        arg_a = self.inference_engine.generate(prompt_a, system_prompt=system_a)
        debate_history.append(DebateTurn(agent="Advocate_A", content=arg_a))
        
        # Advocate B
        prompt_b, system_b = self.prompt_manager.get_prompt("vs_battle_advocate", character_name=char_b.name, opponent_name=char_a.name, character_stats=char_b.stats.model_dump_json(indent=2), opponent_stats=char_a.stats.model_dump_json(indent=2), language=language)
        arg_b = self.inference_engine.generate(prompt_b, system_prompt=system_b)
        debate_history.append(DebateTurn(agent="Advocate_B", content=arg_b))
        
        # Judge
        prompt_j, system_j = self.prompt_manager.get_prompt("vs_battle_judge", character_a_name=char_a.name, character_b_name=char_b.name, character_a_stats=char_a.stats.model_dump_json(indent=2), character_b_stats=char_b.stats.model_dump_json(indent=2), advocate_a_argument=arg_a, advocate_b_argument=arg_b, language=language)
        
        class JudgeVerdict(BaseModel):
            analysis: str
            verdict: str
            winner: str
            confidence: float

        verdict_data = self._safe_generate_structured(prompt=prompt_j, system_prompt=system_j, response_model=JudgeVerdict)
        debate_history.append(DebateTurn(agent="Judge", content=f"{verdict_data.analysis}\n\nVERDICT: {verdict_data.verdict}"))
        
        return CombatResult(character_a=char_a, character_b=char_b, debate_history=debate_history, winner=verdict_data.winner, verdict_summary=verdict_data.verdict)

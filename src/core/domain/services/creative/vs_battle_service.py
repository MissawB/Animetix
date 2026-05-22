import logging
import json
import re
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

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly extracts JSON from LLM output, handling markdown code blocks and garbage.
        """
        try:
            # 1. Try direct parse
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # 2. Try extraction from markdown block
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 3. Last ditch: try to find the first '{' and last '}'
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass
            
            raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}...")

    def _safe_generate_structured(self, prompt: str, system_prompt: str, response_model: Type[T]) -> T:
        """
        Tries generate_structured, falls back to generate + manual parse on failure.
        """
        try:
            logger.info(f"Attempting structured generation for {response_model.__name__}")
            return self.inference_engine.generate_structured(
                prompt=prompt,
                system_prompt=system_prompt,
                response_model=response_model
            )
        except Exception as e:
            logger.warning(f"Structured generation failed ({e}), falling back to manual parsing.")
            # Ensure the prompt asks for JSON (already true in our updated prompts)
            raw_response = self.inference_engine.generate(prompt, system_prompt=system_prompt)
            json_data = self._extract_json(raw_response)
            return response_model.model_validate(json_data)

    def fetch_and_parse_character(self, name: str, franchise: Optional[str] = None) -> CombatCharacter:
        """
        Fetches character data from Fandom with an initial smart search step.
        """
        logger.info(f"🔍 Finding correct Wiki title for: {name} (Franchise: {franchise})")
        
        # 1. SMART SEARCH STEP: Use WebSearchPort if available to find the exact page
        target_name = name
        if self.web_search_port:
            try:
                # We look for the character name on the specific wiki
                search_query = f"{name} {franchise} VS Battles Wiki" if franchise else f"{name} profile VS Battles Wiki"
                search_results = self.web_search_port.search(search_query)
                
                if search_results:
                    for res in search_results[:3]:
                        url = res.get('url', '')
                        if 'vsbattles.fandom.com/wiki/' in url:
                            # Extract the title from the first relevant URL: https://vsbattles.fandom.com/wiki/Title
                            found_title = url.split('/wiki/')[-1].split('?')[0].replace('_', ' ')
                            # Unescape URL characters
                            from urllib.parse import unquote
                            found_title = unquote(found_title)
                            logger.info(f"🎯 Smart search found actual title: {found_title}")
                            target_name = found_title
                            break
            except Exception as e:
                logger.warning(f"⚠️ Smart search failed: {e}")

        # 2. FETCH FROM FANDOM (Pass franchise)
        raw_data = self.fandom_port.fetch_character_data(target_name, franchise=franchise)
        wikitext = raw_data.get("wikitext", "")
        wiki_url = raw_data.get("url", f"https://vsbattles.fandom.com/wiki/{target_name.replace(' ', '_')}")
        image_url = raw_data.get("image_url")

        if not wikitext:
            # Last ditch attempt with original name if smart search target failed
            if target_name != name:
                raw_data = self.fandom_port.fetch_character_data(name)
                wikitext = raw_data.get("wikitext", "")
                image_url = raw_data.get("image_url") or image_url

        if not wikitext:
             raise ValueError(f"Character profile not found on VS Battles Wiki for '{name}'")

        # 3. PARSE WITH LLM
        prompt, system = self.prompt_manager.get_prompt("vs_battle_parser", wikitext=wikitext[:5000]) # Limit context
        
        character = self._safe_generate_structured(
            prompt=prompt,
            system_prompt=system,
            response_model=CombatCharacter
        )
        
        # 4. ENRICH & VALIDATE
        # If the image was missing from API query but present in result, or vice versa
        character.image_url = image_url or character.image_url
        character.wiki_url = wiki_url
        
        # Crucial: if the LLM hallucinated the name because it was empty in the schema, fix it
        if not character.name or character.name in ["Unknown", "Nom du personnage"]:
            character.name = target_name
        
        # Normalize tier value
        if character.stats:
            character.stats.tier_value = self._map_tier_to_value(character.stats.tier)
            logger.info(f"✅ Extracted: {character.name} (Tier {character.stats.tier})")
        
        return character

    def _map_tier_to_value(self, tier_str: str) -> int:
        """
        Maps a VS Battles Wiki tier string to a numeric value (0-100).
        """
        if not tier_str:
            return 0
        
        # Nettoyage manuel au lieu de regex
        t = tier_str.upper()
        t = t.replace("{{", "").replace("}}", "")
        
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
        
        # 3. Numeric tiers (simple check)
        if " 0 " in t or t.startswith("0 "): return 100
        if " 5 " in t or t.startswith("5 "): return 45
        if " 6 " in t or t.startswith("6 "): return 40
        if " 7 " in t or t.startswith("7 "): return 30
        if " 8 " in t or t.startswith("8 "): return 20
        if " 9 " in t or t.startswith("9 "): return 10
        if " 10 " in t or t.startswith("10 "): return 5
        
        return 0

    def _extract_max_tier(self, tier_str: str) -> str:
        """
        Parses complex tier strings (e.g., '9-B | 8-C') and returns the highest tier string.
        """
        # Split by likely separators
        parts = re.split(r'\||OR|AND', tier_str, flags=re.IGNORECASE)
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
        
        class JudgeVerdict(BaseModel):
            analysis: str
            verdict: str
            winner: str
            confidence: float

        verdict_data = self._safe_generate_structured(
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

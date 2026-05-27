import logging
import json
import re as _regex_module
import difflib
from typing import Dict, Any, List, Type, TypeVar, Optional

from pydantic import BaseModel, ConfigDict, Field
from src.core.domain.entities.ai_schemas import (
    CombatCharacter, CombatStats, CombatResult, DebateTurn
)
from src.core.ports.fandom_port import FandomPort
from src.core.ports.inference_port import InferencePort
from src.core.ports.web_search_port import WebSearchPort
from src.core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix." + __name__)

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
        Normalizes common Japanese/English spelling variations and removes wiki suffixes.
        Example: Power (Chainsaw Man) -> power, Tanjirou -> tanjiro
        """
        import re
        n = name.lower()
        # Remove everything in parentheses (common wiki suffix)
        n = re.sub(r'\(.*?\)', '', n)
        # Handle 'ou' -> 'o' (Gojou -> Gojo, Tanjirou -> Tanjiro)
        n = n.replace('ou', 'o').replace('uu', 'u')
        return n.strip()

    def _is_name_match(self, requested_name: str, found_title: str, loose: bool = False) -> bool:
        """
        Determines if a found wiki title belongs to the requested character.
        Strict by default, flexible in 'loose' mode.
        """
        req_norm = self._normalize_anime_name(requested_name)
        found_norm = self._normalize_anime_name(found_title)
        
        req_parts = [p for p in req_norm.split() if len(p) > 1]
        
        if loose:
            # --- LOOSE MODE (Rescue) ---
            if not req_parts: return True
            first_name_match = req_parts[0] in found_norm
            any_part_match = any(part in found_norm for part in req_parts)
            return first_name_match or any_part_match

        # --- STRICT MODE (Default) ---
        found_parts = [p for p in found_norm.split() if len(p) > 1]
        if all(part in found_norm for part in req_parts) or all(part in req_norm for part in found_parts):
            return True
            
        if req_parts and found_parts:
            similarity = difflib.SequenceMatcher(None, req_parts[0], found_parts[0]).ratio()
            if similarity > 0.8: return True
                
        if len(req_parts) >= 2 and len(found_parts) >= 2:
            if req_parts[0] in found_parts and req_parts[-1] in found_parts:
                return True

        return False

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly extracts JSON from LLM output, handling markdown code blocks and garbage.
        """
        try:
            # 1. Try direct parse
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # 2. Try extraction from markdown block
            match = _regex_module.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, _regex_module.DOTALL | _regex_module.IGNORECASE)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    logger.warning(f"Handled error: {e}")
            
            # 3. Last ditch: try to find the first '{' and last '}'
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError as e:
                    logger.warning(f"Handled error: {e}")
            
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
        Fetches character data from Fandom and intelligently selects the most powerful 
        version belonging to that EXACT character.
        """
        versions = self.fetch_character_versions(name, franchise=franchise)
        if not versions:
            raise ValueError(f"Could not successfully parse any valid profile for '{name}'")
            
        # Return the one with highest tier_value
        return max(versions, key=lambda c: c.stats.tier_value if c.stats else -1)

    def fetch_character_versions(self, name: str, franchise: Optional[str] = None, loose_pass: bool = False) -> List[CombatCharacter]:
        """
        Fetches ALL valid character versions from Fandom.
        """
        pass_type = "RESCUE (Loose)" if loose_pass else "STRICT"
        logger.info(f"🔍 Finding Wiki versions for: {name} (Mode: {pass_type})")
        
        # 1. Multi-pass search queries
        search_queries = [
            f"{name} {franchise} VS Battles Wiki" if franchise and not loose_pass else f"{name} profile VS Battles Wiki",
            f"{name} VS Battles Wiki",
            # FINAL FALLBACK: Search for the series Verse page if dedicated profile is missing
            f"{franchise} Verse VS Battles Wiki" if loose_pass and franchise else None
        ]
        
        all_raw_data = []
        seen_titles = set()
        
        for query in search_queries:
            if not query: continue
            
            logger.info(f"🌐 Querying: {query}")
            candidates = self.fandom_port.fetch_character_data(query) 
            
            if candidates:
                for cand in candidates:
                    cand_name = cand.get('name', '')
                    if cand_name not in seen_titles:
                        if "Standard Format" in cand_name or "Powerscaling" in cand_name:
                            continue
                        
                        if self._is_name_match(name, cand_name, loose=loose_pass) or (loose_pass and "Verse" in cand_name):
                            if "Verse" in cand_name:
                                cand['name'] = f"{name} (Verse Estimate)"
                            all_raw_data.append(cand)
                            seen_titles.add(cand_name)
                
                if len(all_raw_data) >= 1: break

        # 2. TRIGGER RESCUE PASS IF NEEDED
        if not all_raw_data and not loose_pass:
            logger.info(f"🛟 No results for '{name}' in strict mode. Triggering Rescue Pass...")
            return self.fetch_character_versions(name, franchise=franchise, loose_pass=True)

        # 3. FINAL FALLBACK: AI GENERATED PROFILE (Synthetic)
        if not all_raw_data:
            logger.warning(f"🤖 Wiki page missing for '{name}'. Triggering Synthetic AI Generation...")
            try:
                gen_prompt, gen_system = self.prompt_manager.get_prompt(
                    "vs_battle_ai_generator",
                    name=name,
                    franchise=franchise or "Unknown"
                )
                synthetic_char = self._safe_generate_structured(
                    prompt=gen_prompt,
                    system_prompt=gen_system,
                    response_model=CombatCharacter
                )
                # Ensure identity
                synthetic_char.name = f"{name} (AI Generated)"
                synthetic_char.wiki_url = f"https://vsbattles.fandom.com/wiki/{name.replace(' ', '_')}"
                if synthetic_char.stats:
                    best_tier = self._extract_max_tier(synthetic_char.stats.tier)
                    synthetic_char.stats.tier_value = self._map_tier_to_value(best_tier)
                
                return [synthetic_char]
            except Exception as e:
                logger.error(f"❌ Failed to generate synthetic profile for {name}: {e}")
                return []

        parsed_versions = []
        for raw_data in all_raw_data:
            wikitext = raw_data.get("wikitext", "")
            wiki_url = raw_data.get("url", "")
            image_url = raw_data.get("image_url")
            page_title = raw_data.get("name", name)

            try:
                prompt, system = self.prompt_manager.get_prompt("vs_battle_parser", wikitext=wikitext[:5000])
                character = self._safe_generate_structured(
                    prompt=prompt,
                    system_prompt=system,
                    response_model=CombatCharacter
                )
                
                character.name = page_title
                character.wiki_url = wiki_url
                character.image_url = image_url or character.image_url
                
                if character.stats:
                    best_tier_str = self._extract_max_tier(character.stats.tier)
                    character.stats.tier_value = self._map_tier_to_value(best_tier_str)
                    
                    logger.info(f"✅ Parsed version: {character.name} (Tier {character.stats.tier} -> Value: {character.stats.tier_value})")
                    parsed_versions.append(character)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse version '{page_title}': {e}")
                continue
                
        return parsed_versions


    def _map_tier_to_value(self, tier_str: str) -> int:
        """
        Maps a VS Battles Wiki tier string or keyword to a numeric value (0-100) 
        following the official power scaling hierarchy with precise matching.
        """
        if not tier_str:
            return 0
        
        t = tier_str.upper()
        
        # 1. Official Tier Identifiers (The most reliable)
        # Order matters: check more specific (High/Low) before base
        tier_patterns = [
            (r"\b0\b", 100), (r"BOUNDLESS", 100),
            (r"\b1-A\b", 95), (r"OUTERVERSAL", 95),
            (r"HIGH 1-B", 92), (r"\b1-B\b", 90), (r"HYPERVERSAL", 90),
            (r"HIGH 1-C", 88), (r"\b1-C\b", 85), (r"COMPLEX MULTIVERSAL", 85),
            (r"HIGH 2-A", 82), (r"\b2-A\b", 80), (r"MULTIVERSAL\+", 80),
            (r"\b2-B\b", 75), (r"MULTIVERSAL", 75),
            (r"\b2-C\b", 70), (r"LOW MULTIVERSAL", 70),
            (r"HIGH 3-A", 68), (r"\b3-A\b", 65), (r"UNIVERSAL", 65),
            (r"\b3-B\b", 60), (r"MULTI-GALAXY", 60),
            (r"\b3-C\b", 58), (r"GALAXY", 58),
            (r"\b4-A\b", 55), (r"MULTI-SOLAR SYSTEM", 55),
            (r"\b4-B\b", 53), (r"COSMIC", 53), (r"SOLAR SYSTEM", 53),
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
            if _regex_module.search(pattern, t):
                return value
                
        return 0

    def _extract_max_tier(self, tier_str: str) -> str:
        """
        Parses complex tier strings and returns the strongest tier string.
        """
        # Séparateurs courants
        parts = _regex_module.split(r'\||,|/|AND|OR', tier_str, flags=_regex_module.IGNORECASE)
        best_tier = tier_str
        max_val = -1
        
        for part in parts:
            part = part.strip()
            # On ré-utilise le mapping pour comparer
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

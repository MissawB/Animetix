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

    def _is_franchise_match(self, franchise: str, categories: List[str], found_title: str) -> bool:
        """
        Validates if the found wiki page belongs to the requested franchise.
        """
        if not franchise:
            return True
            
        f_norm = franchise.lower()
        title_norm = found_title.lower()
        
        # 1. Check title (e.g. 'Power (Chainsaw Man)')
        if f_norm in title_norm:
            return True
            
        # 2. Check categories (e.g. 'Category:Chainsaw Man Characters')
        for cat in categories:
            cat_norm = cat.lower()
            if f_norm in cat_norm:
                return True
                
        return False

    def _is_name_match(self, requested_name: str, found_title: str, loose: bool = False, franchise_matched: bool = False) -> bool:
        """
        Determines if a found wiki title belongs to the requested character.
        If franchise is already matched, name validation is significantly loosened.
        """
        req_norm = self._normalize_anime_name(requested_name)
        found_norm = self._normalize_anime_name(found_title)
        
        req_parts = [p for p in req_norm.split() if len(p) > 1]
        found_parts = [p for p in found_norm.split() if len(p) > 1]
        
        if not req_parts or not found_parts:
            # Fallback for very short names
            return req_norm in found_norm or found_norm in req_norm

        # --- FRANCHISE-BOOSTED MATCH ---
        if franchise_matched:
            # If franchise matches, we only need the first name to match
            if req_parts[0] in found_norm or found_parts[0] in req_norm:
                return True

        # --- LAST NAME CONFLICT CHECK ---
        if len(req_parts) > 1 and len(found_parts) > 1:
            req_last = req_parts[-1]
            found_last = found_parts[-1]
            if req_last not in found_norm and found_last not in req_norm:
                similarity = difflib.SequenceMatcher(None, req_last, found_last).ratio()
                if similarity < 0.7:
                    logger.warning(f"❌ Name conflict: '{requested_name}' vs '{found_title}' (Last name mismatch)")
                    return False

        if loose:
            return req_parts[0] in found_norm or any(p in found_norm for p in req_parts)

        # --- STRICT MODE ---
        if all(part in found_norm for part in req_parts):
            return True
            
        similarity = difflib.SequenceMatcher(None, req_parts[0], found_parts[0]).ratio()
        if similarity > 0.85:
            return True
                
        return False

    def _recover_image(self, character_name: str, franchise: Optional[str]) -> Optional[str]:
        """
        Uses WebSearchPort to find an image URL if one is missing from the wiki.
        """
        if not self.web_search_port:
            return None
        
        logger.info(f"🖼️ [Image Recovery] Searching image for: {character_name}")
        try:
            query = f"{character_name} {franchise or ''} official portrait anime"
            results = self.web_search_port.search(query)
            for res in results[:5]:
                url = res.get('url', '')
                if any(ext in url.lower() for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                    return url
            return None
        except Exception as e:
            logger.warning(f"⚠️ Image recovery failed: {e}")
            return None

    def _extract_json(self, text: Any) -> Dict[str, Any]:
        """
        Robustly extracts JSON from LLM output, stripping all metadata/wrapping.
        Works with raw strings or dictionaries from the inference engine.
        """
        if isinstance(text, dict):
            logger.info("🧩 _extract_json received a dict, looking for nested data...")
            best = self._find_best_dict(text)
            return best or text

        logger.info(f"🧩 _extract_json parsing string (len: {len(str(text))})")
        
        def find_best_dict(obj: Any) -> Optional[Dict]:
            if isinstance(obj, dict):
                if any(k in obj for k in ["stats", "tier", "winner", "analysis", "abilities"]):
                    return obj
                for v in obj.values():
                    res = find_best_dict(v)
                    if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_best_dict(item)
                    if res: return res
            return None

        # 1. Basic cleaning
        cleaned_text = str(text).split("---")[0].strip()
        
        try:
            data = json.loads(cleaned_text)
            best = find_best_dict(data)
            if best: return best
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            # 2. Markdown/Regex Fallback
            match = _regex_module.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, _regex_module.DOTALL | _regex_module.IGNORECASE)
            if match:
                try:
                    data = json.loads(match.group(1))
                    best = find_best_dict(data)
                    return best or data
                except json.JSONDecodeError: pass
            
            # 3. Bruteforce bracket search
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}')
            if start != -1 and end != -1:
                try:
                    data = json.loads(cleaned_text[start:end+1])
                    best = find_best_dict(data)
                    return best or data
                except json.JSONDecodeError: pass
                
            raise ValueError(f"Could not extract valid JSON (len: {len(cleaned_text)})")

    def _find_best_dict(self, obj: Any) -> Optional[Dict]:
        """Helper to find the most likely data object in a nested structure."""
        if isinstance(obj, dict):
            if any(k in obj for k in ["stats", "tier", "winner", "analysis", "abilities"]):
                return obj
            for v in obj.values():
                res = self._find_best_dict(v)
                if res: return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_best_dict(item)
                if res: return res
        return None

    def _safe_generate_structured(self, prompt: str, system_prompt: str, response_model: Type[T]) -> T:
        """
        Tries generate_structured, but ALWAYS applies robust JSON extraction 
        to handle metadata like 'fusion_id' or markdown formatting.
        """
        try:
            logger.info(f"Attempting structured generation for {response_model.__name__}")
            # Get RAW response (could be string or dict)
            raw_response = self.inference_engine.generate(prompt, system_prompt=system_prompt, json_mode=True)
            
            # LOG RAW for debugging
            logger.debug(f"DEBUG RAW LLM RESPONSE: {raw_response}")
            
            # Robust extraction
            json_data = self._extract_json(raw_response)
            
            logger.info(f"✅ Extracted JSON keys: {list(json_data.keys())}")
            return response_model.model_validate(json_data)
        except Exception as e:
            logger.warning(f"Unified generation failed ({e}), attempting last-resort fallback...")
            # If everything fails, try one more time
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
        return max(versions, key=lambda c: c.stats.tier_value if c.stats else -1)

    def fetch_character_versions(self, name: str, franchise: Optional[str] = None, loose_pass: bool = False) -> List[CombatCharacter]:
        """
        Fetches ALL valid character versions from Fandom using an escalating multi-pass search.
        """
        pass_type = "RESCUE (Loose)" if loose_pass else "STRICT"
        logger.info(f"🔍 Finding Wiki versions for: {name} (Franchise: {franchise}, Mode: {pass_type})")
        
        # Multi-pass search queries: from very specific to broad
        search_queries = [
            f"{name} {franchise} VS Battles Wiki" if franchise and not loose_pass else None,
            f"{name} profile VS Battles Wiki",
            # Handle cases like Thorfinn Karlsefni -> Thorfinn OR Edward Elric -> Edward
            f"{name.split()[0]} {franchise} VS Battles Wiki" if franchise and len(name.split()) > 1 else None,
            # Broad search without franchise but with split
            f"{name.split()[0]} VS Battles Wiki" if len(name.split()) > 1 else None,
            # Broad search without 'profile' suffix
            f"{name} VS Battles Wiki",
            # FINAL FALLBACK: Search for the series Verse page
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
                        
                        # FRANCHISE VALIDATION
                        is_franchise_ok = self._is_franchise_match(franchise, cand.get('categories', []), cand_name)
                        
                        # NAME VALIDATION (boosted by franchise)
                        # We allow first name match if franchise matches
                        if self._is_name_match(name, cand_name, loose=loose_pass, franchise_matched=is_franchise_ok) or (loose_pass and "Verse" in cand_name):
                            if "Verse" in cand_name:
                                cand['name'] = f"{name} (Verse Estimate)"
                            all_raw_data.append(cand)
                            seen_titles.add(cand_name)
                
                # If we found direct character matches (not just verse), we can potentially stop
                if len([c for c in all_raw_data if "Verse" not in c['name']]) >= 1:
                    break

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
                # USE THE SAFE METHOD to avoid fusion_id errors
                synthetic_char = self._safe_generate_structured(
                    prompt=gen_prompt,
                    system_prompt=gen_system,
                    response_model=CombatCharacter
                )
                # Ensure identity and basic metadata
                synthetic_char.name = f"{name} (AI Generated)"
                synthetic_char.franchise = franchise
                synthetic_char.wiki_url = f"https://vsbattles.fandom.com/wiki/{name.replace(' ', '_')}"
                
                # RECOVER IMAGE
                synthetic_char.image_url = self._recover_image(name, franchise)
                
                if synthetic_char.stats:
                    best_tier = self._extract_max_tier(synthetic_char.stats.tier)
                    synthetic_char.stats.tier_value = self._map_tier_to_value(best_tier)
                
                return [synthetic_char]
            except Exception as e:
                logger.error(f"❌ Failed to generate synthetic profile for {name}: {e}")
                return []
# ... rest of file ...

        parsed_versions = []

        import time
        
        # 4. PARSE ALL CANDIDATES
        for raw_data in all_raw_data:
            wikitext = raw_data.get("wikitext", "")
            wiki_url = raw_data.get("url", "")
            image_url = raw_data.get("image_url")
            page_title = raw_data.get("name", name)

            try:
                # Truncate even more to avoid local LLM context overflow/timeout (3000 chars is plenty for stats)
                prompt, system = self.prompt_manager.get_prompt("vs_battle_parser", wikitext=wikitext[:3000])
                
                # BREATHING ROOM for local server
                time.sleep(1.0)
                
                character = self._safe_generate_structured(
                    prompt=prompt,
                    system_prompt=system,
                    response_model=CombatCharacter
                )
                
                character.name = page_title
                character.franchise = franchise
                character.wiki_url = wiki_url
                character.image_url = image_url or character.image_url
                
                # RECOVER IMAGE if wiki didn't provide one
                if not character.image_url:
                    character.image_url = self._recover_image(page_title, franchise)
                
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

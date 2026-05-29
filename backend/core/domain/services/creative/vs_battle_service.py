import logging
import json
import re as _regex_module
import difflib
import time
from typing import Dict, Any, List, Type, TypeVar, Optional

from pydantic import BaseModel, ConfigDict, Field
from backend.core.domain.entities.ai_schemas import (
    CombatCharacter, CombatStats, CombatResult, DebateTurn
)
from backend.core.ports.fandom_port import FandomPort
from backend.core.ports.inference_port import InferencePort
from backend.core.ports.web_search_port import WebSearchPort
from backend.core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.vs_battle")

T = TypeVar('T', bound=BaseModel)

class VsBattleService:
    """
    Service orchestrating VS Battles between characters using Fandom data and LLM debates.
    Cleaned version with robust search and metadata stripping.
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
        import re
        n = name.lower()
        n = re.sub(r'\(.*?\)', '', n)
        n = n.replace('ou', 'o').replace('uu', 'u')
        return n.strip()

    def _is_franchise_match(self, franchise: str, categories: List[str], found_title: str) -> bool:
        if not franchise: return True
        f_norm = franchise.lower()
        if f_norm in found_title.lower(): return True
        for cat in categories:
            if f_norm in cat.lower(): return True
        return False

    def _is_name_match(self, requested_name: str, found_title: str, loose: bool = False, franchise_matched: bool = False) -> bool:
        req_norm = self._normalize_anime_name(requested_name)
        found_norm = self._normalize_anime_name(found_title)
        req_parts = [p for p in req_norm.split() if len(p) > 1]
        found_parts = [p for p in found_norm.split() if len(p) > 1]
        
        if not req_parts or not found_parts: return req_norm in found_norm or found_norm in req_norm
        if franchise_matched:
            if req_parts[0] in found_norm or found_parts[0] in req_norm: return True

        if len(req_parts) > 1 and len(found_parts) > 1:
            req_last, found_last = req_parts[-1], found_parts[-1]
            if req_last not in found_norm and found_last not in req_norm:
                if difflib.SequenceMatcher(None, req_last, found_last).ratio() < 0.7:
                    logger.warning(f"❌ Name conflict: '{requested_name}' vs '{found_title}' (Last name mismatch)")
                    return False

        if loose: return req_parts[0] in found_norm or any(p in found_norm for p in req_parts)
        if all(part in found_norm for part in req_parts): return True
        if difflib.SequenceMatcher(None, req_parts[0], found_parts[0]).ratio() > 0.85: return True
        return False

    def _recover_image(self, character_name: str, franchise: Optional[str]) -> Optional[str]:
        if not self.web_search_port: return None
        logger.info(f"🖼️ [Image Recovery] Searching image for: {character_name}")
        try:
            results = self.web_search_port.search(f"{character_name} {franchise or ''} official portrait anime")
            for res in results[:5]:
                url = res.get('url', '')
                if any(ext in url.lower() for ext in ['.jpg', '.png', '.webp', '.jpeg']): return url
            return None
        except Exception as e:
            logger.warning(f"⚠️ Image recovery failed: {e}")
            return None

    def _extract_json(self, text: Any) -> Dict[str, Any]:
        """Ultra-robust recursive JSON extraction."""
        if isinstance(text, dict): return self._find_best_dict(text) or text
        cleaned_text = str(text).split("---")[0].strip()
        try:
            data = json.loads(cleaned_text)
            return self._find_best_dict(data) or (data if isinstance(data, dict) else {})
        except json.JSONDecodeError:
            match = _regex_module.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, _regex_module.DOTALL | _regex_module.IGNORECASE)
            if match:
                try:
                    data = json.loads(match.group(1))
                    return self._find_best_dict(data) or data
                except Exception as e:
                    logger.debug(f"JSON extraction fallback 1 failed: {e}")
            start, end = cleaned_text.find('{'), cleaned_text.rfind('}')
            if start != -1 and end != -1:
                try:
                    data = json.loads(cleaned_text[start:end+1])
                    return self._find_best_dict(data) or data
                except Exception as e:
                    logger.debug(f"JSON extraction fallback 2 failed: {e}")
            raise ValueError(f"Could not extract valid JSON (len: {len(cleaned_text)})")

    def _find_best_dict(self, obj: Any) -> Optional[Dict]:
        if isinstance(obj, dict):
            keys_to_match = ["name", "stats", "tier", "speed", "winner", "analysis", "abilities", "summary"]
            if len([k for k in keys_to_match if k in obj or k.capitalize() in obj]) >= 2: return obj
            for v in obj.values():
                res = self._find_best_dict(v)
                if res: return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_best_dict(item)
                if res: return res
        return None

    def _safe_generate_structured(self, prompt: str, system_prompt: str, response_model: Type[T]) -> T:
        try:
            logger.info(f"Attempting structured generation for {response_model.__name__}")
            raw = self.inference_engine.generate(prompt, system_prompt=system_prompt, json_mode=True)
            return response_model.model_validate(self._extract_json(raw))
        except Exception as e:
            logger.warning(f"Unified generation failed ({e}), attempting fallback...")
            raw = self.inference_engine.generate(prompt, system_prompt=system_prompt)
            return response_model.model_validate(self._extract_json(raw))

    def fetch_and_parse_character(self, name: str, franchise: Optional[str] = None) -> CombatCharacter:
        versions = self.fetch_character_versions(name, franchise=franchise)
        if not versions: raise ValueError(f"Could not successfully parse any valid profile for '{name}'")
        return max(versions, key=lambda c: c.stats.tier_value if c.stats else -1)

    def fetch_character_versions(self, name: str, franchise: Optional[str] = None, loose_pass: bool = False) -> List[CombatCharacter]:
        pass_type = "RESCUE (Loose)" if loose_pass else "STRICT"
        logger.info(f"🔍 Finding Wiki versions for: {name} (Franchise: {franchise}, Mode: {pass_type})")
        
        search_queries = [
            f"{name} {franchise} VS Battles Wiki" if franchise and not loose_pass else None,
            f"{name} profile VS Battles Wiki",
            f"{name.split()[0]} {franchise} VS Battles Wiki" if franchise and len(name.split()) > 1 else None,
            f"{name.split()[0]} VS Battles Wiki" if len(name.split()) > 1 else None,
            f"{name} VS Battles Wiki",
            f"{franchise} Verse VS Battles Wiki" if loose_pass and franchise else None
        ]
        
        all_raw_data, seen_titles = [], set()
        for query in search_queries:
            if not query: continue
            candidates = self.fandom_port.fetch_character_data(query) 
            if candidates:
                for cand in candidates:
                    cand_name = cand.get('name', '')
                    if cand_name not in seen_titles:
                        if "Standard Format" in cand_name or "Powerscaling" in cand_name: continue
                        is_franchise_ok = self._is_franchise_match(franchise, cand.get('categories', []), cand_name)
                        if self._is_name_match(name, cand_name, loose=loose_pass, franchise_matched=is_franchise_ok) or (loose_pass and "Verse" in cand_name):
                            if "Verse" in cand_name: cand['name'] = f"{name} (Verse Estimate)"
                            all_raw_data.append(cand)
                            seen_titles.add(cand_name)
                if len([c for c in all_raw_data if "Verse" not in c['name']]) >= 1: break

        if not all_raw_data and not loose_pass: return self.fetch_character_versions(name, franchise=franchise, loose_pass=True)

        if not all_raw_data:
            logger.warning(f"🤖 Wiki page missing for '{name}'. Triggering Synthetic AI Generation...")
            try:
                gen_prompt, gen_system = self.prompt_manager.get_prompt("vs_battle_ai_generator", name=name, franchise=franchise or "Unknown")
                synthetic_char = self._safe_generate_structured(prompt=gen_prompt, system_prompt=gen_system, response_model=CombatCharacter)
                synthetic_char.name, synthetic_char.franchise = f"{name} (AI Generated)", franchise
                synthetic_char.wiki_url = f"https://vsbattles.fandom.com/wiki/{name.replace(' ', '_')}"
                synthetic_char.image_url = self._recover_image(name, franchise)
                if synthetic_char.stats:
                    best_tier = self._extract_max_tier(synthetic_char.stats.tier)
                    synthetic_char.stats.tier_value = self._map_tier_to_value(best_tier)
                return [synthetic_char]
            except Exception as e:
                logger.error(f"❌ Failed to generate synthetic profile for {name}: {e}")
                return []

        parsed_versions = []
        for raw_data in all_raw_data:
            try:
                wt = raw_data.get("wikitext", "")
                
                # Intelligent Wikitext Extraction to capture stats often located deep in the page
                summary_part = wt[:1000] # Usually enough for the introduction
                
                # Look for the start of the stats block (usually begins with Tier:)
                stats_match = _regex_module.search(r"('''Tier:'''.*?)(?=\n==|\Z)", wt, _regex_module.IGNORECASE | _regex_module.DOTALL)
                if stats_match:
                    stats_part = stats_match.group(1)[:3000] # Get up to 3000 chars of stats
                    focused_wikitext = summary_part + "\n\n--- STATS SECTION ---\n" + stats_part
                else:
                    # Fallback to a broader search around "Speed:" or "Durability:" if "Tier:" is missing
                    alt_match = _regex_module.search(r"('''Speed:'''.*?)(?=\n==|\Z)", wt, _regex_module.IGNORECASE | _regex_module.DOTALL)
                    if alt_match:
                        focused_wikitext = summary_part + "\n\n--- STATS SECTION ---\n" + alt_match.group(1)[:3000]
                    else:
                        focused_wikitext = wt[:4000]

                prompt, system = self.prompt_manager.get_prompt("vs_battle_parser", wikitext=focused_wikitext)
                time.sleep(1.0)
                character = self._safe_generate_structured(prompt=prompt, system_prompt=system, response_model=CombatCharacter)
                character.name, character.franchise = raw_data.get("name", name), franchise
                character.wiki_url, character.image_url = raw_data.get("url", ""), raw_data.get("image_url") or character.image_url
                if not character.image_url: character.image_url = self._recover_image(character.name, franchise)
                if character.stats:
                    character.stats.tier_value = self._map_tier_to_value(self._extract_max_tier(character.stats.tier))
                    logger.info(f"✅ Parsed version: {character.name} (Value: {character.stats.tier_value})")
                    parsed_versions.append(character)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse version '{raw_data.get('name')}': {e}")
        return parsed_versions

    def _map_tier_to_value(self, tier_str: str) -> int:
        if not tier_str: return 0
        t = tier_str.upper()
        # Relaxed patterns: remove \b to match fragments in complex sentences
        tier_patterns = [
            (r"(?<!\d)0(?!\d)", 100), (r"BOUNDLESS", 100), (r"1-A", 95), (r"OUTERVERSAL", 95),
            (r"HIGH 1-B", 92), (r"1-B", 90), (r"HYPERVERSAL", 90), (r"HIGH 1-C", 88),
            (r"1-C", 85), (r"COMPLEX MULTIVERSAL", 85), (r"HIGH 2-A", 82), (r"2-A", 80),
            (r"MULTIVERSAL\+", 80), (r"2-B", 75), (r"MULTIVERSAL", 75), (r"2-C", 70),
            (r"LOW MULTIVERSAL", 70), (r"HIGH 3-A", 68), (r"3-A", 65), (r"UNIVERSAL", 65),
            (r"3-B", 60), (r"MULTI-GALAXY", 60), (r"3-C", 58), (r"GALAXY", 58),
            (r"4-A", 55), (r"MULTI-SOLAR SYSTEM", 55), (r"4-B", 53), (r"COSMIC", 53),
            (r"SOLAR SYSTEM", 53), (r"4-C", 50), (r"STAR", 50), (r"5-A", 48),
            (r"LARGE PLANET", 48), (r"5-B", 46), (r"PLANET", 46), (r"LOW 5-B", 45),
            (r"5-C", 44), (r"MOON", 44), (r"6-A", 42), (r"LARGE CONTINENT", 42),
            (r"6-B", 40), (r"CONTINENT", 40), (r"HIGH 6-C", 39), (r"6-C", 38),
            (r"ISLAND", 38), (r"HIGH 7-A", 37), (r"7-A", 36), (r"LARGE MOUNTAIN", 36),
            (r"7-B", 34), (r"MOUNTAIN", 34), (r"7-C", 32), (r"TOWN", 32),
            (r"LOW 7-C", 31), (r"HIGH 8-A", 31), (r"8-A", 30), (r"MULTI-CITY BLOCK", 30),
            (r"8-B", 28), (r"CITY BLOCK", 28), (r"8-C", 26), (r"BUILDING", 26),
            (r"9-A", 24), (r"SMALL BUILDING", 24), (r"ROOM", 24), (r"9-B", 22),
            (r"WALL", 22), (r"9-C", 20), (r"STREET", 20), (r"10-A", 15), (r"ATHLETE", 15),
            (r"10-B", 10), (r"HUMAN", 10), (r"10-C", 5)
        ]
        for pattern, value in tier_patterns:
            if _regex_module.search(pattern, t): 
                logger.debug(f"🎯 Matched tier {pattern} -> {value}")
                return value
        return 0

    def _extract_max_tier(self, tier_str: str) -> str:
        parts = _regex_module.split(r'\||,|/|AND|OR', tier_str, flags=_regex_module.IGNORECASE)
        best_tier, max_val = tier_str, -1
        for part in parts:
            val = self._map_tier_to_value(part.strip())
            if val > max_val: max_val, best_tier = val, part
        return best_tier.strip()

    def run_battle(self, char_a_name: str, char_b_name: str, char_a_franchise: Optional[str] = None, char_b_franchise: Optional[str] = None, language: str = "Français") -> CombatResult:
        logger.info(f"Starting battle: {char_a_name} vs {char_b_name}")
        char_a = self.fetch_and_parse_character(char_a_name, franchise=char_a_franchise)
        char_b = self.fetch_and_parse_character(char_b_name, franchise=char_b_franchise)
        debate_history = []
        for role, c, o in [("Advocate_A", char_a, char_b), ("Advocate_B", char_b, char_a)]:
            p, s = self.prompt_manager.get_prompt("vs_battle_advocate", character_name=c.name, opponent_name=o.name, character_stats=c.stats.model_dump_json(indent=2), opponent_stats=o.stats.model_dump_json(indent=2), language=language)
            arg = self.inference_engine.generate(p, system_prompt=s)
            debate_history.append(DebateTurn(agent=role, content=arg))
        
        prompt_j, system_j = self.prompt_manager.get_prompt("vs_battle_judge", character_a_name=char_a.name, character_b_name=char_b.name, character_a_stats=char_a.stats.model_dump_json(indent=2), character_b_stats=char_b.stats.model_dump_json(indent=2), advocate_a_argument=debate_history[0].content, advocate_b_argument=debate_history[1].content, language=language)
        
        class JudgeVerdict(BaseModel):
            analysis: str
            verdict: str
            winner: str
            confidence: float
            model_config = ConfigDict(extra='ignore')

        verdict_data = self._safe_generate_structured(prompt=prompt_j, system_prompt=system_j, response_model=JudgeVerdict)
        debate_history.append(DebateTurn(agent="Judge", content=f"{verdict_data.analysis}\n\nVERDICT: {verdict_data.verdict}"))
        return CombatResult(character_a=char_a, character_b=char_b, debate_history=debate_history, winner=verdict_data.winner, verdict_summary=verdict_data.verdict)

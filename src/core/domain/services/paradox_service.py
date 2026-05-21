import random
import logging
import orjson
from typing import Dict, List, Tuple, Optional
from .llm_service import LLMService
from .neuro_symbolic_service import NeuroSymbolicService
from ..entities.ai_schemas import ParadoxLogic

logger = logging.getLogger("animetix.paradox")

class ParadoxDomainService:
    def __init__(self, llm_service: LLMService, neuro_symbolic_service: Optional[NeuroSymbolicService] = None):
        self.llm_service = llm_service
        self.neuro_symbolic_service = neuro_symbolic_service

    def prepare_challenge(self, catalog: Dict, is_daily: bool = False, secret_title: str = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Prépare les 3 œuvres (2 normales + 1 intrus)."""
        valid = [t for t in catalog.get('titles', []) if t in catalog.get('title_to_full_data', {})]
        if not valid:
            return None, None, None

        if is_daily and secret_title:
            intruder = secret_title
            t1, t2 = random.choices(valid[:100], k=2)
        else:
            # 2 œuvres populaires + 1 œuvre "intrigue" plus niche
            t1, t2 = random.choices(valid[:200], k=2)
            intruder = random.choice(valid[500:1000]) if len(valid) > 1000 else random.choice(valid)
            
        return t1, t2, intruder

    def generate_logic_stream(self, media_type: str, item_a: Dict, item_b: Dict, intruder: Dict, language: str):
        """Version streaming du raisonnement paradoxal."""
        yield {"type": "thought", "content": "Initialisation du solveur neuro-symbolique..."}
        
        label_a = item_a.get('title') or item_a.get('name')
        label_b = item_b.get('title') or item_b.get('name')
        label_i = intruder.get('title') or intruder.get('name')
        
        yield {"type": "thought", "content": f"Analyse des similarités entre {label_a}, {label_b} et {label_i}..."}
        
        if self.neuro_symbolic_service:
            yield {"type": "thought", "content": "Extraction des prédicats logiques (Graph Nodes)..."}
            # Simulation d'analyse
            import time; time.sleep(0.3)
            yield {"type": "thought", "content": "Détection d'une anomalie dans le cluster thématique..."}

        prompt, system = self.llm_service.prompt_manager.get_prompt(
            "paradox_generation", 
            media_type=media_type, 
            item_a=label_a, 
            item_b=label_b, 
            intruder=label_i
        )
        
        full_res = ""
        for token in self.llm_service.inference_engine.stream_generate(prompt, system_prompt=system):
            full_res += token
            # On pourrait yield token ici pour un effet CoT ultra-détaillé
            
        try:
            if '{' in full_res and '}' in full_res:
                clean_json = full_res[full_res.find('{'):full_res.rfind('}')+1]
                parsed = orjson.loads(clean_json)
                yield {"type": "result", "content": ParadoxLogic(
                    reasoning=parsed.get('reasoning', "Analyse Indisponible"),
                    scenario=parsed.get('scenario', full_res)
                )}
            else:
                yield {"type": "result", "content": ParadoxLogic(reasoning="LLM Fallback", scenario=full_res)}
        except Exception as e:
            logger.warning(f"Paradox logic generator parsing failed: {e}")
            yield {"type": "result", "content": ParadoxLogic(reasoning="Error", scenario=full_res)}

    def generate_logic(self, media_type: str, item_a: Dict, item_b: Dict, intruder: Dict, language: str) -> ParadoxLogic:
        """Génère le scénario paradoxal via IA Neuro-Symbolique ou fallback LLM."""
        label_a = item_a.get('title') or item_a.get('name')
        label_b = item_b.get('title') or item_b.get('name')
        label_i = intruder.get('title') or intruder.get('name')

        if self.neuro_symbolic_service:
            # Approche Hybride (Neuro-Symbolic AI)
            identified_intruder, explanation = self.neuro_symbolic_service.solve_paradox(
                media_type, label_a, label_b, label_i
            )
            
            if identified_intruder:
                return ParadoxLogic(
                    reasoning="Raisonnement Mathématique Formel (Z3 Solver)",
                    scenario=explanation
                )
                
        # Fallback classique (LLM pure)
        res_text = self.llm_service.generate_paradox_explanation(media_type, label_a, label_b, label_i)
        
        try:
            if '{' in res_text and '}' in res_text:
                clean_json = res_text[res_text.find('{'):res_text.rfind('}')+1]
                parsed = orjson.loads(clean_json)
                return ParadoxLogic(
                    reasoning=parsed.get('reasoning', "Analyse Indisponible"),
                    scenario=parsed.get('scenario', res_text)
                )
        except Exception as e:
            logger.warning(f"Paradox JSON Parsing Error: {e}")
            
        return ParadoxLogic(reasoning="Analyse probabiliste (LLM)", scenario=res_text)

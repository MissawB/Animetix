import logging
import random
from typing import Any, Dict, Optional, Tuple

import orjson
from core.ports.game_state_port import GameStatePort

from ..entities.ai_schemas import ParadoxLogic
from .llm_service import LLMService
from .neuro_symbolic_service import NeuroSymbolicService

logger = logging.getLogger("animetix.paradox")


class ParadoxDomainService:
    def __init__(
        self,
        llm_service: LLMService,
        neuro_symbolic_service: Optional[NeuroSymbolicService] = None,
    ):
        self.llm_service = llm_service
        self.neuro_symbolic_service = neuro_symbolic_service

    def get_state(self, port: GameStatePort) -> Dict[str, Any]:
        return {
            "answer": port.get("paradox_answer"),
            "options": port.get("paradox_options", []),
            "reasoning": port.get("paradox_reasoning"),
            "scenario": port.get("paradox_scenario"),
            "media": port.get("paradox_media", "Anime"),
            "is_daily": port.get("is_daily", False),
        }

    def save_state(self, port: GameStatePort, state: Dict[str, Any]):
        port.update(
            {
                "paradox_answer": state.get("answer"),
                "paradox_options": state.get("options"),
                "paradox_reasoning": state.get("reasoning"),
                "paradox_scenario": state.get("scenario"),
                "paradox_media": state.get("media"),
                "paradox_game_over": state.get("game_over", False),
            }
        )

    def prepare_challenge(
        self, catalog: Dict, is_daily: bool = False, secret_title: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Prépare les 3 œuvres (2 normales + 1 intrus)."""
        valid = [
            t
            for t in catalog.get("titles", [])
            if t in catalog.get("title_to_full_data", {})
        ]
        if not valid:
            return None, None, None

        if is_daily and secret_title:
            intruder = secret_title
            t1, t2 = random.choices(valid[:100], k=2)
        else:
            # 2 œuvres populaires + 1 œuvre "intrigue" plus niche
            t1, t2 = random.choices(valid[:200], k=2)
            intruder = (
                random.choice(valid[500:1000])
                if len(valid) > 1000
                else random.choice(valid)
            )

        return t1, t2, intruder

    def generate_logic_stream(
        self, media_type: str, item_a: Dict, item_b: Dict, intruder: Dict, language: str
    ):
        """Version streaming du raisonnement paradoxal."""
        yield {
            "type": "thought",
            "content": "Initialisation du solveur neuro-symbolique...",
        }

        label_a = item_a.get("title") or item_a.get("name")
        label_b = item_b.get("title") or item_b.get("name")
        label_i = intruder.get("title") or intruder.get("name")

        yield {
            "type": "thought",
            "content": f"Analyse des similarités entre {label_a}, {label_b} et {label_i}...",
        }

        if self.neuro_symbolic_service:
            yield {
                "type": "thought",
                "content": "Extraction des prédicats logiques (Graph Nodes)...",
            }
            # Simulation d'analyse
            import time

            time.sleep(0.3)  # noqa: E402
            yield {
                "type": "thought",
                "content": "Détection d'une anomalie dans le cluster thématique...",
            }

        prompt, system = self.llm_service.prompt_manager.get_prompt(
            "paradox_generation",
            media_type=media_type,
            item_a=label_a,
            item_b=label_b,
            intruder=label_i,
        )

        full_res = ""
        # Utilisation du Compact Reasoning Core pour le streaming
        for token in self.llm_service.stream_generate(
            prompt, system_prompt=system, use_slm=True
        ):
            full_res += token.text
            # On pourrait yield token ici pour un effet CoT ultra-détaillé

        try:
            if "{" in full_res and "}" in full_res:
                clean_json = full_res[full_res.find("{") : full_res.rfind("}") + 1]
                parsed = orjson.loads(clean_json)
                yield {
                    "type": "result",
                    "content": ParadoxLogic(
                        reasoning=parsed.get("reasoning", "Analyse Indisponible"),
                        scenario=parsed.get("scenario", full_res),
                    ),
                }
            else:
                yield {
                    "type": "result",
                    "content": ParadoxLogic(
                        reasoning="LLM Fallback (SLM)", scenario=full_res
                    ),
                }
        except Exception as e:
            logger.warning(f"Paradox logic generator parsing failed: {e}")
            yield {
                "type": "result",
                "content": ParadoxLogic(reasoning="Error", scenario=full_res),
            }

    def generate_logic(
        self, media_type: str, item_a: Dict, item_b: Dict, intruder: Dict, language: str
    ) -> ParadoxLogic:
        """Génère le scénario paradoxal via IA Neuro-Symbolique ou fallback LLM (SLM)."""
        label_a = item_a.get("title") or item_a.get("name") or ""
        label_b = item_b.get("title") or item_b.get("name") or ""
        label_i = intruder.get("title") or intruder.get("name") or ""

        if self.neuro_symbolic_service:
            # Approche Hybride (Neuro-Symbolic AI)
            identified_intruder, explanation, meta = (
                self.neuro_symbolic_service.solve_paradox(
                    media_type, label_a, label_b, label_i
                )
            )

            if identified_intruder:
                reasoning_type = (
                    "Formel (Z3 SAT)"
                    if meta.get("method") == "formal"
                    else "Heuristique (Mock SAT)"
                )
                return ParadoxLogic(
                    reasoning=f"Raisonnement {reasoning_type} via {meta.get('engine', 'Logic Solver')}",
                    scenario=explanation,
                )

        # Fallback classique (LLM pure via SLM pour la rapidité)
        res_text = self.llm_service.generate_paradox_explanation(
            media_type, label_a, label_b, label_i
        )

        try:
            if "{" in res_text and "}" in res_text:
                clean_json = res_text[res_text.find("{") : res_text.rfind("}") + 1]
                parsed = orjson.loads(clean_json)
                return ParadoxLogic(
                    reasoning=parsed.get("reasoning", "Analyse Indisponible"),
                    scenario=parsed.get("scenario", res_text),
                )
        except Exception as e:
            logger.warning(f"Paradox JSON Parsing Error: {e}")

        return ParadoxLogic(reasoning="Analyse probabiliste (SLM)", scenario=res_text)

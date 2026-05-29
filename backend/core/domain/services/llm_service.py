from typing import Optional, Dict, Type, Any
import logging
import orjson
from pydantic import BaseModel
from ...ports.inference_port import InferencePort

from ...ports.usage_port import UsagePort
from ..exceptions import InferenceError, ParsingError
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix." + __name__)

# --- OPENTELEMETRY TRACING ---
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    tracer = trace.get_tracer("animetix.llm_service")
except ImportError as e:
    logger.warning(f"Handled error: {e}")
    tracer = None

class LLMService:
    def __init__(
        self, 
        inference_engine: InferencePort, 
        prompt_manager: PromptManager, 
        usage_port: Optional[UsagePort] = None,
        slm_engine: Optional[InferencePort] = None,
        vision_engine: Optional[InferencePort] = None,
        obs_service = None
    ):
        self.inference_engine = inference_engine
        self.slm_engine = slm_engine or inference_engine # Fallback to main if no SLM
        self.vision_engine = vision_engine or inference_engine # Fallback to main if no Vision
        self.prompt_manager = prompt_manager
        self.usage_port = usage_port
        self.obs_service = obs_service

    def generate(self, prompt: str, system_prompt: str = "", forbidden_terms: list = None, use_slm: bool = False, thinking_budget: int = 0, thinking_mode: bool = False, user_id: int = None, tier: str = 'free') -> str:
        # --- QUOTA CHECK ---
        if not user_id:
            try:
                from animetix.middleware import get_current_user_id, get_current_user_tier
                user_id = get_current_user_id()
                tier = get_current_user_tier()
            except ImportError as e:
                logger.warning(f"Handled error: {e}")
                pass

        if user_id and self.usage_port:
            if not self.usage_port.check_quota(user_id, tier):
                from ..exceptions import QuotaExceededError
                raise QuotaExceededError("You have reached your daily AI limit.")

        import time
        start_time = time.time()

        span = None
        if tracer:
            span = tracer.start_span("LLMService.generate")
            span.set_attribute("llm.prompt", prompt[:1000])
            span.set_attribute("llm.system_prompt", system_prompt[:1000])
            span.set_attribute("llm.use_slm", use_slm)
            span.set_attribute("llm.thinking_mode", thinking_mode)
            span.set_attribute("llm.thinking_budget", thinking_budget)

        try:
            engine = self.slm_engine if use_slm else self.inference_engine
            res = engine.generate(prompt, system_prompt, thinking_budget=thinking_budget, thinking_mode=thinking_mode)
            latency = time.time() - start_time
            
            if not res:
                raise InferenceError("Engine returned empty response")
            
            if span:
                span.set_attribute("llm.response", res[:1000])
                span.set_attribute("llm.latency", latency)
                span.set_status(Status(StatusCode.OK))
                span.end()
                span = None
            
            # --- W&B OBSERVABILITY ---
            if self.obs_service:
                tokens = (len(prompt) + len(system_prompt) + len(res)) // 4
                model_id = getattr(engine, 'model_name', 'local-llama')
                self.obs_service.log_inference(model_id, latency, tokens, metadata={"slm": use_slm})

            # --- TOKEN TRACKING ---
            if self.usage_port:
                in_tokens = (len(prompt) + len(system_prompt)) // 4
                out_tokens = len(res) // 4
                
                engine_name = getattr(engine, 'model_name', 'brain-api')
                if use_slm: engine_name += "-slm"
                self.usage_port.log_usage(engine_name, in_tokens, out_tokens, user_id=user_id)

            # --- LLM GUARDRAILS (Sanitization) ---
            if forbidden_terms:
                import re
                for term in forbidden_terms:
                    if not term: continue
                    # Remplacement insensible à la casse avec regex
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    if pattern.search(res):
                        res = pattern.sub("[CENSURÉ]", res)
            
            return res
        except Exception as e:
            logger.error(
                f"AI Generation failed: {str(e)}", 
                extra={'context': {'prompt': prompt[:200], 'use_slm': use_slm}}
            )
            if span:
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                span.end()
            if type(e).__name__ == "InferenceTimeoutError":
                raise e
            raise InferenceError(f"AI Generation failed: {str(e)}", context={'original_error': str(e)})

    def generate_structured(self, prompt: str, schema: Type[BaseModel], system_prompt: str = "", use_slm: bool = False) -> Any:
        """Génère une réponse structurée (JSON) avec une tentative de correction automatique en cas d'échec."""
        res = self.generate(prompt, system_prompt=system_prompt, use_slm=use_slm)
        try:
            return self._parse_json(res, schema)
        except ParsingError as e:
            logger.warning(f"Initial JSON parsing failed, attempting retry: {e}")
            return self._retry_json(prompt, res, str(e), schema, system_prompt, use_slm)

    def _parse_json(self, text: str, schema: Type[BaseModel]) -> Any:
        try:
            # Extraction du bloc JSON si nécessaire
            if '{' in text and '}' in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
                data = orjson.loads(json_str)
                return schema.model_validate(data)
            else:
                raise ParsingError("No JSON block found in output")
        except Exception as e:
            raise ParsingError(f"Failed to parse or validate JSON: {str(e)}")

    def _retry_json(self, original_prompt: str, malformed_output: str, error_msg: str, schema: Type[BaseModel], system_prompt: str, use_slm: bool) -> Any:
        """Tente de corriger un JSON malformé en demandant explicitement une correction à l'IA."""
        fix_prompt = (
            f"Tu as précédemment retourné un JSON invalide. Voici l'erreur : {error_msg}\n"
            f"Voici ton contenu malformé :\n{malformed_output}\n\n"
            f"S'il te plaît, corrige-le et retourne UNIQUEMENT le JSON valide correspondant au schéma suivant :\n"
            f"{schema.model_json_schema()}"
        )
        
        # On utilise souvent un modèle plus rapide/robuste pour la correction
        res = self.generate(fix_prompt, system_prompt="Tu es un expert en correction de JSON. Retourne uniquement du JSON valide.", use_slm=use_slm)
        try:
            return self._parse_json(res, schema)
        except ParsingError as e:
            logger.error(f"JSON retry failed: {e}", extra={'context': {'output': res[:500]}})
            raise ParsingError(f"JSON recovery failed after retry: {str(e)}")

    def generate_fusion_scenario(self, media_type: str, item1: Dict, item2: Dict, language: str, chaos_level: int = 50, universe_balance: int = 50, art_style: str = "Cyberpunk") -> str:
        """Génère un synopsis de fusion avec des paramètres créatifs via PromptManager."""
        balance_instruction = ""
        if universe_balance < 40:
            balance_instruction = f"L'univers de {item1['title']} doit dominer."
        elif universe_balance > 60:
            balance_instruction = f"L'univers de {item2['title']} doit dominer."
        else:
            balance_instruction = "Les deux univers doivent être parfaitement équilibrés."
            
        chaos_instruction = "Garde un récit très logique et ancré dans le lore." if chaos_level < 30 else ("N'hésite pas à être abstrait et à briser le 4ème mur." if chaos_level > 70 else "Mélange les concepts de manière créative.")
        
        prompt, system = self.prompt_manager.get_prompt(
            "fusion_scenario", 
            media_type=media_type,
            item_a=item1['title'], 
            item_b=item2['title'],
            language=language,
            art_style=art_style,
            balance_instruction=balance_instruction,
            chaos_level=chaos_level,
            chaos_instruction=chaos_instruction
        )
        
        return self.generate(prompt, system_prompt=system, forbidden_terms=[item1['title'], item2['title']])

    def generate_paradox_explanation(self, media_type: str, item_a: str, item_b: str, intruder: str) -> str:
        prompt = self.prompt_manager.get_prompt("paradox_explanation", media_type=media_type, item_a=item_a, item_b=item_b, intruder=intruder)
        return self.generate(prompt, forbidden_terms=[item_a, item_b, intruder])

    def generate_emojis(self, media_type: str, title: str, description: str) -> str:
        prompt = self.prompt_manager.get_prompt("generate_emojis", media_type=media_type, title=title, description=description[:200])
        return self.generate(prompt)

    def ask_oracle(self, media_type: str, title: str, question: str, thinking_mode: bool = False) -> str:
        prompt, system = self.prompt_manager.get_prompt("ask_oracle", media_type=media_type, title=title, question=question)
        return self.generate(prompt, system, thinking_mode=thinking_mode)

    def ask_oracle_stream(self, media_type: str, title: str, question: str, thinking_mode: bool = False):
        """Version streaming de l'Oracle."""
        prompt, system = self.prompt_manager.get_prompt("ask_oracle", media_type=media_type, title=title, question=question)
        yield from self.inference_engine.stream_generate(prompt, system, thinking_mode=thinking_mode)

    def propose_next_question(self, media_type: str, history: str, candidates: list) -> str:
        prompt = self.prompt_manager.get_prompt("akinetix_next_question", media_type=media_type, history=history, candidates=candidates[:10])
        return self.generate(prompt)

    def generate_undercover_clue(self, media_type: str, item_a: str, item_b: str) -> str:
        prompt, system = self.prompt_manager.get_prompt("undercover_clue", media_type=media_type, item_a=item_a, item_b=item_b)
        return self.generate(prompt, system_prompt=system, forbidden_terms=[item_a, item_b])

    def explain_relationship(self, source_name: str, target_name: str, rel_type: str) -> str:
        prompt, system = self.prompt_manager.get_prompt("explain_link", source_name=source_name, target_name=target_name, rel_type=rel_type)
        return self.generate(prompt, system_prompt=system)

    def get_status(self) -> dict:
        return self.inference_engine.health_check()

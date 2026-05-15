from typing import Optional
from ...ports.inference_port import InferencePort
from ...ports.usage_port import UsagePort
from ..exceptions import InferenceError
from .prompt_manager import PromptManager

class LLMService:
    def __init__(
        self, 
        inference_engine: InferencePort, 
        prompt_manager: PromptManager, 
        usage_port: Optional[UsagePort] = None,
        slm_engine: Optional[InferencePort] = None,
        obs_service = None
    ):
        self.inference_engine = inference_engine
        self.slm_engine = slm_engine or inference_engine # Fallback to main if no SLM
        self.prompt_manager = prompt_manager
        self.usage_port = usage_port
        self.obs_service = obs_service

    def generate(self, prompt: str, system_prompt: str = "", forbidden_terms: list = None, use_slm: bool = False, thinking_budget: int = 0) -> str:
        import time
        start_time = time.time()
        try:
            engine = self.slm_engine if use_slm else self.inference_engine
            res = engine.generate(prompt, system_prompt, thinking_budget=thinking_budget)
            latency = time.time() - start_time
            
            if not res:
                raise InferenceError("Engine returned empty response")
            
            # --- W&B OBSERVABILITY ---
            if self.obs_service:
                tokens = (len(prompt) + len(system_prompt) + len(res)) // 4
                model_id = getattr(engine, 'model_name', 'local-llama')
                self.obs_service.log_inference(model_id, latency, tokens, metadata={"slm": use_slm})

            # --- TOKEN TRACKING ---
            if self.usage_port:
                in_tokens = (len(prompt) + len(system_prompt)) // 4
                out_tokens = len(res) // 4
                try:
                    from animetix.middleware import get_current_user_id
                    user_id = get_current_user_id()
                except ImportError:
                    user_id = None
                
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
            raise InferenceError(f"AI Generation failed: {str(e)}")

    def generate_fusion_scenario(self, media_type: str, item_a: str, item_b: str, language: str) -> str:
        prompt, system_prompt = self.prompt_manager.get_prompt("fusion_scenario", item_a=item_a, item_b=item_b, language=language, media_type=media_type)
        return self.generate(prompt, system_prompt, forbidden_terms=[item_a, item_b])

    def generate_paradox_explanation(self, media_type: str, item_a: str, item_b: str, intruder: str) -> str:
        prompt = self.prompt_manager.get_prompt("paradox_explanation", media_type=media_type, item_a=item_a, item_b=item_b, intruder=intruder)
        return self.generate(prompt, forbidden_terms=[item_a, item_b, intruder])

    def generate_emojis(self, media_type: str, title: str, description: str) -> str:
        prompt = self.prompt_manager.get_prompt("generate_emojis", media_type=media_type, title=title, description=description[:200])
        return self.generate(prompt)

    def ask_oracle(self, media_type: str, title: str, question: str) -> str:
        prompt = self.prompt_manager.get_prompt("ask_oracle", media_type=media_type, title=title, question=question)
        return self.generate(prompt)

    def propose_next_question(self, media_type: str, history: str, candidates: list) -> str:
        prompt = self.prompt_manager.get_prompt("akinetix_next_question", media_type=media_type, history=history, candidates=candidates[:10])
        return self.generate(prompt)

    def generate_undercover_clue(self, media_type: str, item_a: str, item_b: str) -> str:
        prompt = self.prompt_manager.get_prompt("undercover_clue", media_type=media_type, item_a=item_a, item_b=item_b)
        return self.generate(prompt, forbidden_terms=[item_a, item_b])

    def get_status(self) -> dict:
        return self.inference_engine.health_check()

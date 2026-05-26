import logging
import aiohttp
import asyncio
import os
from typing import Optional, List, Dict, Any, Generator
from core.ports.inference_port import InferencePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
transformers = lazy_import('transformers')
AutoModelForCausalLM = transformers.AutoModelForCausalLM
AutoTokenizer = transformers.AutoTokenizer
pipeline = transformers.pipeline

logger = logging.getLogger("animetix.inference.transformers")

class TransformersAdapter(InferencePort):
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.use_4bit = use_4bit
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    def _load_model(self):
        if self.model: return
        try:
            from transformers import BitsAndBytesConfig
            logger.info(f"🏗️ Loading Local Model: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            quantization_config = None
            if self.use_4bit:
                quantization_config = BitsAndBytesConfig(load_in_4bit=True)
                
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map="auto", 
                quantization_config=quantization_config,
                trust_remote_code=True
            )
        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        try:
            self._load_model()
        except Exception as e:
            raise InferenceError(f"Critical failure during model loading: {str(e)}")
            
        if not self.model: 
            raise InferenceError("Local Transformers model not loaded.")
        
        try:
            # Injection du prompt de réflexion
            if thinking_mode or thinking_budget > 0:
                prompt = f"<think>\nAnalyse en profondeur.\n</think>\n{prompt}"
                
            inputs = self.tokenizer(f"{system_prompt}\n\n{prompt}", return_tensors="pt").to(self.model.device)
            max_new_tokens = 512 + (thinking_budget if thinking_budget > 0 else 0)
            
            input_length = inputs.input_ids.shape[1]
            outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            generated_tokens = outputs[0][input_length:]
            return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        except Exception as e:
            raise InferenceError(f"Generation failed: {str(e)}")

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        try:
            yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)
        except InferenceError:
            raise

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
        found = [w for w in bad_words if w in text.lower()]
        is_safe = len(found) == 0
        return {
            "is_safe": is_safe,
            "detected_categories": found,
            "action": "block" if not is_safe else "allow"
        }

    def health_check(self) -> dict: return {"status": "online" if self.model else "offline", "engine": "transformers"}

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Implémentation du reranking SOTA avec sentence_transformers ou Cohere Rerank API (SOTA 2026)."""
        if not documents:
            return []
            
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {cohere_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "rerank-multilingual-v3.0",
                    "query": query,
                    "documents": documents
                }
                response = requests.post("https://api.cohere.ai/v1/rerank", headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    scores = [0.0] * len(documents)
                    for item in data.get("results", []):
                        idx = item.get("index")
                        if idx is not None and idx < len(scores):
                            scores[idx] = float(item.get("relevance_score", 0.0))
                    return scores
            except Exception as e:
                logger.error(f"❌ Cohere Rerank API connection failed: {e}.")

        from core.utils.lazy_import import lazy_import
        sentence_transformers = lazy_import('sentence_transformers')
        
        model_name = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        if not hasattr(self, '_cross_encoder') or getattr(self, '_cross_encoder_name', '') != model_name:
            self._cross_encoder = sentence_transformers.CrossEncoder(model_name)
            self._cross_encoder_name = model_name
            
        pairs = [[query, doc] for doc in documents]
        scores = self._cross_encoder.predict(pairs)
        return [float(score) for score in scores]

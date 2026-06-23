import logging
import os
from typing import Any, List, Optional

from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.exceptions import InferenceError
from core.ports.inference_port import InferencePort
from core.utils.lazy_import import lazy_import
from core.utils.model_registry import resolve_trust_remote_code, trusted_revision

torch = lazy_import("torch")
transformers = lazy_import("transformers")

from core.ports.usage_port import UsagePort  # noqa: E402

logger = logging.getLogger("animetix.inference.text")


class LocalTextAdapter(InferencePort):
    def __init__(
        self,
        model_id: str = "Qwen/Qwen3.5-4B",
        use_4bit: bool = True,
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.model: Any = None
        self.tokenizer: Any = None
        self._embedding_model: Any = None
        self.use_4bit = use_4bit

        # Speculative Decoding configuration
        self.speculative_enabled = (
            os.getenv("SPECULATIVE_DECODING", "True").lower() == "true"
        )
        self.draft_model_id = os.getenv("DRAFT_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
        self.draft_model: Any = None

        # Radix KV Cache configuration
        self.kv_cache_enabled = (
            os.getenv("KV_CACHE_RADIX_ATTENTION", "True").lower() == "true"
        )
        from core.utils.radix_cache import RadixCacheManager

        self.radix_cache = RadixCacheManager(max_nodes=16, min_prefix_len=10)

    def _load_model(self):
        if self.model:
            return
        try:
            from transformers import (
                AutoModelForCausalLM,  # noqa: E402
                AutoTokenizer,
                BitsAndBytesConfig,
            )

            logger.info(f"🏗️ Loading Local Text Model: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id, revision=trusted_revision(self.model_id) or "main"
            )
            quantization_config = (
                BitsAndBytesConfig(load_in_4bit=True) if self.use_4bit else None
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                revision=trusted_revision(self.model_id) or "main",
                device_map="auto",
                quantization_config=quantization_config,
                trust_remote_code=resolve_trust_remote_code(self.model_id),
            )

            # Load assistant model if speculative decoding is enabled
            if self.speculative_enabled and self.draft_model_id:
                logger.info(f"🏗️ Loading Draft Assistant Model: {self.draft_model_id}")
                self.draft_model = AutoModelForCausalLM.from_pretrained(
                    self.draft_model_id,
                    revision=trusted_revision(self.draft_model_id) or "main",
                    device_map="auto",
                    quantization_config=quantization_config,
                    trust_remote_code=resolve_trust_remote_code(self.draft_model_id),
                )
        except Exception as e:
            logger.error(f"❌ Failed to load local text model: {e}")
            raise InferenceError(
                f"Critical failure during text model loading: {str(e)}"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        self._load_model()
        try:
            if thinking_mode or thinking_budget > 0:
                prompt = f"<think>\nAnalyse en profondeur.\n</think>\n{prompt}"

            full_text = f"{system_prompt}\n\n{prompt}"
            token_ids = self.tokenizer.encode(full_text)
            input_length = len(token_ids)

            import torch

            device = self.model.device

            # Check Prefix KV Cache
            cached_pkv = None
            match_len = 0
            if self.kv_cache_enabled:
                cached_pkv, match_len = self.radix_cache.query(token_ids)

            generate_kwargs = {
                "max_new_tokens": 512 + thinking_budget,
                "return_dict_in_generate": True,
            }
            if self.draft_model:
                generate_kwargs["assistant_model"] = self.draft_model

            if cached_pkv is not None and match_len > 0:
                logger.info(f"⚡ [Radix KV Cache] Hit for prefix of length {match_len}")
                suffix_ids = token_ids[match_len:]

                # Build tensors for suffix tokens
                input_ids_tensor = torch.tensor(
                    [suffix_ids], dtype=torch.long, device=device
                )
                position_ids = torch.arange(
                    match_len,
                    match_len + len(suffix_ids),
                    dtype=torch.long,
                    device=device,
                ).unsqueeze(0)
                attention_mask = torch.ones(
                    1, match_len + len(suffix_ids), dtype=torch.long, device=device
                )

                generate_kwargs["position_ids"] = position_ids
                generate_kwargs["attention_mask"] = attention_mask
                generate_kwargs["past_key_values"] = cached_pkv

                outputs = self.model.generate(
                    input_ids=input_ids_tensor, **generate_kwargs
                )
            else:
                logger.info("🐢 [Radix KV Cache] Miss / full sequence computation")
                inputs = self.tokenizer(full_text, return_tensors="pt").to(device)
                outputs = self.model.generate(**inputs, **generate_kwargs)

            # Update Prefix KV Cache with computed prefix keys
            if self.kv_cache_enabled and hasattr(outputs, "past_key_values"):
                self.radix_cache.insert(token_ids, outputs.past_key_values)

            # Retrieve generated tokens
            if hasattr(outputs, "sequences"):
                sequences = outputs.sequences[0]
                if cached_pkv is not None and match_len > 0:
                    suffix_input_len = len(token_ids) - match_len
                    output_tokens = sequences[suffix_input_len:]
                else:
                    output_tokens = sequences[input_length:]
            else:
                output_tokens = outputs[0][input_length:]

            text = self.tokenizer.decode(
                output_tokens, skip_special_tokens=True
            ).strip()

            self._log_usage(
                engine=f"local:{self.model_id}",
                input_tokens=input_length,
                output_tokens=len(output_tokens),
                allocated_budget=thinking_budget,
            )

            return InferenceResponse(text=text)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise InferenceError(f"Text generation failed: {str(e)}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        yield self.generate(
            prompt, system_prompt, thinking_budget, thinking_mode, include_logprobs
        )

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding local via SentenceTransformer."""
        if not self._embedding_model:
            from sentence_transformers import SentenceTransformer  # noqa: E402

            logger.info("🏗️ Loading Local Embedding Model: all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        embedding = self._embedding_model.encode(text)

        self._log_usage(engine="local:all-MiniLM-L6-v2", units=1)

        return embedding.tolist()

    def health_check(self) -> dict:
        return {
            "status": "online" if self.model or self._embedding_model else "offline",
            "engine": "local_text",
        }

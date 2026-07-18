from typing import Dict, Optional

from core.utils.gemini_models import GEMINI_EMBEDDING, GEMINI_FLASH, GEMINI_LIVE


class PricingService:
    """
    Industrialized pricing registry for all AI models used in the project.
    Stores costs in USD per 1M tokens or per unit (image, audio request, etc.).
    """

    TIER_LIMITS = {
        "free": {"daily_tokens": 50000, "daily_requests": 30},
        "premium": {"daily_tokens": 1000000, "daily_requests": 500},
        "pro": {"daily_tokens": 10000000, "daily_requests": 5000},
    }

    # The runtime logs namespaced engines, e.g. "google_genai:gemini-3.5-flash:vision"
    # (see google_genai_adapter._log_usage). These provider prefixes and modality
    # suffixes are stripped when resolving a price (see _resolve_pricing) so the
    # cost estimate lands on the base model instead of the $0 fallback.
    _PROVIDER_PREFIXES = frozenset(
        {"google_genai", "transformers", "brain_api", "ollama", "moshi"}
    )
    _MODALITY_SUFFIXES = frozenset({"vision", "video", "audio"})

    def __init__(self):
        # Pricing registry: USD per 1M tokens or per unit
        self._registry: Dict[str, Dict[str, float]] = {
            # LLMs - USD / 1M tokens
            "Qwen/Qwen3.5-4B": {"input": 0.10, "output": 0.10},
            "Qwen/Qwen3-8B": {"input": 0.15, "output": 0.15},
            "Qwen/Qwen2.5-1.5B-Instruct": {"input": 0.07, "output": 0.07},
            "meta-llama/Llama-3-8B-Instruct": {"input": 0.15, "output": 0.15},
            "ollama/qwen3.5": {"input": 0.0, "output": 0.0},
            "ollama/llama3": {"input": 0.0, "output": 0.0},
            "HuggingFaceTB/SmolVLM-Instruct": {"input": 0.20, "output": 0.20},
            "Qwen/Qwen3-VL-8B-Instruct": {"input": 0.30, "output": 0.30},
            "moondream2": {"input": 0.50, "output": 0.50},
            # Cloud LLM actually used by the production chain [brain_api, google_genai].
            # Flash-tier estimates (USD/1M tokens); logged as "google_genai:<model>[:vision]".
            GEMINI_FLASH: {"input": 0.15, "output": 0.60},
            GEMINI_LIVE: {"input": 0.50, "output": 2.00},
            GEMINI_EMBEDDING: {"input": 0.15, "output": 0.0},
            "local-llama": {"input": 0.0, "output": 0.0},
            "brain-api": {"input": 1.0, "output": 2.0},
            "brain-api-slm": {"input": 0.1, "output": 0.1},
            # Generative Models - USD per Unit
            "black-forest-labs/FLUX.1-schnell": {
                "unit_cost": 0.03
            },  # High quality fast gen
            "stabilityai/sdxl-turbo": {"unit_cost": 0.01},  # Legacy fast gen
            "xtts-v2": {"unit_cost": 0.005},  # USD per voice cloning request
        }

    def _resolve_pricing(self, engine: str) -> Optional[Dict[str, float]]:
        """Look up pricing, tolerating the namespaced engine strings the runtime
        logs (e.g. "google_genai:gemini-3.5-flash:vision"). Tries an exact match
        first, then strips a known provider prefix and a trailing modality suffix
        and retries. Returns None if still unknown."""
        pricing = self._registry.get(engine)
        if pricing is not None:
            return pricing
        if ":" in engine:
            parts = engine.split(":")
            if parts[0] in self._PROVIDER_PREFIXES:
                parts = parts[1:]
            if parts and parts[-1] in self._MODALITY_SUFFIXES:
                parts = parts[:-1]
            return self._registry.get(":".join(parts))
        return None

    def calculate_cost(
        self, engine: str, input_tokens: int = 0, output_tokens: int = 0, units: int = 0
    ) -> float:
        """
        Calculates the estimated cost based on engine and usage metrics.
        """
        pricing = self._resolve_pricing(engine)
        if not pricing:
            # Fallback for unknown engines
            return 0.0

        # Unit-based pricing (Image, Audio, etc.)
        if "unit_cost" in pricing:
            return units * pricing["unit_cost"]

        # Token-based pricing
        input_rate = pricing.get("input", 0.0)
        output_rate = pricing.get("output", 0.0)

        cost = (input_tokens / 1_000_000 * input_rate) + (
            output_tokens / 1_000_000 * output_rate
        )

        return cost

    def get_pricing_info(self, engine: str) -> Optional[Dict[str, float]]:
        return self._registry.get(engine)

    def get_limits(self, tier: str) -> Dict[str, int]:
        """
        Retrieves daily limits for a given user tier.
        Defaults to 'free' tier if unknown.
        """
        return self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])

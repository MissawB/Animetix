from typing import Dict, Optional

class PricingService:
    """
    Industrialized pricing registry for all AI models used in the project.
    Stores costs in USD per 1M tokens or per unit (image, audio request, etc.).
    """
    def __init__(self):
        # Pricing registry: USD per 1M tokens or per unit
        self._registry: Dict[str, Dict[str, float]] = {
            # LLMs - USD / 1M tokens
            "Qwen/Qwen2.5-1.5B-Instruct": {"input": 0.07, "output": 0.07},
            "meta-llama/Llama-3-8B-Instruct": {"input": 0.15, "output": 0.15},
            "ollama/llama3": {"input": 0.0, "output": 0.0},
            "moondream2": {"input": 0.50, "output": 0.50},
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "local-llama": {"input": 0.0, "output": 0.0},
            "brain-api": {"input": 1.0, "output": 2.0},
            "brain-api-slm": {"input": 0.1, "output": 0.1},
            
            # Generative Models - USD per Unit
            "stabilityai/sdxl-turbo": {"unit_cost": 0.01}, # USD per image
            "xtts-v2": {"unit_cost": 0.005},             # USD per voice cloning request
        }

    def calculate_cost(
        self, 
        engine: str, 
        input_tokens: int = 0, 
        output_tokens: int = 0, 
        units: int = 0
    ) -> float:
        """
        Calculates the estimated cost based on engine and usage metrics.
        """
        pricing = self._registry.get(engine)
        if not pricing:
            # Fallback for unknown engines
            return 0.0
        
        # Unit-based pricing (Image, Audio, etc.)
        if "unit_cost" in pricing:
            return units * pricing["unit_cost"]
        
        # Token-based pricing
        input_rate = pricing.get("input", 0.0)
        output_rate = pricing.get("output", 0.0)
        
        cost = (input_tokens / 1_000_000 * input_rate) + \
               (output_tokens / 1_000_000 * output_rate)
        
        return cost

    def get_pricing_info(self, engine: str) -> Optional[Dict[str, float]]:
        return self._registry.get(engine)

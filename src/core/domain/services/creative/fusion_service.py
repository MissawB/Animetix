from typing import Dict, Optional
import logging
from ....ports.inference_port import InferencePort
from ..prompt_manager import PromptManager

logger = logging.getLogger('animetix.creative.fusion')

class FusionDomainService:
    """Domain service for universe fusion operations."""
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def generate_fusion_image(self, item_a: Dict, item_b: Dict, art_style: str = "Cyberpunk") -> Optional[str]:
        """
        Generates a fusion image based on two items and a specific style.
        Uses the inference engine's image generation capabilities if available.
        """
        title_a = item_a.get('title') or item_a.get('name', 'A')
        title_b = item_b.get('title') or item_b.get('name', 'B')
        
        prompt, _ = self.prompt_manager.get_prompt(
            "fusion_image", 
            title_a=title_a, 
            title_b=title_b, 
            art_style=art_style
        )
        
        try:
            # We assume the inference engine port might support image generation
            # If not, we return a themed placeholder or use a default URL pattern
            if hasattr(self.inference_engine, 'generate_image'):
                return self.inference_engine.generate_image(prompt)
            
            # Fallback/Mock implementation
            # In a real project, this would call a Stable Diffusion or DALL-E API
            return f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=576&nologo=true"
        except Exception as e:
            logger.error(f"Image Generation failed: {e}")
            return None

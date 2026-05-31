from typing import Dict, Optional
import logging
import os
from ....ports.inference_port import InferencePort
from ..prompt_manager import PromptManager
from ..multi_lora_manager import MultiLoraManager

logger = logging.getLogger('animetix.creative.fusion')

class FusionDomainService:
    """Domain service for universe fusion operations."""
    def __init__(self, 
                 inference_engine: InferencePort, 
                 prompt_manager: PromptManager,
                 lora_manager: Optional[MultiLoraManager] = None):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.lora_manager = lora_manager
        
        # Répertoire des adaptateurs LoRA (ex: data/models/loras/style_cyberpunk)
        self.lora_base_path = "data/models/loras"

    def generate_fusion_image(self, item_a: Dict, item_b: Dict, art_style: str = "Cyberpunk") -> Optional[str]:
        """
        Génère une image de fusion en utilisant dynamiquement un adaptateur LoRA si disponible.
        """
        title_a = item_a.get('title') or item_a.get('name', 'A')
        title_b = item_b.get('title') or item_b.get('name', 'B')
        
        # 1. Gestion du LoRA de style artistique
        if self.lora_manager:
            # Sécurité : On enlève tout caractère suspect pour éviter le path traversal
            safe_style = art_style.lower().replace(' ', '_').replace('.', '').replace('/', '').replace('\\', '')
            adapter_name = f"style_{safe_style}"
            adapter_path = os.path.join(self.lora_base_path, adapter_name)
            
            if os.path.exists(adapter_path):
                logger.info(f"🎨 Applying LoRA adapter for style: {art_style}")
                self.lora_manager.load_adapter(adapter_name, adapter_path)
                self.lora_manager.set_active_adapter(adapter_name)
            else:
                logger.debug(f"ℹ️ No specific LoRA found for {art_style}, using base model + prompt.")
                self.lora_manager.disable_adapters()

        # 2. Génération du prompt
        prompt, _ = self.prompt_manager.get_prompt(
            "fusion_image", 
            title_a=title_a, 
            title_b=title_b, 
            art_style=art_style
        )
        
        try:
            # 3. Appel au moteur d'inférence (qui utilise maintenant le modèle avec LoRA injecté)
            return self.inference_engine.generate_image(prompt)
        except Exception as e:
            logger.error(f"Image Generation failed: {e}")
            return None
        finally:
            # Libérer l'adaptateur pour ne pas polluer les prochaines générations
            if self.lora_manager:
                self.lora_manager.disable_adapters()

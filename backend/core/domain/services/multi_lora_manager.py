import logging
import os

from peft import PeftModel

logger = logging.getLogger("animetix")


class MultiLoraManager:
    """
    Système de Hot-Swapping Multi-LoRA.
    Permet de charger dynamiquement plusieurs adaptateurs (domaines ou styles)
    sur un seul modèle de base, sans réallocation de VRAM complète.
    """

    def __init__(self, base_model):
        self.base_model = base_model
        self.active_adapter = None
        self.loaded_adapters = {}

    def load_adapter(self, adapter_name: str, adapter_path: str):
        """Charge un adaptateur LoRA en mémoire s'il ne l'est pas déjà."""
        if adapter_name in self.loaded_adapters:
            return

        if not os.path.exists(adapter_path):
            logger.warning(f"⚠️ LoRA Adapter path not found: {adapter_path}")
            return

        logger.info(f"🔄 Loading LoRA Adapter: {adapter_name} from {adapter_path}")
        try:
            # Si le modèle de base n'est pas encore enveloppé par PEFT, on le fait avec le premier adaptateur
            if not isinstance(self.base_model, PeftModel):
                self.base_model = PeftModel.from_pretrained(
                    self.base_model, adapter_path, adapter_name=adapter_name
                )
            else:
                self.base_model.load_adapter(adapter_path, adapter_name=adapter_name)

            self.loaded_adapters[adapter_name] = adapter_path
        except Exception as e:
            logger.error(f"Failed to load LoRA Adapter '{adapter_name}': {e}")

    def set_active_adapter(self, adapter_name: str):
        """Active un adaptateur spécifique en quelques millisecondes."""
        if adapter_name not in self.loaded_adapters:
            logger.warning(f"⚠️ Adapter '{adapter_name}' not loaded. Keeping current.")
            return

        if self.active_adapter == adapter_name:
            return  # Déjà actif

        if isinstance(self.base_model, PeftModel):
            self.base_model.set_adapter(adapter_name)
            self.active_adapter = adapter_name
            logger.debug(f"⚡ Switched to LoRA Adapter: {adapter_name}")

    def disable_adapters(self):
        """Désactive tous les adaptateurs pour utiliser le modèle de base pur."""
        if isinstance(self.base_model, PeftModel):
            with self.base_model.disable_adapter():
                self.active_adapter = None
                logger.debug("⚡ Adapters disabled. Using base model.")

    def generate_with_adapter(self, adapter_name: str, **kwargs):
        """Génère du texte en activant temporairement un adaptateur."""
        self.set_active_adapter(adapter_name)
        return self.base_model.generate(**kwargs)

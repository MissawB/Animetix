import logging
from typing import List, Dict, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.guardrail")

class LocalGuardrailAdapter(InferencePort):
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
        found = [w for w in bad_words if w in text.lower()]
        is_safe = len(found) == 0
        
        if not is_safe:
            logger.warning(f"🚨 Content moderation triggered. Found: {found}")
            
        return {
            "is_safe": is_safe,
            "detected_categories": found,
            "action": "block" if not is_safe else "allow"
        }

    def health_check(self) -> dict:
        return {"status": "online", "engine": "local_guardrail"}

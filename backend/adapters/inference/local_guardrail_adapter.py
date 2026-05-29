import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from pydantic import BaseModel, Field

logger = logging.getLogger("animetix.inference.guardrail")

class ModerationResult(BaseModel):
    is_safe: bool = Field(..., description="True si le texte ne contient aucun contenu inapproprié, offensant ou spoiler.")
    detected_categories: List[str] = Field(..., description="Liste des catégories inappropriées détectées (ex: 'nsfw', 'violence', 'spoiler', 'hate_speech').")
    reason: str = Field(..., description="Explication concise de la décision de modération.")

class LocalGuardrailAdapter(InferencePort):
    def __init__(self, inference_engine: Optional[Any] = None):
        super().__init__()
        self.inference_engine = inference_engine

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        if self.inference_engine:
            try:
                categories_str = ", ".join(categories)
                prompt = (
                    f"Analyse le texte suivant pour détecter s'il contient du contenu inapproprié "
                    f"ou correspondant à l'une de ces catégories : {categories_str}.\n"
                    f"Texte : \"{text}\""
                )
                
                result = self.inference_engine.generate_structured(
                    prompt=prompt,
                    response_model=ModerationResult,
                    system_prompt="Tu es un agent de modération sémantique expert pour une plateforme Anime/Manga."
                )
                
                is_safe = result.is_safe
                detected = result.detected_categories
                action = "block" if not is_safe else "allow"
                
                if not is_safe:
                    logger.warning(f"🚨 Semantic content moderation triggered. Categories: {detected}. Reason: {result.reason}")
                    
                return {
                    "is_safe": is_safe,
                    "detected_categories": detected,
                    "action": action,
                    "reason": result.reason
                }
            except Exception as e:
                logger.warning(f"Failed semantic moderation check, falling back to keywords: {e}")

        # Fallback classique par mots-clés
        bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
        found = [w for w in bad_words if w in text.lower()]
        is_safe = len(found) == 0
        
        if not is_safe:
            logger.warning(f"🚨 Content moderation triggered (Keyword fallback). Found: {found}")
            
        return {
            "is_safe": is_safe,
            "detected_categories": found,
            "action": "block" if not is_safe else "allow",
            "reason": "Vérification par mots-clés effectuée."
        }

    def health_check(self) -> dict:
        return {"status": "online", "engine": "local_guardrail"}

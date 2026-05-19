import json
import logging
from typing import List, Dict, Any, Optional
from ...ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger('animetix.guardrail')

class GuardrailService:
    """
    Hallucination & Safety Guardrail.
    Utilise des modèles de modération (type Llama-Guard) ou un fallback LLM pour protéger l'utilisateur.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.enabled_categories = [
            "SPOILER", 
            "INAPPROPRIATE_CONTENT", 
            "HATE_SPEECH", 
            "HALLUCINATION_RISK"
        ]

    def _llm_moderate(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Fallback: utilise le LLM principal pour effectuer la modération via un prompt structuré."""
        logger.info(f"🛡️ [Guardrail] Running LLM-based moderation for: {text[:50]}...")
        
        prompt, system = self.prompt_manager.get_prompt(
            "content_moderator", 
            text=text, 
            categories=", ".join(categories)
        )
        
        try:
            response = self.inference_engine.generate(prompt, system_prompt=system)
            # Nettoyage basique du JSON si le LLM a ajouté du markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response)
            return result
        except Exception as e:
            logger.error(f"❌ [Guardrail] LLM Moderation failed: {e}")
            # En cas d'échec total, on autorise par défaut pour ne pas bloquer l'UX, 
            # ou on bloque si la sécurité est critique. Ici on autorise avec log.
            return {"is_safe": True, "action": "allow", "reasoning": "Fallback error recovery"}

    def validate_input(self, text: str) -> Dict[str, Any]:
        """Analyse la requête de l'utilisateur avant traitement."""
        result = self.inference_engine.moderate_content(text, categories=self.enabled_categories)
        
        # Si l'adaptateur ne fournit pas de résultat exploitable (stub ou vide)
        if not result or (not result.get("detected_categories") and result.get("is_safe") is True):
            # On vérifie si c'est vraiment un stub ou si c'est juste safe.
            # Dans le doute, pour les inputs utilisateurs, on peut forcer une validation LLM
            # si l'adaptateur est connu pour être un stub (ex: vLLM sans Llama-Guard).
            return self._llm_moderate(text, self.enabled_categories)
            
        return result

    def validate_output(self, response_text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Analyse la réponse générée avant affichage (Détection de spoilers/hallucinations)."""
        check_text = response_text
        if context:
            check_text = f"CONTEXTE: {context[:1000]}\nRÉPONSE: {response_text}"
            
        result = self.inference_engine.moderate_content(check_text, categories=self.enabled_categories)
        
        # Bascule vers LLM si l'adaptateur n'a rien détecté (pour assurer la détection de spoilers)
        if not result or not result.get("unsafe_categories"):
            result = self._llm_moderate(check_text, self.enabled_categories)
        
        # Logique spécifique aux spoilers
        if "SPOILER" in result.get("unsafe_categories", []):
            result["action"] = "mask"
            result["warning"] = "⚠️ Cette réponse contient potentiellement des spoilers."
            
        return result

class RedTeamingAgent:
    """
    Agent Adversaire (Red-Teaming).
    Génère des requêtes conçues pour tester les failles du RAG et de l'Oracle.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def generate_adversarial_queries(self, media_item: Dict) -> List[str]:
        """Génère des questions piégeuses basées sur les données d'une œuvre."""
        title = media_item.get('title', 'Inconnu')
        description = media_item.get('description', '')[:1000]
        
        prompt, system = self.prompt_manager.get_prompt(
            "red_teaming_generate", 
            title=title, 
            description=description
        )
        
        response = self.inference_engine.generate(prompt, system_prompt=system)
        return [q.strip() for q in response.split('\n') if len(q.strip()) > 10]

    def evaluate_vulnerability(self, query: str, response: str, ground_truth: str) -> Dict[str, Any]:
        """Évalue si l'agent a réussi à piéger l'IA."""
        prompt, system = self.prompt_manager.get_prompt(
            "red_teaming_eval", 
            query=query, 
            response=response, 
            ground_truth=ground_truth
        )
        eval_res = self.inference_engine.generate(prompt, system_prompt=system)
        return {
            "is_vulnerable": "OUI" in eval_res.upper(),
            "analysis": eval_res
        }

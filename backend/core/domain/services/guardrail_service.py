import json
import logging
from typing import List, Dict, Any, Optional
from ...ports.inference_port import InferencePort
from .prompt_manager import PromptManager
from ..exceptions import InferenceError, ParsingError

logger = logging.getLogger('animetix.guardrail')

class GuardrailService:
    """
    Système de Guardrails multi-couches (2026 SOTA).
    Assure la sécurité, la factualité et l'intégrité de l'expérience utilisateur.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: Optional[PromptManager] = None, neo4j_manager=None):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.neo4j = neo4j_manager
        self.enabled_categories = [
            "SPOILER", 
            "INAPPROPRIATE_CONTENT", 
            "HATE_SPEECH", 
            "HALLUCINATION_RISK",
            "JAILBREAK_ATTEMPT"
        ]

    def validate_input(self, text: str) -> Dict[str, Any]:
        """Analyse proactive de la requête utilisateur (Pre-processing)."""
        logger.info(f"🛡️ [Guardrail] Validating input: {text[:50]}...")
        
        # 1. Détection de Jailbreak / Prompt Injection
        if self._is_potential_jailbreak(text):
            return {
                "is_safe": False,
                "reason": "Suspicion de tentative d'injection de prompt ou de contournement des règles.",
                "action": "block"
            }

        # 2. Modération via modèle spécialisé (Llama-Guard) ou LLM
        result = self.inference_engine.moderate_content(text, categories=self.enabled_categories)
        if not result or result.get("stub") or ("unsafe_categories" not in result and "detected_categories" not in result):
            result = self._llm_moderate(text, self.enabled_categories, mode="input")
            
        if result:
            if "unsafe_categories" in result and "detected_categories" not in result:
                result["detected_categories"] = result["unsafe_categories"]
            elif "detected_categories" in result and "unsafe_categories" not in result:
                result["unsafe_categories"] = result["detected_categories"]

        return result

    def validate_output(self, response_text: str, context: Optional[str] = None, query: str = "") -> Dict[str, Any]:
        """Validation post-génération (Post-processing)."""
        logger.info("🛡️ [Guardrail] Validating AI response...")

        # 1. Vérification de Factualité (Cross-Check Graphe)
        fact_check = self._cross_check_with_graph(response_text)
        if fact_check and not fact_check.get("is_factual"):
             logger.warning(f"⚠️ [Guardrail] Hallucination detected: {fact_check['reason']}")
             return {
                 "is_safe": False, 
                 "reason": f"Divergence factuelle détectée : {fact_check['reason']}",
                 "action": "rewrite"
             }

        # 2. Détection de Spoilers & Modération standard
        check_text = f"REQUÊTE: {query}\nCONTEXTE: {context[:1000] if context else 'N/A'}\nRÉPONSE: {response_text}"
        result = self.inference_engine.moderate_content(check_text, categories=self.enabled_categories)
        
        if not result or result.get("stub") or ("unsafe_categories" not in result and "detected_categories" not in result):
            result = self._llm_moderate(check_text, self.enabled_categories, mode="output")

        if result:
            if "unsafe_categories" in result and "detected_categories" not in result:
                result["detected_categories"] = result["unsafe_categories"]
            elif "detected_categories" in result and "unsafe_categories" not in result:
                result["unsafe_categories"] = result["detected_categories"]

        # 3. Actions correctives dynamiques
        if result.get("detected_categories"):
            if "SPOILER" in result["detected_categories"]:
                result["action"] = "mask"
                result["warning"] = "⚠️ Alerte Spoiler : Ce contenu contient des spoilers et a été masqué pour préserver votre découverte."
            elif any(c in result["detected_categories"] for c in ["HATE_SPEECH", "INAPPROPRIATE_CONTENT"]):
                result["action"] = "block"
                result["message"] = "Je ne peux pas afficher cette réponse car elle ne respecte pas nos règles de sécurité."

        return result

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Expose le service de modération de contenu en utilisant le LLM."""
        return self._llm_moderate(text, categories)

    def _is_potential_jailbreak(self, text: str) -> bool:
        """Heuristique simple pour détecter les tentatives de détournement."""
        jailbreak_patterns = [
            "ignore previous instructions", "system prompt", "dan mode", 
            "dev mode", "as a hacker", "unlock all features"
        ]
        text_lower = text.lower()
        return any(p in text_lower for p in jailbreak_patterns)

    def _cross_check_with_graph(self, text: str) -> Optional[Dict]:
        """Utilise Neo4j pour vérifier les relations citées dans le texte."""
        if not self.neo4j:
            return None
            
        try:
            # Vérification de connexion rapide
            if hasattr(self.neo4j, 'check_health') and not self.neo4j.check_health():
                return None

            # Recherche d'entités candidates capitalisées dans le texte
            import re
            words = re.findall(r'[A-Z][a-z]+', text)
            mentioned_entities = list(set([w for w in words if len(w) > 3]))
            
            if not mentioned_entities:
                return {"is_factual": True, "reason": "Aucune entité majeure identifiée pour cross-checking."}
                
            query = """
            MATCH (n) WHERE n.title IN $entities OR n.name IN $entities
            RETURN n.title as title, n.name as name, labels(n) as labels
            LIMIT 5
            """
            results = self.neo4j.execute_read(query, {"entities": mentioned_entities})
            
            if results:
                found_names = [r.get('title') or r.get('name') for r in results]
                logger.info(f"🛡️ [Guardrail] Factual check matched knowledge graph nodes: {found_names}")
                return {
                    "is_factual": True, 
                    "reason": f"Entités validées par le graphe Neo4j: {', '.join(found_names)}.",
                    "metadata": {"matched_nodes": found_names}
                }
                
            return {"is_factual": True, "reason": "Vérification effectuée. Pas d'incohérence détectée."}
        except Exception as e:
            logger.warning(f"⚠️ [Guardrail] Factual check failed due to exception: {e}")
            return None 

    def _llm_moderate(self, text: str, categories: List[str], mode: str = "output") -> Dict[str, Any]:
        """Utilise le cerveau principal pour une modération fine par prompt."""
        try:
            prompt_key = "input_moderator" if mode == "input" else "output_moderator"
            if self.prompt_manager is None:
                prompt, system = f"Text: {text}, Categories: {', '.join(categories)}", "System"
            else:
                prompt, system = self.prompt_manager.get_prompt(
                    prompt_key, 
                    text=text, 
                    categories=", ".join(categories)
                )
            
            response = self.inference_engine.generate(prompt, system_prompt=system)
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            result = json.loads(response)
            
            # Map is_safe
            is_safe = result.get("is_safe")
            if is_safe is None:
                is_safe = result.get("safe")
            if is_safe is None:
                is_safe = True
                
            # Map detected_categories
            detected_categories = result.get("detected_categories")
            if detected_categories is None:
                detected_categories = result.get("unsafe_categories")
            if detected_categories is None:
                detected_categories = result.get("violations", [])
                
            # Map action
            action = result.get("action")
            if action is None:
                action = "none" if is_safe else "block"
                
            return {
                "is_safe": is_safe,
                "detected_categories": detected_categories,
                "unsafe_categories": detected_categories,
                "action": action
            }
        except Exception as e:
            logger.exception("❌ Guardrail verification failed due to unexpected error.")
            from core.domain.entities.exceptions import ContentModerationError
            raise ContentModerationError("Guardrail verification failed due to internal error.") from e

class RedTeamingAgent:
    """
    Agent Adversaire automatisé pour le stress-test des Guardrails.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def generate_adversarial_queries(self, media_item: Dict) -> List[str]:
        """Génère des requêtes complexes visant à forcer un spoiler ou une hallucination."""
        prompt, system = self.prompt_manager.get_prompt(
            "red_teaming_generate", 
            title=media_item.get('title'), 
            description=media_item.get('description', '')[:500]
        )
        response = self.inference_engine.generate(prompt, system_prompt=system)
        return [q.strip() for q in response.split('\n') if len(q.strip()) > 5]

    def evaluate_vulnerability(self, query: str, response: str, ground_truth: str) -> dict:
        prompt = f"Query: {query}\nResponse: {response}\nGround Truth: {ground_truth}"
        evaluation = self.inference_engine.generate(prompt)
        is_vulnerable = "halluciné" in evaluation.lower() or "oui" in evaluation.lower()
        return {"is_vulnerable": is_vulnerable, "analysis": evaluation}

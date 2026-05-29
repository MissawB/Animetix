from typing import List, Dict, Optional
import orjson
import logging
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager
from ..entities.ai_schemas import CoVePlan

logger = logging.getLogger("animetix.oracle")

class CoveOracleService:
    """
    Implémentation de Chain-of-Verification (CoVe).
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, neo4j_manager=None):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.neo4j_manager = neo4j_manager

    def answer_with_verification(self, question: str, media_type: str) -> str:
        """
        Processus CoVe complet.
        """
        logger.info(f"🛡️ CoVe: Processing question: '{question}'")
        
        # Étape 1 : Générer une réponse initiale (Baseline)
        baseline_prompt = self.prompt_manager.get_prompt("cove_baseline", media_type=media_type, question=question)
        baseline_response = self.inference_engine.generate(baseline_prompt)
        
        # Étape 2 : Planification des vérifications (Deconstruct claims)
        plan_prompt, plan_system = self.prompt_manager.get_prompt("cove_plan", baseline_response=baseline_response)
        plan_data = self._safe_json_generate(plan_prompt, system_prompt=plan_system)
        
        try:
            plan = CoVePlan(**plan_data)
            verification_questions = plan.verification_questions
        except Exception as e:
            logger.warning(f"CoVe plan parsing failed: {e}")
            verification_questions = []
        
        if not verification_questions:
            return baseline_response
            
        logger.info(f"🔍 CoVe: Verifying {len(verification_questions)} claims...")
        
        # Étape 3 : Exécution des vérifications (contre le Graphe)
        verified_facts = []
        for v_question in verification_questions:
            # On demande au LLM d'extraire les entités de la question de vérification
            ent_prompt = self.prompt_manager.get_prompt("cove_entities", v_question=v_question)
            entities = [e.strip() for e in self.inference_engine.generate(ent_prompt).split(',')]
            
            # Interrogation de Neo4j (GraphRAG)
            graph_context = ""
            if self.neo4j_manager:
                for ent in entities:
                    ctx = self.neo4j_manager.get_creator_network_context(ent)
                    if "Pas de données" not in ctx:
                        graph_context += f"{ctx}\n"
            
            # Évaluation du fait avec le contexte vérifié
            eval_prompt = self.prompt_manager.get_prompt("cove_eval", v_question=v_question, graph_context=graph_context)
            fact_check = self.inference_engine.generate(eval_prompt)
            verified_facts.append(f"Fait vérifié ({v_question}) : {fact_check}")

        # Étape 4 : Génération de la réponse finale révisée
        final_prompt, final_system = self.prompt_manager.get_prompt("cove_final", question=question, baseline_response=baseline_response, verified_facts=" ".join(verified_facts))
        
        logger.info("✅ CoVe: Generating final verified response.")
        return self.inference_engine.generate(final_prompt, system_prompt=final_system)

    def _safe_json_generate(self, prompt: str, system_prompt: str = "Réponds UNIQUEMENT en JSON.") -> Dict:
        res = self.inference_engine.generate(prompt, system_prompt=system_prompt)
        try:
            if '{' in res and '}' in res:
                return orjson.loads(res[res.find('{'):res.rfind('}')+1])
        except Exception as e:
            logger.warning(f"CoVe JSON Parsing Error: {e}")
        return {}

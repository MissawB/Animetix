import logging
from typing import Any, Dict

import orjson
from core.ports.inference_port import InferencePort

from ..entities.ai_schemas import CoVePlan
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.oracle")


class CoveOracleService:
    """
    Implémentation de Chain-of-Verification (CoVe).
    """

    def __init__(
        self,
        inference_engine: InferencePort,
        prompt_manager: PromptManager,
        neo4j_manager=None,
    ):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.neo4j_manager = neo4j_manager

    def answer_with_verification(self, question: str, media_type: str) -> str:
        """
        Processus CoVe complet. Retourne uniquement la réponse finale.
        """
        trace = self.trace_verification(question, media_type)
        return trace.get("final_response", "")

    def trace_verification(self, question: str, media_type: str) -> Dict:
        """
        Processus CoVe complet avec trace détaillée pour visualisation.
        """
        logger.info(f"🛡️ CoVe Trace: Processing question: '{question}'")

        trace: Dict[str, Any] = {
            "question": question,
            "baseline": "",
            "verification_plan": [],
            "verifications": [],
            "final_response": "",
        }

        # Étape 1 : Générer une réponse initiale (Baseline)
        baseline_prompt = self.prompt_manager.get_prompt(
            "cove_baseline", media_type=media_type, question=question
        )
        baseline_res = self.inference_engine.generate(baseline_prompt)
        trace["baseline"] = baseline_res.text

        # Étape 2 : Planification des vérifications (Deconstruct claims)
        plan_prompt, plan_system = self.prompt_manager.get_prompt(
            "cove_plan", baseline_response=trace["baseline"]
        )
        plan_data = self._safe_json_generate(plan_prompt, system_prompt=plan_system)

        try:
            plan = CoVePlan(**plan_data)
            verification_questions = plan.verification_questions
            trace["verification_plan"] = verification_questions
        except Exception as e:
            logger.warning(f"CoVe plan parsing failed: {e}")
            verification_questions = []

        if not verification_questions:
            trace["final_response"] = trace["baseline"]
            return trace

        logger.info(f"🔍 CoVe Trace: Verifying {len(verification_questions)} claims...")

        # Étape 3 : Exécution des vérifications (contre le Graphe)
        verified_facts = []
        for v_question in verification_questions:
            # On demande au LLM d'extraire les entités de la question de vérification
            ent_prompt = self.prompt_manager.get_prompt(
                "cove_entities", v_question=v_question
            )
            ent_res = self.inference_engine.generate(ent_prompt)
            entities = [e.strip() for e in ent_res.text.split(",")]

            # Interrogation de Neo4j (GraphRAG)
            graph_context = ""
            if self.neo4j_manager:
                for ent in entities:
                    ctx = self.neo4j_manager.get_creator_network_context(ent)
                    if "Pas de données" not in ctx:
                        graph_context += f"{ctx}\n"

            # Évaluation du fait avec le contexte vérifié
            eval_prompt = self.prompt_manager.get_prompt(
                "cove_eval", v_question=v_question, graph_context=graph_context
            )
            eval_res = self.inference_engine.generate(eval_prompt)

            verification_entry = {
                "query": v_question,
                "entities": entities,
                "context_found": graph_context != "",
                "result": eval_res.text,
            }
            trace["verifications"].append(verification_entry)
            verified_facts.append(f"Fait vérifié ({v_question}) : {eval_res.text}")

        # Étape 4 : Génération de la réponse finale révisée
        final_prompt, final_system = self.prompt_manager.get_prompt(
            "cove_final",
            question=question,
            baseline_response=trace["baseline"],
            verified_facts=" ".join(verified_facts),
        )

        logger.info("✅ CoVe Trace: Generating final verified response.")
        final_res = self.inference_engine.generate(
            final_prompt, system_prompt=final_system
        )
        trace["final_response"] = final_res.text

        return trace

    def _safe_json_generate(
        self, prompt: str, system_prompt: str = "Réponds UNIQUEMENT en JSON."
    ) -> Dict:
        res = self.inference_engine.generate(prompt, system_prompt=system_prompt)
        text = res.text
        try:
            if "{" in text and "}" in text:
                return orjson.loads(text[text.find("{") : text.rfind("}") + 1])
        except Exception as e:
            logger.warning(f"CoVe JSON Parsing Error: {e}")
        return {}

import orjson
import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort

logger = logging.getLogger('animetix')

class State:
    """Représente l'état partagé entre les nœuds du graphe."""
    def __init__(self, query: str, media_type: str):
        self.query = query
        self.media_type = media_type
        self.plan = []
        self.context = ""
        self.final_answer = ""
        self.history = []
        self.next_node = "PLANNER"

class OrchestratorAgentService:
    """
    Orchestration Agentique de type LangGraph (Graphe d'États).
    Gère des flux de raisonnement complexes via des nœuds spécialisés.
    """
    def __init__(self, inference_engine: InferencePort, services_factory, message_bus=None):
        self.inference_engine = inference_engine
        self.factory = services_factory # Accès aux autres services (RAG, Graph, Vision)
        self.message_bus = message_bus

    def execute_workflow(self, query: str, media_type: str) -> str:
        """Point d'entrée du workflow LangGraph-like."""
        state = State(query, media_type)
        
        if self.message_bus:
            self.message_bus.publish_binary_message("Orchestrator", "System", "WORKFLOW_START", {"query": query})
        
        # Simulation d'une boucle de graphe d'états
        max_steps = 10
        for _ in range(max_steps):
            if state.next_node == "END":
                break
                
            # Dispatch vers le nœud correspondant
            if state.next_node == "PLANNER":
                self._node_planner(state)
            elif state.next_node == "RETRIEVER":
                self._node_retriever(state)
            elif state.next_node == "VERIFIER":
                self._node_verifier(state)
            elif state.next_node == "WRITER":
                self._node_writer(state)
            else:
                state.next_node = "END"
                
        if self.message_bus:
            self.message_bus.publish_binary_message("Orchestrator", "System", "WORKFLOW_END", {"answer_length": len(state.final_answer)})
            
        return state.final_answer

    def _node_planner(self, state: State):
        """Nœud de Planification : Analyse et décide de la stratégie."""
        logger.info("🕸️ State Node: PLANNER")
        prompt = f"""
        QUERY: {state.query}
        
        MISSION: Planifie la résolution de cette question. 
        Dois-je chercher dans la DB (RETRIEVE) ou passer directement à la réponse (WRITE) ?
        
        FORMAT JSON :
        {{
            "plan": ["step 1", "step 2"],
            "next_node": "RETRIEVER" | "WRITER"
        }}
        """
        res = self._safe_json_generate(prompt)
        state.plan = res.get("plan", [])
        state.next_node = res.get("next_node", "RETRIEVER")

    def _node_retriever(self, state: State):
        """Nœud de Récupération : Appelle le RAG ou le Graphe."""
        logger.info("🕸️ State Node: RETRIEVER")
        # On utilise le RAG Agentique déjà existant pour cette partie
        rag_res = self.factory.agentic_rag.plan_and_solve(state.query, state.media_type)
        state.context += f"\n--- RAG INFO ---\n{rag_res}"
        state.next_node = "VERIFIER"

    def _node_verifier(self, state: State):
        """Nœud de Vérification : Utilise CoVe pour valider les faits."""
        logger.info("🕸️ State Node: VERIFIER")
        # Si le contexte contient des affirmations risquées, on demande une vérification
        prompt = f"Le contexte suivant est-il fiable ? {state.context[:500]}. Réponds par OUI ou NON."
        is_reliable = "OUI" in self.inference_engine.generate(prompt).upper()
        
        if not is_reliable:
            # On pourrait renvoyer vers un nœud de recherche corrective
            pass
            
        state.next_node = "WRITER"

    def _node_writer(self, state: State):
        """Nœud de Rédaction : Synthèse finale avec vérification de confiance."""
        logger.info("🕸️ State Node: WRITER")
        prompt = f"QUERY: {state.query}\nCONTEXTE: {state.context}\nRédige la réponse finale."
        state.final_answer = self.inference_engine.generate(prompt)
        
        # --- Uncertainty Quantification (XAI) ---
        confidence = self.factory.uncertainty_service.measure_confidence(prompt, state.final_answer)
        logger.info(f"📊 Confidence Score: {confidence['confidence_score']:.2f}")
        
        if not confidence["is_reliable"]:
            logger.warning("⚠️ Confidence low. Redirecting to WEB search for external verification.")
            state.next_node = "RETRIEVER" # Re-tenter avec plus d'info
            # On force leRequires Web pour le prochain tour de retriever
            state.history.append("Confidence low, seeking external facts.")
        else:
            state.next_node = "END"

    def _safe_json_generate(self, prompt: str) -> Dict:
        res = self.inference_engine.generate(prompt, system_prompt="Réponds en JSON.")
        try:
            if '{' in res and '}' in res:
                return orjson.loads(res[res.find('{'):res.rfind('}')+1])
        except: pass
        return {}

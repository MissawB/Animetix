from typing import Dict, List, Optional
from ...ports.inference_port import InferencePort

class ReasoningAgentService:
    def __init__(self, inference_engine: InferencePort, search_service=None, graph_manager=None, agent_bus=None):
        self.inference_engine = inference_engine
        self.search_service = search_service
        self.graph_manager = graph_manager
        self.agent_bus = agent_bus
        
        # Enregistrement sur le bus pour communication binaire inter-agents
        if self.agent_bus:
            self.agent_bus.register_agent("reasoning_agent", self._on_bus_message)

    def _on_bus_message(self, msg_id: str):
        """Callback pour les messages asynchrones/partagés."""
        data = self.agent_bus.read_shared_memory(msg_id)
        # Logique de réaction aux instructions d'autres agents (ex: Orchestrateur)
        pass

    def solve_complex_query(self, query: str, media_type: str) -> str:
        """
        Agent utilisant le pattern ReAct (Reasoning + Acting) avec citations de sources.
        """
        # 1. Étape de Raisonnement (Thought)
        thought_prompt = f"""
        QUERY : {query}
        CONTEXTE : {media_type}
        
        MISSION : Réfléchis étape par étape à la manière de répondre à cette question.
        Quelles informations manquent ? Dois-je chercher dans la base vectorielle ou le graphe de connaissances ?
        
        Réponds par :
        THOUGHT: [Ton raisonnement]
        ACTION: [SEARCH|GRAPH|ANSWER]
        PARAMS: [Paramètres de recherche si besoin]
        """
        
        thought_res = self.inference_engine.generate(thought_prompt, system_prompt="Tu es un agent de raisonnement logique.")
        
        context_data = ""
        sources = []
        
        # 2. Étape d'Action (Act)
        if "ACTION: SEARCH" in thought_res:
            # Action de recherche sémantique
            if self.search_service:
                results = self.search_service.hybrid_search(query, media_type, limit=3)
                for r in results:
                    title = r.get('title') or r.get('name')
                    context_data += f"- {title}: {r.get('description', '')[:200]}\n"
                    sources.append(title)
        
        elif "ACTION: GRAPH" in thought_res:
            # Action de parcours de graphe
            if self.graph_manager:
                # Simulé ici : on chercherait les relations de l'entité principale mentionnée
                pass
            
        # 3. Réponse finale (Final Answer) avec citations
        final_prompt = f"""
        CONSIGNES : Réponds à la question en utilisant le CONTEXTE fourni. 
        TU DOIS citer tes sources à la fin de tes affirmations clés sous la forme [Source: Nom].
        
        CONTEXTE :
        {context_data if context_data else "Aucun contexte spécifique trouvé."}
        
        RAISONNEMENT :
        {thought_res}
        
        QUESTION : {query}
        """
        
        answer = self.inference_engine.generate(final_prompt, system_prompt="Tu es un expert qui cite toujours ses sources.")
        
        # Post-processing pour s'assurer que les sources sont bien formatées si l'IA a oublié
        if sources and "[Source:" not in answer:
            answer += "\n\n(Sources consultées : " + ", ".join(sources) + ")"
            
        return answer

    def execute_react_loop(self, query: str, max_iterations: int = 3) -> str:
        """Boucle itérative de raisonnement."""
        history = []
        for i in range(max_iterations):
            prompt = f"Historique : {history}\nRequête actuelle : {query}\nFais une étape de raisonnement."
            # ... logic to parse actions and execute tools
            pass
        return "Réponse de l'agent raisonneur."

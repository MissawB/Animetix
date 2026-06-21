import logging
import re
from typing import Optional

from ...ports.graph_persistence_port import GraphPersistencePort
from ...ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.reasoning")


class ReasoningAgentService:
    def __init__(
        self,
        inference_engine: InferencePort,
        prompt_manager: PromptManager,
        search_service=None,
        graph_manager: Optional[GraphPersistencePort] = None,
        agent_bus=None,
    ):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.search_service = search_service
        self.graph_manager = graph_manager
        self.agent_bus = agent_bus

        # Enregistrement sur le bus pour communication binaire inter-agents
        if self.agent_bus:
            self.agent_bus.register_agent("reasoning_agent", self._on_bus_message)

    async def _on_bus_message(self, msg_id: str):
        """Callback pour les messages asynchrones/partagés."""
        if not self.agent_bus:
            return
        data = await self.agent_bus.read_shared_memory(msg_id)
        if data and isinstance(data, dict) and data.get("target") == "reasoning_agent":
            logger.info(
                f"Agent Raisonneur a reçu une instruction via le bus : {data.get('command')}"
            )
            # Ici on pourrait déclencher un solve_complex_query ou une autre action

    def solve_complex_query(self, query: str, media_type: str) -> str:
        """
        Agent utilisant le pattern ReAct (Reasoning + Acting) avec citations de sources.
        """
        return self.execute_react_loop(query, media_type)

    def execute_react_loop(
        self, query: str, media_type: str = "Anime", max_iterations: int = 3
    ) -> str:
        """Boucle itérative de raisonnement (Reasoning + Acting)."""
        history: list[str] = []
        context_data = ""
        sources = []

        logger.info(f"Démarrage de la boucle ReAct pour : {query}")

        for i in range(max_iterations):
            # 1. Étape de Raisonnement (Thought) via PromptManager
            prompt, sys = self.prompt_manager.get_prompt(
                "reasoning_thought",
                query=query,
                media_type=media_type,
                history="\n".join(history) if history else "Néant",
            )

            res = self.inference_engine.generate(prompt, system_prompt=sys)
            history.append(f"Iteration {i + 1}:\n{res}")

            # 2. Étape d'Action (Act)
            if "ACTION: ANSWER" in res:
                logger.info("L'agent a décidé de répondre.")
                break

            if "ACTION: SEARCH" in res:
                # Extraire PARAMS pour la recherche
                match = re.search(r"PARAMS:\s*(.*)", res)
                search_query = match.group(1).strip() if match else query
                logger.info(f"Action: SEARCH sémantique pour '{search_query}'")

                if self.search_service:
                    results = self.search_service.hybrid_search(
                        search_query, media_type, limit=3
                    )
                    for r in results:
                        title = r.get("title") or r.get("name")
                        if title not in sources:
                            context_data += (
                                f"- {title}: {r.get('description', '')[:300]}\n"
                            )
                            sources.append(title)
                else:
                    history.append("OBSERVATION: Service de recherche non disponible.")

            elif "ACTION: GRAPH" in res:
                match = re.search(r"PARAMS:\s*(.*)", res)
                entity = match.group(1).strip() if match else ""
                logger.info(f"Action: GRAPH traversal pour '{entity}'")

                if self.graph_manager and entity:
                    graph_res = self.graph_manager.get_enriched_context([entity])
                    context_data += f"\nINFOS GRAPHE ({entity}):\n{graph_res}\n"
                    history.append(
                        f"OBSERVATION: Données de graphe récupérées pour {entity}."
                    )
                else:
                    history.append(
                        "OBSERVATION: Graphe non disponible ou entité manquante."
                    )

            else:
                # Si le format n'est pas respecté ou action inconnue
                history.append(
                    "OBSERVATION: Format non reconnu. Veuillez choisir SEARCH, GRAPH ou ANSWER."
                )

        # 3. Réponse finale (Final Answer)
        final_prompt, sys = self.prompt_manager.get_prompt(
            "reasoning_final",
            query=query,
            context=(
                context_data if context_data else "Aucun contexte additionnel trouvé."
            ),
            thought="\n".join(history),
        )

        answer = self.inference_engine.generate(final_prompt, system_prompt=sys)

        # Post-processing pour garantir les citations si l'IA a oublié
        if sources and "[Source:" not in answer:
            answer += "\n\n(Sources consultées : " + ", ".join(sources) + ")"

        return answer

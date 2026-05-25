import logging
import time
from typing import List, Dict, Optional, Generator, Any
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from core.ports.graph_persistence_port import GraphPersistencePort
from .advanced_rag_service import AdvancedRAGService
from .prompt_manager import PromptManager
from .llm_service import LLMService
from .xai_service import UncertaintyService
from .rag_workflow_manager import RAGWorkflowManager
from ..exceptions import (
    InfrastructureError, ParsingError, InferenceError, AnimetixError,
)
from ..entities.ai_schemas import (
    StreamStep, RAGState, RAGContext
)
from .rag.agents import SemanticRouter

logger = logging.getLogger("animetix.rag")

class AgenticRAGService:
    """
    Orchestrateur RAG Agentique 2.0.
    Délègue la machine à états au RAGWorkflowManager.
    """
    def __init__(
        self, 
        inference_engine: InferencePort, 
        rag_service: AdvancedRAGService,
        web_search: WebSearchPort,
        prompt_manager: PromptManager,
        llm_service: LLMService,
        workflow_manager: RAGWorkflowManager,
        neo4j_manager: Optional[GraphPersistencePort] = None,
        memory_service=None,
        semantic_cache=None,
        obs_service=None,
        uncertainty_service: Optional[UncertaintyService] = None,
        semantic_router: Optional[SemanticRouter] = None,
    ):
        self.inference_engine = inference_engine
        self.rag_service = rag_service
        self.web_search = web_search
        self.prompt_manager = prompt_manager
        self.llm_service = llm_service
        self.workflow_manager = workflow_manager
        self.neo4j_manager = neo4j_manager
        self.memory_service = memory_service
        self.semantic_cache = semantic_cache
        self.obs_service = obs_service
        
        self.uncertainty_service = uncertainty_service or UncertaintyService(self.inference_engine)
        self.semantic_router = semantic_router or SemanticRouter(self.llm_service, self.prompt_manager)


    def plan_and_solve(self, query: str, media_type: str, user_id: Optional[str] = None) -> str:
        """Wrapper non-streaming. Retourne uniquement la réponse finale."""
        last_answer = ""
        for event in self.plan_and_solve_stream(query, media_type, user_id):
            if event['type'] == 'token':
                last_answer += event['content']
            elif event['type'] == 'thought' and "[Synthesizer]" in event['content']:
                last_answer = ""
        return last_answer

    def plan_and_solve_stream(self, query: str, media_type: str, user_id: Optional[str] = None) -> Generator[Dict, None, None]:
        """Boucle principale orchestrée via RAGWorkflowManager."""
        
        # 1. ROUTAGE SÉMANTIQUE INTELLIGENT (SOTA 2026)
        routing_decision = self.semantic_router.classify(query)
        if routing_decision == "SIMPLE":
            yield StreamStep(type="thought", content="[Semantic Router] Requête simple détectée. Court-circuitage vers la recherche et synthèse directe en < 2 secondes...").model_dump()
            full_answer = ""
            for event in self.workflow_manager.handle_fast_rag(query, media_type):
                yield event
                if event['type'] == 'token':
                    full_answer += event['content']
            
            if full_answer:
                self._store_results(query, full_answer, user_id)
            return

        # 2. ANALYSE COMPLEXITÉ ET INITIALISATION CONTEXTE
        thinking_budget, complexity = self._assess_complexity(query)
        thinking_mode = complexity >= 2
        
        if thinking_budget > 0 or thinking_mode:
            yield StreamStep(type="thought", content=f"[TTC] Requête complexe (Score {complexity}). Budget: {thinking_budget} tokens. Mode Thinking: {thinking_mode}").model_dump()

        if cached := self._check_cache(query):
            yield from self._stream_cached_response(cached)
            return

        # Chargement de la mémoire utilisateur depuis le Graphe (Task 5.2)
        user_context = ""
        if user_id and self.neo4j_manager:
            user_context = self.neo4j_manager.get_user_preferences_context(user_id)
            if user_context:
                yield StreamStep(type="thought", content=f"[Graph User Memory] Profil utilisateur '{user_id}' chargé depuis le graphe sémantique.").model_dump()

        ctx = RAGContext(
            query=query,
            media_type=media_type,
            user_id=user_id,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
            memories=self._get_memories(user_id, query),
            current_state=RAGState.PLAN,
            graph_expert=self.workflow_manager.graph_expert,
            truth_path=user_context
        )

        # 3. DÉLÉGATION AU WORKFLOW MANAGER
        yield from self.workflow_manager.run_workflow(ctx)

        # 4. FINALISATION
        if ctx.full_answer:
            self._store_results(ctx.query, ctx.full_answer, ctx.user_id)
            # Enregistrement asynchrone de l'interaction utilisateur dans Neo4j (Task 5.2)
            if user_id and self.neo4j_manager:
                import threading
                threading.Thread(
                    target=self.neo4j_manager.sync_user_interaction,
                    args=(user_id, query, "SEARCH"),
                    daemon=True
                ).start()


    # --- MÉTHODES UTILITAIRES ---
    def _assess_complexity(self, query: str) -> tuple[int, int]:
        prompt, sys = self.prompt_manager.get_prompt("complexity_analyzer", query=query)
        try:
            res = self.llm_service.generate(prompt, sys, use_slm=False)
            data = self._extract_json(res)
            return int(data.get("thinking_budget", 0)), int(data.get("complexity_score", 0))
        except (ParsingError, ValueError) as e:
            logger.error(f"Error parsing complexity metrics: {e}")
            return 0, 0
        except InferenceError as e:
            logger.error(f"Inference failed during complexity analysis: {e}")
            return 0, 0
        except (InfrastructureError, RuntimeError) as e:
            logger.error(f"Unexpected error in complexity analysis: {e}")
            return 0, 0

    def _check_cache(self, query: str) -> Optional[str]:
        if self.semantic_cache:
            return self.semantic_cache.get_cached_response(query)
        return None

    def _stream_cached_response(self, text: str) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[Cache] ⚡ Réponse trouvée en cache !").model_dump()
        for token in text.split(' '):
            yield StreamStep(type="token", content=token + " ").model_dump()
            time.sleep(0.01)

    def _get_memories(self, user_id: str, query: str) -> str:
        if self.memory_service and user_id:
            return self.memory_service.retrieve_relevant_memories(user_id, query)
        return ""

    def _store_results(self, query: str, answer: str, user_id: str):
        if self.semantic_cache:
            try: 
                self.semantic_cache.set_cached_response(query, answer)
            except InfrastructureError as e:
                logger.error(f"Semantic Cache storage failed: {e}")
            except (InferenceError, InfrastructureError, RuntimeError) as e:
                logger.error(f"Unexpected error in Cache storage: {e}")

        if self.memory_service and user_id:
            try: 
                self.memory_service.store_memory(user_id, [{"role": "user", "content": query}, {"role": "assistant", "content": answer}])
            except InfrastructureError as e:
                logger.error(f"Long-term memory storage failed for user {user_id}: {e}")
            except (InferenceError, InfrastructureError, RuntimeError) as e:
                logger.error(f"Unexpected error in memory storage: {e}")

    def _extract_json(self, text: str) -> Dict:
        import orjson
        try:
            if '{' in text and '}' in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
                return orjson.loads(json_str)
        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI output: {e}. Output was: {text[:200]}...")
            raise ParsingError(f"Invalid JSON from AI: {e}")
        except (InferenceError, InfrastructureError, RuntimeError) as e:
            logger.error(f"Unexpected error during JSON extraction: {e}")
            raise ParsingError(f"JSON extraction failed: {e}")
        return {}

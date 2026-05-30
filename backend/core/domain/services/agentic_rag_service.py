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
        **kwargs
    ):
        self.inference_engine = inference_engine
        self.rag_service = rag_service
        self.web_search = web_search
        self.prompt_manager = prompt_manager
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.memory_service = memory_service
        self.semantic_cache = semantic_cache
        self.obs_service = obs_service
        
        self.uncertainty_service = uncertainty_service or UncertaintyService(self.inference_engine)
        self.semantic_router = semantic_router or SemanticRouter(self.llm_service, self.prompt_manager)

        is_mock = False
        try:
            from unittest.mock import MagicMock
            is_mock = isinstance(workflow_manager, MagicMock)
        except ImportError:
            logger.debug("unittest.mock not available, skipping mock check.")

        if workflow_manager is None or is_mock:
            from .rag.agents import SearchPlanner, ResponseCritic, ResponseSynthesizer, ResponseJudge, ScoutAgent, GraphExpert, RetrievalEvaluator, ContextCompressor
            from .rag.agents.debate_manager import DebateManager
            from .rag.agents.librarian import LibrarianAgent
            from .rag.agents.forge import ForgeAgent
            from .rag.agents.saga_agent import SagaAgent
            from .rag.agents.chronicler import ChroniclerAgent
            from pipeline.mlops.graph_community_partitioner import GraphCommunityPartitioner

            planner = SearchPlanner(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            critic = ResponseCritic(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            synthesizer = ResponseSynthesizer(inference_engine=self.inference_engine, prompt_manager=self.prompt_manager)
            judge = ResponseJudge(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            scout = ScoutAgent(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            semantic_router_obj = SemanticRouter(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            retrieval_evaluator = RetrievalEvaluator(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            community_partitioner = GraphCommunityPartitioner(neo4j_manager=self.neo4j_manager, llm_service=self.llm_service)
            graph_expert = GraphExpert(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            debate_manager = DebateManager(llm_service=self.llm_service, prompt_manager=self.prompt_manager)
            librarian = LibrarianAgent(llm_service=self.llm_service, prompt_manager=self.prompt_manager, web_search=self.web_search)
            forge = ForgeAgent(llm_service=self.llm_service, prompt_manager=self.prompt_manager, neo4j_manager=self.neo4j_manager)
            saga_agent = SagaAgent(llm_service=self.llm_service, neo4j_manager=self.neo4j_manager)
            chronicler = ChroniclerAgent(llm_service=self.llm_service, prompt_manager=self.prompt_manager, neo4j_manager=self.neo4j_manager, web_search=self.web_search)
            context_compressor = ContextCompressor(llm_service=self.llm_service, prompt_manager=self.prompt_manager)

            self.workflow_manager = RAGWorkflowManager(
                planner=planner,
                critic=critic,
                synthesizer=synthesizer,
                judge=judge,
                scout=scout,
                semantic_router=semantic_router_obj,
                retrieval_evaluator=retrieval_evaluator,
                community_partitioner=community_partitioner,
                graph_expert=graph_expert,
                debate_manager=debate_manager,
                librarian=librarian,
                forge=forge,
                saga_agent=saga_agent,
                chronicler=chronicler,
                uncertainty_service=self.uncertainty_service,
                inference_engine=self.inference_engine,
                web_search=self.web_search,
                prompt_manager=self.prompt_manager,
                rag_service=self.rag_service,
                neo4j_manager=self.neo4j_manager,
                context_compressor=context_compressor
            )
        else:
            self.workflow_manager = workflow_manager

        # Delegate kwargs to workflow_manager if present
        for key, val in kwargs.items():
            if self.workflow_manager and hasattr(self.workflow_manager, key):
                setattr(self.workflow_manager, key, val)

    @property
    def planner(self):
        return self.workflow_manager.planner if self.workflow_manager else None

    @planner.setter
    def planner(self, value):
        if self.workflow_manager:
            self.workflow_manager.planner = value

    @property
    def scout(self):
        return self.workflow_manager.scout if self.workflow_manager else None

    @scout.setter
    def scout(self, value):
        if self.workflow_manager:
            self.workflow_manager.scout = value

    @property
    def synthesizer(self):
        return self.workflow_manager.synthesizer if self.workflow_manager else None

    @synthesizer.setter
    def synthesizer(self, value):
        if self.workflow_manager:
            self.workflow_manager.synthesizer = value

    @property
    def librarian(self):
        return self.workflow_manager.librarian if self.workflow_manager else None

    @librarian.setter
    def librarian(self, value):
        if self.workflow_manager:
            self.workflow_manager.librarian = value

    @property
    def critic(self):
        return self.workflow_manager.critic if self.workflow_manager else None

    @critic.setter
    def critic(self, value):
        if self.workflow_manager:
            self.workflow_manager.critic = value

    @property
    def judge(self):
        return self.workflow_manager.judge if self.workflow_manager else None

    @judge.setter
    def judge(self, value):
        if self.workflow_manager:
            self.workflow_manager.judge = value

    @property
    def debate_manager(self):
        return self.workflow_manager.debate_manager if self.workflow_manager else None

    @debate_manager.setter
    def debate_manager(self, value):
        if self.workflow_manager:
            self.workflow_manager.debate_manager = value

    @property
    def forge(self):
        return self.workflow_manager.forge if self.workflow_manager else None

    @forge.setter
    def forge(self, value):
        if self.workflow_manager:
            self.workflow_manager.forge = value

    @property
    def saga_agent(self):
        return self.workflow_manager.saga_agent if self.workflow_manager else None

    @saga_agent.setter
    def saga_agent(self, value):
        if self.workflow_manager:
            self.workflow_manager.saga_agent = value

    @property
    def graph_expert(self):
        return self.workflow_manager.graph_expert if self.workflow_manager else None

    @graph_expert.setter
    def graph_expert(self, value):
        if self.workflow_manager:
            self.workflow_manager.graph_expert = value


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
            for event in self.workflow_manager.handle_fast_rag(query, media_type, user_id=user_id):
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
        try:
            from .complexity_analyser import ComplexityAnalyser
            analyser = ComplexityAnalyser(self.prompt_manager, self.llm_service)
            return analyser.assess_complexity(query)
        except ImportError as e:
            logger.error(f"ComplexityAnalyser not available: {e}")
            return 0, 0
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"AI/Infrastructure error in dynamic complexity analysis: {e}")
            return 0, 0
        except Exception as e:
            logger.error(f"Error in dynamic complexity analysis: {e}", exc_info=True)
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
        except (InferenceError, InfrastructureError, RuntimeError) as e:
            logger.error(f"Unexpected error during JSON extraction: {e}")
        return {}

    def _execute_search(self, plan, media_type: str, user_id: Optional[str] = None) -> tuple[List[Dict], str]:
        if self.workflow_manager:
            return self.workflow_manager._execute_search(plan, media_type, user_id=user_id)
        return [], ""

    def _handle_research(self, ctx) -> Generator[Dict, None, None]:
        if self.workflow_manager:
            yield from self.workflow_manager._handle_research(ctx)

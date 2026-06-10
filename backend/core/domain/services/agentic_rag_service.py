import logging
import time
from typing import List, Dict, Optional, Generator, Any
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from core.ports.graph_persistence_port import GraphPersistencePort
from .advanced_rag_service import AdvancedRAGService
from .prompt_manager import PromptManager
from .llm_service import LLMService
from .xai_service import XaiDiagnosticService, XaiCollector
from .rag_orchestrator import RAGOrchestrator # Updated import
from ..exceptions import (
    InfrastructureError, ParsingError, InferenceError, AnimetixError,
)
from ..entities.ai_schemas import (
    StreamStep, RAGState, RAGContext, InferenceResponse
)
from .rag.agents import SemanticRouter

logger = logging.getLogger("animetix.rag")

class AgenticRAGService:
    """
    Orchestrateur RAG Agentique 2.0.
    Délègue la machine à états au RAGOrchestrator.
    """
    def __init__(
        self, 
        inference_engine: InferencePort, 
        rag_service: AdvancedRAGService,
        web_search: WebSearchPort,
        prompt_manager: PromptManager,
        llm_service: LLMService,
        workflow_orchestrator: RAGOrchestrator, # Updated parameter
        neo4j_manager: Optional[GraphPersistencePort] = None,
        memory_service=None,
        semantic_cache=None,
        obs_service=None,
        xai_service: Optional[XaiDiagnosticService] = None,
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
        self.xai_service = xai_service or XaiDiagnosticService(self.inference_engine)
        self.semantic_router = semantic_router or SemanticRouter(self.llm_service, self.prompt_manager)
        self.orchestrator = workflow_orchestrator # Updated assignment

        # Delegate kwargs to orchestrator if present
        for key, val in kwargs.items():
            if self.orchestrator and hasattr(self.orchestrator, key):
                setattr(self.orchestrator, key, val)

    def _record_agent_trace(self, state_name: str, details: dict):
        from django.conf import settings
        if not getattr(settings, 'VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE', False):
            return

        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span and span.is_recording():
                agent_id = getattr(settings, 'VERTEX_AI_AGENT_ID', 'animetix-core-rag-agent')
                span.set_attribute("gcp.agent.id", agent_id)
                span.set_attribute("gcp.agent.state", state_name)
                for key, val in details.items():
                    span.set_attribute(f"gcp.agent.details.{key}", str(val))
        except Exception as e:
            logger.debug(f"Telemetry logging failed: {e}")

    @property
    def planner(self):
        return self.orchestrator.processors[RAGState.PLAN].planner if self.orchestrator else None

    @planner.setter
    def planner(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.PLAN].planner = value

    @property
    def scout(self):
        return self.orchestrator.processors[RAGState.RESEARCH].scout if self.orchestrator else None

    @scout.setter
    def scout(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.RESEARCH].scout = value

    @property
    def synthesizer(self):
        return self.orchestrator.processors[RAGState.SYNTHESIZE].synthesizer if self.orchestrator else None

    @synthesizer.setter
    def synthesizer(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.SYNTHESIZE].synthesizer = value

    @property
    def librarian(self):
        return self.orchestrator.processors[RAGState.ACQUIRE_KNOWLEDGE].librarian if self.orchestrator else None

    @librarian.setter
    def librarian(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.ACQUIRE_KNOWLEDGE].librarian = value

    @property
    def critic(self):
        return self.orchestrator.processors[RAGState.JUDGE].critic if self.orchestrator else None

    @critic.setter
    def critic(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.JUDGE].critic = value

    @property
    def judge(self):
        return self.orchestrator.processors[RAGState.JUDGE].judge if self.orchestrator else None

    @judge.setter
    def judge(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.JUDGE].judge = value

    @property
    def debate_manager(self):
        return self.orchestrator.processors[RAGState.JUDGE].debate_manager if self.orchestrator else None

    @debate_manager.setter
    def debate_manager(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.JUDGE].debate_manager = value

    @property
    def forge(self):
        return self.orchestrator.processors[RAGState.SPECULATE].forge if self.orchestrator else None

    @forge.setter
    def forge(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.SPECULATE].forge = value

    @property
    def saga_agent(self):
        return self.orchestrator.processors[RAGState.SAGA_LOOKUP].saga_agent if self.orchestrator else None

    @saga_agent.setter
    def saga_agent(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.SAGA_LOOKUP].saga_agent = value

    @property
    def graph_expert(self):
        return self.orchestrator.processors[RAGState.GRAPH_EXPLORE].graph_expert if self.orchestrator else None

    @graph_expert.setter
    def graph_expert(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.GRAPH_EXPLORE].graph_expert = value

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
        """Boucle principale orchestrée via RAGOrchestrator."""
        
        # 1. ROUTAGE SÉMANTIQUE INTELLIGENT (SOTA 2026)
        routing_decision = self.semantic_router.classify(query)
        if routing_decision == "SIMPLE":
            yield StreamStep(type="thought", content="[Semantic Router] Requête simple détectée. Court-circuitage vers la recherche et synthèse directe en < 2 secondes...")
            full_answer = ""
            ctx = RAGContext(
                query=query, media_type=media_type, user_id=user_id,
                thinking_budget=0, thinking_mode=False,
                memories="", current_state=RAGState.FALLBACK_RAG # Direct to Fallback
            )
            yield from self.orchestrator.run_workflow(ctx) # Run simple flow
            if ctx.full_answer:
                self._store_results(query, ctx.full_answer, user_id)
            return

        # 2. ANALYSE COMPLEXITÉ ET INITIALISATION CONTEXTE
        self._record_agent_trace("PLAN", {"query": query, "media_type": media_type})
        thinking_budget, complexity = self._assess_complexity(query)
        thinking_mode = complexity >= 2
        
        if thinking_budget > 0 or thinking_mode:
            yield StreamStep(type="thought", content=f"[TTC] Requête complexe (Score {complexity}). Budget: {thinking_budget} tokens. Mode Thinking: {thinking_mode}")

        if cached := self._check_cache(query):
            yield from self._stream_cached_response(cached)
            return

        # Chargement de la mémoire utilisateur depuis le Graphe (Task 5.2)
        user_context = ""
        if user_id and self.neo4j_manager:
            user_context = self.neo4j_manager.get_user_preferences_context(user_id)
            if user_context:
                yield StreamStep(type="thought", content=f"[Graph User Memory] Profil utilisateur '{user_id}' chargé depuis le graphe sémantique.")

        ctx = RAGContext(
            query=query,
            media_type=media_type,
            user_id=user_id,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
            memories=self._get_memories(user_id, query),
            current_state=RAGState.PLAN,
            graph_expert=self.orchestrator.processors[RAGState.GRAPH_EXPLORE].graph_expert if self.orchestrator and RAGState.GRAPH_EXPLORE in self.orchestrator.processors else None,
            truth_path=user_context
        )

        # 3. DÉLÉGATION À L'ORCHESTRATEUR
        xai_collector = XaiCollector()
        yield from self.orchestrator.run_workflow(ctx, xai_collector=xai_collector)

        # 4. FINALISATION
        if ctx.full_answer:
            self._store_results(ctx.query, ctx.full_answer, ctx.user_id)

            if self.xai_service:
                try:
                    response_obj = InferenceResponse(text=ctx.full_answer)
                    report = self.xai_service.generate_advanced_report(
                        query=ctx.query,
                        response=response_obj,
                        collector=xai_collector
                    )
                    yield StreamStep(type="xai_report", content=report) # Yield StreamStep directly
                except Exception as e:
                    logger.error(f"Error generating XAI report: {e}", exc_info=True)
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
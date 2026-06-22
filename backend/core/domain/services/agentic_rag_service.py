import logging
import time
from typing import Dict, Generator, Optional

from core.config import get_config
from core.ports.config_port import ConfigPort
from core.ports.graph_persistence_port import GraphPersistencePort
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort

from ..entities.ai_schemas import (
    InferenceResponse,
    RAGContext,  # noqa: E402
    RAGState,
    StreamStep,
)
from ..exceptions import InferenceError, InfrastructureError
from .advanced_rag_service import AdvancedRAGService
from .graph_health import is_graph_degraded
from .llm_service import LLMService
from .prompt_manager import PromptManager
from .rag.agents import SemanticRouter  # noqa: E402
from .rag_orchestrator import RAGOrchestrator  # Updated import
from .xai_service import XaiCollector, XaiDiagnosticService

logger = logging.getLogger("animetix.rag")

# Re-exported for callers/tests that reference it on this module.
_graph_is_degraded = is_graph_degraded


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
        workflow_orchestrator: RAGOrchestrator,  # Updated parameter
        neo4j_manager: Optional[GraphPersistencePort] = None,
        memory_service=None,
        semantic_cache=None,
        obs_service=None,
        xai_service: Optional[XaiDiagnosticService] = None,
        semantic_router: Optional[SemanticRouter] = None,
        config_port: Optional[ConfigPort] = None,
        guardrail_service=None,
        **kwargs,
    ):
        self.config = config_port or get_config()
        self.inference_engine = inference_engine
        self.rag_service = rag_service
        self.web_search = web_search
        self.prompt_manager = prompt_manager
        self.llm_service = llm_service
        self.neo4j_manager = neo4j_manager
        self.memory_service = memory_service
        self.semantic_cache = semantic_cache
        self.obs_service = obs_service
        self.xai_service = (
            xai_service
            or kwargs.get("uncertainty_service")
            or XaiDiagnosticService(self.inference_engine)
        )
        self.semantic_router = semantic_router or SemanticRouter(
            self.llm_service, self.prompt_manager
        )
        self.orchestrator = workflow_orchestrator  # Updated assignment

        # Injecté par le conteneur DI (cf. AgenticContainer.guardrail_service).
        # Rétro-compat : accepte aussi un passage via kwargs.
        self.guardrail_service = guardrail_service or kwargs.get("guardrail_service")

        # Delegate kwargs to properties/attributes on self if present, otherwise to orchestrator
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)
            elif self.orchestrator and hasattr(self.orchestrator, key):
                setattr(self.orchestrator, key, val)

    def _execute_search(self, query: str, requires_web: bool) -> tuple:
        """Stub method for testing compatibility and mocking."""
        return [], ""

    def _record_agent_trace(self, state_name: str, details: dict):
        if not self.config.get("VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE", False):
            return

        try:
            from opentelemetry import trace  # noqa: E402

            span = trace.get_current_span()
            if span and span.is_recording():
                agent_id = self.config.get(
                    "VERTEX_AI_AGENT_ID", "animetix-core-rag-agent"
                )
                span.set_attribute("gcp.agent.id", agent_id)
                span.set_attribute("gcp.agent.state", state_name)
                for key, val in details.items():
                    span.set_attribute(f"gcp.agent.details.{key}", str(val))
        except Exception as e:
            logger.debug(f"Telemetry logging failed: {e}")

    @property
    def planner(self):
        return (
            self.orchestrator.processors[RAGState.PLAN].planner
            if self.orchestrator
            else None
        )

    @planner.setter
    def planner(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.PLAN].planner = value

    @property
    def scout(self):
        return (
            self.orchestrator.processors[RAGState.RESEARCH].scout
            if self.orchestrator
            else None
        )

    @scout.setter
    def scout(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.RESEARCH].scout = value

    @property
    def synthesizer(self):
        return (
            self.orchestrator.processors[RAGState.SYNTHESIZE].synthesizer
            if self.orchestrator
            else None
        )

    @synthesizer.setter
    def synthesizer(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.SYNTHESIZE].synthesizer = value

    @property
    def librarian(self):
        return (
            self.orchestrator.processors[RAGState.ACQUIRE_KNOWLEDGE].librarian
            if self.orchestrator
            else None
        )

    @librarian.setter
    def librarian(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.ACQUIRE_KNOWLEDGE].librarian = value

    @property
    def critic(self):
        return (
            self.orchestrator.processors[RAGState.JUDGE].critic
            if self.orchestrator
            else None
        )

    @critic.setter
    def critic(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.JUDGE].critic = value

    @property
    def judge(self):
        return (
            self.orchestrator.processors[RAGState.JUDGE].judge
            if self.orchestrator
            else None
        )

    @judge.setter
    def judge(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.JUDGE].judge = value

    @property
    def debate_manager(self):
        return (
            self.orchestrator.processors[RAGState.JUDGE].debate_manager
            if self.orchestrator
            else None
        )

    @debate_manager.setter
    def debate_manager(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.JUDGE].debate_manager = value

    @property
    def forge(self):
        return (
            self.orchestrator.processors[RAGState.SPECULATE].forge
            if self.orchestrator
            else None
        )

    @forge.setter
    def forge(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.SPECULATE].forge = value

    @property
    def saga_agent(self):
        return (
            self.orchestrator.processors[RAGState.SAGA_LOOKUP].saga_agent
            if self.orchestrator
            else None
        )

    @saga_agent.setter
    def saga_agent(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.SAGA_LOOKUP].saga_agent = value

    @property
    def graph_expert(self):
        return (
            self.orchestrator.processors[RAGState.GRAPH_EXPLORE].graph_expert
            if self.orchestrator
            else None
        )

    @graph_expert.setter
    def graph_expert(self, value):
        if self.orchestrator:
            self.orchestrator.processors[RAGState.GRAPH_EXPLORE].graph_expert = value

    @property
    def uncertainty_service(self):
        return self.xai_service

    @uncertainty_service.setter
    def uncertainty_service(self, value):
        self.xai_service = value
        if self.orchestrator and RAGState.SYNTHESIZE in self.orchestrator.processors:
            self.orchestrator.processors[RAGState.SYNTHESIZE].xai_service = value

    def plan_and_solve(
        self,
        query: str,
        media_type: str,
        user_id: Optional[str] = None,
        language: str = "Français",
    ) -> str:
        """Wrapper non-streaming. Retourne uniquement la réponse finale."""
        last_answer = ""
        for event in self.plan_and_solve_stream(query, media_type, user_id, language):
            if event["type"] == "token":
                last_answer += event["content"]
            elif event["type"] == "thought" and "[Synthesizer]" in event["content"]:
                last_answer = ""
        return last_answer

    def plan_and_solve_stream(
        self,
        query: str,
        media_type: str,
        user_id: Optional[str] = None,
        language: str = "Français",
    ) -> Generator[Dict, None, None]:
        """Boucle principale orchestrée via RAGOrchestrator."""
        start_time = time.time()

        # 0. SÉCURITÉ ET GUARDRAILS (Anti-Jailbreak / Prompt Injection)
        if self.guardrail_service:
            guard_input = self.guardrail_service.validate_input(query)
            if not guard_input.get("is_safe", True):
                reason = guard_input.get(
                    "reason",
                    "Suspicion de tentative d'injection de prompt ou de contournement des règles.",
                )
                logger.warning(f"🛡️ [Guardrail] Query blocked: {reason}")
                yield StreamStep(
                    type="thought", content=f"[Guardrail] Requête bloquée : {reason}"
                ).model_dump()
                # Yield tokens for streaming compatibility
                for token in reason.split(" "):
                    yield StreamStep(type="token", content=token + " ").model_dump()
                return

        # 1. ROUTAGE SÉMANTIQUE INTELLIGENT (SOTA 2026)
        routing_decision = self.semantic_router.classify(query)
        if routing_decision == "SIMPLE":
            yield StreamStep(
                type="thought",
                content="[Semantic Router] Requête simple détectée. Court-circuitage vers la recherche et synthèse directe en < 2 secondes...",
            ).model_dump()
            ctx = RAGContext(
                query=query,
                media_type=media_type,
                user_id=user_id,
                thinking_budget=0,
                thinking_mode=False,
                memories="",
                current_state=RAGState.FALLBACK_RAG,  # Direct to Fallback
                language=language,
            )
            yield from self.orchestrator.run_workflow(ctx)  # Run simple flow
            if ctx.full_answer:
                self._store_results(query, ctx.full_answer, user_id)

            if self.obs_service:
                self.obs_service.log_rag_latency(
                    time.time() - start_time, query, user_id
                )
            return

        # 2. ANALYSE COMPLEXITÉ ET INITIALISATION CONTEXTE
        self._record_agent_trace("PLAN", {"query": query, "media_type": media_type})
        thinking_budget, complexity = self._assess_complexity(query)
        thinking_mode = complexity >= 2

        if thinking_budget > 0 or thinking_mode:
            yield StreamStep(
                type="thought",
                content=f"[TTC] Requête complexe (Score {complexity}). Budget: {thinking_budget} tokens. Mode Thinking: {thinking_mode}",
            ).model_dump()

        if cached := self._check_cache(query):
            yield from self._stream_cached_response(cached)
            if self.obs_service:
                self.obs_service.log_rag_latency(
                    time.time() - start_time, query, user_id
                )
            return

        # Chargement de la mémoire utilisateur depuis le Graphe (Task 5.2),
        # avec résilience : si le graphe est indisponible, on bascule sur la
        # mémoire vectorielle (pgvector) et on signale l'état dégradé.
        user_context, graph_degraded = self._load_user_preferences(user_id, query)
        if graph_degraded:
            yield StreamStep(
                type="thought",
                content="[Mode dégradé] Graphe de connaissances indisponible — bascule sur la mémoire vectorielle (pgvector) et la recherche web.",
            ).model_dump()
        elif user_context:
            yield StreamStep(
                type="thought",
                content=f"[Graph User Memory] Profil utilisateur '{user_id}' chargé depuis le graphe sémantique.",
            ).model_dump()

        ctx = RAGContext(
            query=query,
            media_type=media_type,
            user_id=user_id,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
            use_slm=complexity
            in [1, 2],  # On utilise le SLM pour les niveaux 1 et 2 (déchargement)
            memories=self._get_memories(user_id, query),
            current_state=RAGState.PLAN,
            graph_expert=(
                getattr(
                    self.orchestrator.processors[RAGState.GRAPH_EXPLORE],
                    "graph_expert",
                    None,
                )
                if self.orchestrator
                and RAGState.GRAPH_EXPLORE in self.orchestrator.processors
                else None
            ),
            truth_path=user_context,
            language=language,
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
                        query=ctx.query, response=response_obj, collector=xai_collector
                    )
                    yield StreamStep(
                        type="xai_report", content=report
                    ).model_dump()  # Yield StreamStep directly
                except Exception as e:
                    logger.error(f"Error generating XAI report: {e}", exc_info=True)
            # Enregistrement asynchrone de l'interaction utilisateur dans Neo4j (Task 5.2)
            if user_id and self.neo4j_manager:
                import threading  # noqa: E402

                threading.Thread(
                    target=self.neo4j_manager.sync_user_interaction,
                    args=(user_id, query, "SEARCH"),
                    daemon=True,
                ).start()

        if self.obs_service:
            self.obs_service.log_rag_latency(time.time() - start_time, query, user_id)

    # --- MÉTHODES UTILITAIRES ---
    def _assess_complexity(self, query: str) -> tuple[int, int]:
        try:
            from .complexity_analyser import ComplexityAnalyser  # noqa: E402

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
        yield StreamStep(
            type="thought", content="[Cache] ⚡ Réponse trouvée en cache !"
        ).model_dump()
        for token in text.split(" "):
            yield StreamStep(type="token", content=token + " ").model_dump()
            time.sleep(0.01)

    def _get_memories(self, user_id: Optional[str], query: str) -> str:
        if self.memory_service and user_id:
            return self.memory_service.retrieve_relevant_memories(user_id, query)
        return ""

    def _load_user_preferences(
        self, user_id: Optional[str], query: str
    ) -> tuple[str, bool]:
        """Load the user-preference context with graph-outage resilience.

        Returns ``(context, degraded)``. The graph is the primary source; when
        it is unreachable we fall back to the pgvector memory store instead of
        silently proceeding with an empty context, and surface a degraded-state
        signal (observability + a caller-visible flag).
        """
        if not (user_id and self.neo4j_manager):
            return "", False

        context = ""
        try:
            context = self.neo4j_manager.get_user_preferences_context(user_id) or ""
        except Exception as e:  # adapter already guards, but stay defensive
            logger.warning(f"Graph preference lookup failed: {e}")
            context = ""

        if context:
            return context, False

        # Empty context: tell "user has no history" apart from "graph is down".
        if not _graph_is_degraded(self.neo4j_manager):
            return "", False

        # Degraded: fall back to the pgvector memory store and report it.
        fallback = self._get_memories(user_id, query)
        if self.obs_service:
            self.obs_service.log_error(
                error_type="GraphDegraded",
                message=(
                    f"Neo4j unreachable; fell back to vector memory for user={user_id}"
                ),
            )
        logger.warning(
            "⚠️ Knowledge graph degraded — using pgvector memory fallback "
            f"for user={user_id}"
        )
        return fallback, True

    def _store_results(self, query: str, answer: str, user_id: Optional[str]):
        if self.semantic_cache:
            try:
                self.semantic_cache.set_cached_response(query, answer)
            except InfrastructureError as e:
                logger.error(f"Semantic Cache storage failed: {e}")
            except (InferenceError, InfrastructureError, RuntimeError) as e:
                logger.error(f"Unexpected error in Cache storage: {e}")

        if self.memory_service and user_id:
            try:
                self.memory_service.store_memory(
                    user_id,
                    [
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": answer},
                    ],
                )
            except InfrastructureError as e:
                logger.error(f"Long-term memory storage failed for user {user_id}: {e}")
            except (InferenceError, InfrastructureError, RuntimeError) as e:
                logger.error(f"Unexpected error in memory storage: {e}")

    def _extract_json(self, text: str) -> Dict:
        import orjson  # noqa: E402

        try:
            if "{" in text and "}" in text:
                json_str = text[text.find("{") : text.rfind("}") + 1]
                return orjson.loads(json_str)
        except orjson.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON from AI output: {e}. Output was: {text[:200]}..."
            )
        except (InferenceError, InfrastructureError, RuntimeError) as e:
            logger.error(f"Unexpected error during JSON extraction: {e}")
        return {}

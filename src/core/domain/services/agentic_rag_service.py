import logging
import time
import orjson
from enum import Enum
from typing import List, Dict, Optional, Generator, Any
from pydantic import BaseModel
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from .advanced_rag_service import AdvancedRAGService
from .prompt_manager import PromptManager
from .llm_service import LLMService
from ..entities.ai_schemas import (
    SearchPlan, CritiqueResult, StreamStep, JudgeEvaluation, JudgeAction
)
from .rag.agents import SearchPlanner, ResponseCritic, ResponseSynthesizer, ResponseJudge, ScoutAgent, GraphExpert

logger = logging.getLogger("animetix.rag")

class RAGState(str, Enum):
    """États de la machine à états RAG."""
    ANALYZE = "ANALYZE"
    PLAN = "PLAN"
    GRAPH_EXPLORE = "GRAPH_EXPLORE"
    RESEARCH = "RESEARCH"
    SYNTHESIZE = "SYNTHESIZE"
    JUDGE = "JUDGE"
    FINALIZE = "FINALIZE"
    FAILED = "FAILED"

class RAGContext(BaseModel):
    """Contexte de la session RAG agentique."""
    model_config = {"arbitrary_types_allowed": True}
    
    query: str
    media_type: str
    user_id: Optional[str] = None
    thinking_budget: int = 0
    thinking_mode: bool = False
    memories: str = ""
    plan: Optional[SearchPlan] = None
    raw_context: str = ""
    truth_path: str = ""
    full_answer: str = ""
    correction_feedback: Optional[str] = None
    iteration: int = 0
    max_iterations: int = 10
    current_state: RAGState = RAGState.ANALYZE
    graph_expert: Optional[GraphExpert] = None

class AgenticRAGService:
    """
    Orchestrateur RAG Agentique 2.0.
    Gère la boucle de réflexion et coordonne les agents spécialisés via une machine à états.
    """
    def __init__(
        self, 
        inference_engine: InferencePort, 
        rag_service: AdvancedRAGService,
        web_search: WebSearchPort,
        prompt_manager: PromptManager,
        llm_service: Optional[LLMService] = None,
        neo4j_manager=None,
        memory_service=None,
        semantic_cache=None,
        obs_service=None,
        graph_expert: Optional[GraphExpert] = None
    ):
        self.inference_engine = inference_engine
        self.rag_service = rag_service
        self.web_search = web_search
        self.prompt_manager = prompt_manager
        self.llm_service = llm_service or LLMService(inference_engine, prompt_manager)
        self.neo4j_manager = neo4j_manager
        self.memory_service = memory_service
        self.semantic_cache = semantic_cache
        self.obs_service = obs_service
        self.graph_expert = graph_expert or GraphExpert(self.llm_service, prompt_manager)

        # Initialisation des agents spécialisés
        self.planner = SearchPlanner(self.llm_service, prompt_manager)
        self.critic = ResponseCritic(self.llm_service, prompt_manager)
        self.synthesizer = ResponseSynthesizer(inference_engine, prompt_manager)
        self.judge = ResponseJudge(self.llm_service, prompt_manager, obs_service)
        self.scout = ScoutAgent(self.llm_service, prompt_manager, neo4j_manager)

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
        """Boucle principale orchestrée sous forme de machine à états."""
        
        # 1. ANALYSE COMPLEXITÉ ET INITIALISATION CONTEXTE
        thinking_budget, complexity = self._assess_complexity(query)
        thinking_mode = complexity >= 2
        
        if thinking_budget > 0 or thinking_mode:
            yield StreamStep(type="thought", content=f"[TTC] Requête complexe (Score {complexity}). Budget: {thinking_budget} tokens. Mode Thinking: {thinking_mode}").model_dump()

        if cached := self._check_cache(query):
            yield from self._stream_cached_response(cached)
            return
            
        ctx = RAGContext(
            query=query,
            media_type=media_type,
            user_id=user_id,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
            memories=self._get_memories(user_id, query),
            current_state=RAGState.PLAN,
            graph_expert=self.graph_expert
        )

        # 2. BOUCLE DE LA MACHINE À ÉTATS
        while ctx.current_state not in [RAGState.FINALIZE, RAGState.FAILED] and ctx.iteration < ctx.max_iterations:
            ctx.iteration += 1
            yield StreamStep(type="thought", content=f"[State Machine] Itération {ctx.iteration} - État: {ctx.current_state}").model_dump()

            try:
                if ctx.current_state == RAGState.PLAN:
                    yield from self._handle_plan(ctx)
                elif ctx.current_state == RAGState.GRAPH_EXPLORE:
                    yield from self._handle_graph_explore(ctx)
                elif ctx.current_state == RAGState.RESEARCH:
                    yield from self._handle_research(ctx)
                elif ctx.current_state == RAGState.SYNTHESIZE:
                    yield from self._handle_synthesize(ctx)
                elif ctx.current_state == RAGState.JUDGE:
                    yield from self._handle_judge(ctx)
                else:
                    ctx.current_state = RAGState.FINALIZE
            except Exception as e:
                logger.error(f"Erreur critique dans l'état {ctx.current_state}: {e}", exc_info=True)
                yield StreamStep(type="thought", content=f"[Error] Une erreur est survenue dans l'état {ctx.current_state}. Tentative de finalisation...").model_dump()
                ctx.current_state = RAGState.FAILED

        # 3. FINALISATION
        self._store_results(ctx.query, ctx.full_answer, ctx.user_id)

    # --- HANDLERS D'ÉTATS ---

    def _handle_plan(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[Planner] Établissement du plan de recherche...").model_dump()
        start = time.time()
        ctx.plan = self.planner.plan(
            ctx.query, 
            ctx.memories, 
            thinking_budget=ctx.thinking_budget // 2, 
            thinking_mode=ctx.thinking_mode
        )
        logger.info(f"PERF: Planner took {(time.time() - start)*1000:.2f}ms")
        
        if ctx.plan.requires_graph:
            ctx.current_state = RAGState.GRAPH_EXPLORE
        else:
            ctx.current_state = RAGState.RESEARCH

    def _handle_graph_explore(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if not ctx.plan:
            ctx.current_state = RAGState.PLAN
            return

        if not self.neo4j_manager:
            yield StreamStep(type="thought", content="[Graph-Agent] Neo4j non disponible pour l'exploration.").model_dump()
            ctx.current_state = RAGState.RESEARCH
            return

        yield StreamStep(type="thought", content="[Graph-Agent] Génération d'une requête Cypher...").model_dump()
        
        # Le GraphExpert peut être dans ctx ou self. On utilise self.graph_expert
        cypher = self.graph_expert.generate_cypher(ctx.query, ctx.plan.reasoning)
        
        if cypher:
            yield StreamStep(type="thought", content=f"[Graph-Agent] Exécution Cypher : {cypher}").model_dump()
            try:
                results = self.neo4j_manager.execute_query(cypher)
                if results:
                    res_str = f"\n[Graph-Agent Results]:\n{results}\n"
                    # On ajoute au truth_path comme demandé (pourra être enrichi par Research après)
                    ctx.truth_path += res_str
                else:
                    yield StreamStep(type="thought", content="[Graph-Agent] Aucun résultat trouvé dans le graphe.").model_dump()
            except Exception as e:
                logger.error(f"Graph execution failed: {e}")
                yield StreamStep(type="thought", content=f"[Graph-Agent] Erreur d'exécution Cypher : {e}").model_dump()
        else:
            yield StreamStep(type="thought", content="[Graph-Agent] Impossible de générer une requête Cypher pertinente.").model_dump()
        
        ctx.current_state = RAGState.RESEARCH

    def _handle_research(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if not ctx.plan:
            ctx.current_state = RAGState.PLAN
            return

        source = 'Web' if ctx.plan.requires_web else 'Local'
        yield StreamStep(type="thought", content=f"[Searcher] Exécution recherche ({source})...").model_dump()
        
        search_start = time.time()
        ctx.raw_context = self._execute_search(ctx.plan, ctx.media_type)
        logger.info(f"PERF: Searcher ({source}) took {(time.time() - search_start)*1000:.2f}ms")
        
        yield StreamStep(type="thought", content="[Scout] Distillation du contexte en Chemin de Vérité...").model_dump()
        scout_start = time.time()
        distilled = self.scout.find_truth_path(ctx.query, ctx.plan, ctx.raw_context)
        
        # On append pour ne pas perdre les infos du GraphExpert
        if ctx.truth_path:
            ctx.truth_path += f"\n[Scout Distillation]:\n{distilled}"
        else:
            ctx.truth_path = distilled
            
        logger.info(f"PERF: Scout took {(time.time() - scout_start)*1000:.2f}ms")
        
        ctx.current_state = RAGState.SYNTHESIZE

    def _handle_synthesize(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if ctx.correction_feedback:
            yield StreamStep(type="thought", content="[Synthesizer] Tentative d'auto-correction...").model_dump()
        else:
            yield StreamStep(type="thought", content="[Synthesizer] Rédaction de la réponse expert...").model_dump()
        
        ctx.full_answer = ""
        syn_start = time.time()
        for token in self.synthesizer.synthesize_stream(
            ctx.query, 
            ctx.truth_path, 
            thinking_budget=ctx.thinking_budget, 
            thinking_mode=ctx.thinking_mode,
            correction_feedback=ctx.correction_feedback
        ):
            ctx.full_answer += token
            yield StreamStep(type="token", content=token).model_dump()
        
        logger.info(f"PERF: Synthesizer took {(time.time() - syn_start)*1000:.2f}ms")
        ctx.current_state = RAGState.JUDGE

    def _handle_judge(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[Judge] Évaluation de la fiabilité...").model_dump()
        judge_start = time.time()
        evaluation = self.judge.evaluate(ctx.query, ctx.truth_path, ctx.full_answer)
        
        if not evaluation:
            logger.warning("Judge failed to return evaluation. Finalizing.")
            ctx.current_state = RAGState.FINALIZE
            return

        logger.info(f"PERF: Judge took {(time.time() - judge_start)*1000:.2f}ms")
        yield StreamStep(type="eval", content=evaluation.model_dump()).model_dump()
        
        action = evaluation.next_action
        if action == JudgeAction.APPROVE:
            ctx.current_state = RAGState.FINALIZE
        elif action == JudgeAction.REWRITE:
            ctx.correction_feedback = f"DÉFAUT DÉTECTÉ: {evaluation.reasoning}. Corrige en restant fidèle au contexte."
            ctx.current_state = RAGState.SYNTHESIZE
        elif action == JudgeAction.RESEARCH_MORE:
            # On pourrait injecter evaluation.reasoning dans le plan ici
            ctx.current_state = RAGState.RESEARCH
        elif action == JudgeAction.REPLAN:
            ctx.current_state = RAGState.PLAN
        else:
            ctx.current_state = RAGState.FINALIZE

    # --- MÉTHODES UTILITAIRES (Inchangées ou légèrement adaptées) ---
    def _assess_complexity(self, query: str) -> tuple[int, int]:
        prompt, sys = self.prompt_manager.get_prompt("complexity_analyzer", query=query)
        res = self.llm_service.generate(prompt, sys, use_slm=True)
        try:
            data = self._extract_json(res)
            return int(data.get("thinking_budget", 0)), int(data.get("complexity_score", 0))
        except Exception as e:
            logger.error(f"Error parsing complexity metrics: {e}")
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

    def _execute_search(self, plan, media_type: str) -> str:
        if plan.requires_web:
            results = self.web_search.search(plan.optimized_query)
            return "\n".join([f"WEB - {r['title']}: {r['snippet']}" for r in results])
        
        ctx = ""
        results = self.rag_service.hybrid_search(plan.optimized_query, media_type)
        ctx += "\n".join([f"DB - {r.get('title')}: {r.get('description', '')[:500]}" for r in results])
        
        if self.neo4j_manager and plan.entities:
            if plan.graph_traversal_steps:
                traversal = self.neo4j_manager.multi_hop_traversal(plan.entities[0], plan.graph_traversal_steps)
                ctx += f"\nGRAPH_PATH:\n{traversal}"
            else:
                graph_ctx = self.neo4j_manager.get_enriched_context(plan.entities)
                ctx += f"\nGRAPH:\n{graph_ctx}"
        return ctx

    def _store_results(self, query: str, answer: str, user_id: str):
        if self.semantic_cache:
            try: 
                self.semantic_cache.set_cached_response(query, answer)
            except Exception as e:
                logger.error(f"Semantic Cache storage failed: {e}")
        if self.memory_service and user_id:
            try: 
                self.memory_service.store_memory(user_id, [{"role": "user", "content": query}, {"role": "assistant", "content": answer}])
            except Exception as e:
                logger.error(f"Long-term memory storage failed for user {user_id}: {e}")

    def _extract_json(self, text: str) -> Dict:
        try:
            if '{' in text and '}' in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
                return orjson.loads(json_str)
        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI output: {e}. Output was: {text[:200]}...")
        except Exception as e:
            logger.error(f"Unexpected error during JSON extraction: {e}")
        return {}

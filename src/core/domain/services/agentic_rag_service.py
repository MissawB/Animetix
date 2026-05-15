import logging
import time
import orjson
from typing import List, Dict, Optional, Generator
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from .advanced_rag_service import AdvancedRAGService
from .prompt_manager import PromptManager
from .llm_service import LLMService
from ..entities.ai_schemas import (
    SearchPlan, CritiqueResult, StreamStep, JudgeEvaluation
)
from .rag.agents import SearchPlanner, ResponseCritic, ResponseSynthesizer, ResponseJudge, ScoutAgent

logger = logging.getLogger("animetix.rag")

class AgenticRAGService:
    """
    Orchestrateur RAG Agentique 2.0.
    Gère la boucle de réflexion et coordonne les agents spécialisés.
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
        obs_service=None
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

        # Initialisation des agents spécialisés
        self.planner = SearchPlanner(self.llm_service, prompt_manager)
        self.critic = ResponseCritic(self.llm_service, prompt_manager)
        self.synthesizer = ResponseSynthesizer(inference_engine, prompt_manager)
        self.judge = ResponseJudge(self.llm_service, prompt_manager, obs_service)
        self.scout = ScoutAgent(self.llm_service, prompt_manager, neo4j_manager)

    def plan_and_solve(self, query: str, media_type: str, user_id: Optional[str] = None) -> str:
        """Wrapper non-streaming."""
        full_answer = ""
        for event in self.plan_and_solve_stream(query, media_type, user_id):
            if event['type'] == 'token':
                full_answer += event['content']
        return full_answer

    def plan_and_solve_stream(self, query: str, media_type: str, user_id: Optional[str] = None) -> Generator[Dict, None, None]:
        """Boucle principale orchestrée par agents avec Architecture Scout."""
        
        # 1. ANALYSE COMPLEXITÉ (TTC)
        thinking_budget, complexity = self._assess_complexity(query)
        if thinking_budget > 0:
            yield StreamStep(type="thought", content=f"[TTC] Requête complexe (Score {complexity}). Budget: {thinking_budget} tokens.").model_dump()

        # 2. CACHE & MÉMOIRE
        if cached := self._check_cache(query):
            yield from self._stream_cached_response(cached)
            return
            
        memories = self._get_memories(user_id, query)

        # 3. PLANIFICATION
        yield StreamStep(type="thought", content="[Planner] Établissement du plan de recherche...").model_dump()
        start = time.time()
        plan = self.planner.plan(query, memories, thinking_budget=thinking_budget // 2)
        logger.info(f"PERF: Planner took {(time.time() - start)*1000:.2f}ms")

        # 4. RÉCUPÉRATION & SCOUTING (BOUCLE)
        raw_context = ""
        truth_path = ""
        
        for i in range(2):
            source = 'Web' if plan.requires_web else 'Local'
            yield StreamStep(type="thought", content=f"[Searcher] Exécution recherche ({source})...").model_dump()
            
            search_start = time.time()
            raw_context = self._execute_search(plan, media_type)
            logger.info(f"PERF: Searcher ({source}) took {(time.time() - search_start)*1000:.2f}ms")
            
            # --- ARCHITECTURE SCOUT (SOTA 2026) ---
            yield StreamStep(type="thought", content="[Scout] Distillation du contexte brut en Chemin de Vérité...").model_dump()
            scout_start = time.time()
            truth_path = self.scout.find_truth_path(query, plan, raw_context)
            logger.info(f"PERF: Scout took {(time.time() - scout_start)*1000:.2f}ms")
            
            yield StreamStep(type="thought", content="[Critic] Évaluation du Chemin de Vérité...").model_dump()
            critic_start = time.time()
            critique = self.critic.evaluate(query, truth_path, thinking_budget=thinking_budget // 4)
            logger.info(f"PERF: Critic took {(time.time() - critic_start)*1000:.2f}ms")

            if critique.is_relevant or critique.suggested_action == "PROCEED":
                break
            else:
                yield StreamStep(type="thought", content=f"[Critic] Amélioration requise: {critique.suggested_action}").model_dump()
                plan.requires_web = (critique.suggested_action == "TRIGGER_WEB")

        # 5. SYNTHÈSE FINALE (Modèle 8B+ sur le Truth Path pré-mâché)
        yield StreamStep(type="thought", content="[Synthesizer] Rédaction de la réponse expert...").model_dump()
        full_answer = ""
        syn_start = time.time()
        for token in self.synthesizer.synthesize_stream(query, truth_path, thinking_budget=thinking_budget):
            full_answer += token
            yield StreamStep(type="token", content=token).model_dump()
        logger.info(f"PERF: Synthesizer took {(time.time() - syn_start)*1000:.2f}ms")

        # 6. ÉVALUATION & PERSISTANCE
        yield StreamStep(type="thought", content="[Judge] Évaluation de la fiabilité...").model_dump()
        judge_start = time.time()
        if evaluation := self.judge.evaluate(query, truth_path, full_answer):
            logger.info(f"PERF: Judge took {(time.time() - judge_start)*1000:.2f}ms")
            if not evaluation.is_reliable:
                yield StreamStep(type="thought", content=f"⚠️ Fiabilité : {evaluation.reasoning}").model_dump()
                
            if getattr(evaluation, 'hallucination_detected', False):
                # --- SELF-EVOLVING: AUTO-CORRECTION ---
                bad_input = f"Requête: {query}\nContexte: {truth_path[:500]}..." 
                good_output = "RÉPONSE IDÉALE : Je ne peux pas répondre avec certitude..."
                yield StreamStep(type="thought", content="[Metacognition] Hallucination détectée. Enregistrement d'une auto-correction...").model_dump()
                self.prompt_manager.add_few_shot_correction("synthesizer_final", bad_input, good_output)
                
            yield StreamStep(type="eval", content=evaluation.model_dump()).model_dump()

        self._store_results(query, full_answer, user_id)

    def _assess_complexity(self, query: str) -> tuple[int, int]:
        prompt, sys = self.prompt_manager.get_prompt("complexity_analyzer", query=query)
        res = self.llm_service.generate(prompt, sys, use_slm=True)
        try:
            data = self._extract_json(res)
            return int(data.get("thinking_budget", 0)), int(data.get("complexity_score", 0))
        except: return 0, 0

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
            try: self.semantic_cache.set_cached_response(query, answer)
            except: pass
        if self.memory_service and user_id:
            try: self.memory_service.store_memory(user_id, [{"role": "user", "content": query}, {"role": "assistant", "content": answer}])
            except: pass

    def _extract_json(self, text: str) -> Dict:
        try:
            if '{' in text and '}' in text:
                return orjson.loads(text[text.find('{'):text.rfind('}')+1])
        except: pass
        return {}

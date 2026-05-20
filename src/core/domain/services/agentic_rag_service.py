import logging
import time
import orjson
from enum import Enum
from typing import List, Dict, Optional, Generator, Any
from pydantic import BaseModel, Field
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from .advanced_rag_service import AdvancedRAGService
from .prompt_manager import PromptManager
from .llm_service import LLMService
from .xai_service import UncertaintyService
from ..entities.ai_schemas import (
    SearchPlan, CritiqueResult, StreamStep, JudgeEvaluation, JudgeAction, DebateOutcome,
    RAGState, RAGContext
)
from .rag.agents import SearchPlanner, ResponseCritic, ResponseSynthesizer, ResponseJudge, ScoutAgent, GraphExpert
from .rag.agents.debate_manager import DebateManager
from .rag.agents.librarian import LibrarianAgent

logger = logging.getLogger("animetix.rag")

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
        graph_expert: Optional[GraphExpert] = None,
        debate_manager: Optional[DebateManager] = None,
        librarian: Optional[LibrarianAgent] = None,
        uncertainty_service: Optional[UncertaintyService] = None
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
        self.debate_manager = debate_manager
        self.librarian = librarian or LibrarianAgent(self.llm_service, prompt_manager)
        self.uncertainty_service = uncertainty_service or UncertaintyService(inference_engine)

        # Initialisation des agents spécialisés
        self.planner = SearchPlanner(self.llm_service, prompt_manager)
        self.critic = ResponseCritic(self.llm_service, prompt_manager)
        self.synthesizer = ResponseSynthesizer(inference_engine, prompt_manager)
        self.judge = ResponseJudge(self.llm_service, prompt_manager, obs_service)
        self.scout = ScoutAgent(self.llm_service, prompt_manager, neo4j_manager)
        self.debate_manager = debate_manager or DebateManager(self.llm_service, prompt_manager)

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
                elif ctx.current_state == RAGState.ACQUIRE_KNOWLEDGE:
                    yield from self._handle_acquire_knowledge(ctx)
                elif ctx.current_state == RAGState.VLM_RERANK:
                    yield from self._handle_vlm_rerank(ctx)
                elif ctx.current_state == RAGState.SYNTHESIZE:
                    yield from self._handle_synthesize(ctx)
                elif ctx.current_state == RAGState.JUDGE:
                    yield from self._handle_judge(ctx)
                elif ctx.current_state == RAGState.FALLBACK_RAG:
                    yield from self._handle_fallback_rag(ctx)
                else:
                    ctx.current_state = RAGState.FINALIZE
            except Exception as e:
                logger.error(f"Erreur critique dans l'état {ctx.current_state}: {e}", exc_info=True)
                if ctx.current_state != RAGState.FALLBACK_RAG:
                    yield StreamStep(type="thought", content=f"[Recovery] Erreur dans {ctx.current_state}. Bascule vers le mode RAG classique de secours...").model_dump()
                    ctx.current_state = RAGState.FALLBACK_RAG
                else:
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
        results, ctx_str = self._execute_search(ctx.plan, ctx.media_type)
        ctx.candidates = results
        ctx.raw_context = ctx_str
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
        
        if ctx.plan.is_visual_query:
            ctx.current_state = RAGState.VLM_RERANK
        else:
            ctx.current_state = RAGState.SYNTHESIZE

    def _handle_acquire_knowledge(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[Librarian] Analyse des lacunes de connaissances...").model_dump()
        
        gap = self.librarian.identify_gap(ctx.query, ctx.truth_path)
        
        if gap and gap.get("query"):
            yield StreamStep(type="thought", content=f"[Librarian] Recherche active sur {gap.get('source_type', 'Web')} : {gap['query']}").model_dump()
            
            fresh_data = self.librarian.fetch_data(gap)
            
            if fresh_data:
                ctx.truth_path += f"\n\n### FRESH WEB/JIKAN DATA ###\n{fresh_data}\n"
                yield StreamStep(type="thought", content="[Librarian] Nouvelles connaissances intégrées au Chemin de Vérité.").model_dump()
            else:
                yield StreamStep(type="thought", content="[Librarian] Aucune donnée supplémentaire trouvée.").model_dump()
        else:
            yield StreamStep(type="thought", content="[Librarian] Aucune lacune critique identifiée.").model_dump()
            
        ctx.current_state = RAGState.SYNTHESIZE

    def _handle_vlm_rerank(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[VLM-Reranker] Analyse visuelle des images candidates...").model_dump()
        
        # Extraction des URLs d'images
        image_urls = []
        valid_candidates = []
        for c in ctx.candidates:
            # On cherche plusieurs champs possibles pour l'image
            url = c.get('image') or c.get('image_url') or c.get('cover_url') or c.get('poster_path')
            if url:
                image_urls.append(url)
                valid_candidates.append(c)
        
        if not image_urls:
            yield StreamStep(type="thought", content="[VLM-Reranker] Aucune image exploitable trouvée pour le reranking.").model_dump()
            ctx.current_state = RAGState.SYNTHESIZE
            return

        try:
            # Récupération du prompt spécifique via le PromptManager
            prompt_text, system_prompt = self.prompt_manager.get_prompt(
                "vlm_reranker", 
                query=ctx.query, 
                num_images=len(image_urls)
            )

            # Appel au VLM pour le reranking
            # La méthode visual_rerank doit retourner une liste de dicts avec 'index' et 'score'
            reranked = self.inference_engine.visual_rerank(prompt_text, image_urls, system_prompt=system_prompt)
            
            # Attribution des scores aux candidats
            for item in reranked:
                idx = item.get('index')
                if idx is not None and idx < len(valid_candidates):
                    valid_candidates[idx]['visual_score'] = item.get('score', 0.0)
            
            # Tri par score visuel décroissant
            valid_candidates.sort(key=lambda x: x.get('visual_score', 0.0), reverse=True)
            
            # Mise à jour du truth_path avec le top 5 re-classé (on append pour préserver Graph/Scout)
            top_5 = valid_candidates[:5]
            vlm_context = "\n### VÉRIFICATION VISUELLE (RERANKING) ###\n"
            for i, c in enumerate(top_5):
                vlm_context += f"{i+1}. {c.get('title')} (Score Visuel: {c.get('visual_score', 0.0):.2f})\n"
                vlm_context += f"   - Description: {c.get('description', '')[:300]}...\n"
            
            ctx.truth_path += f"\n{vlm_context}"
            yield StreamStep(type="thought", content=f"[VLM-Reranker] Classement visuel terminé. Top match : {top_5[0].get('title')}").model_dump()
            
        except Exception as e:
            logger.error(f"VLM Rerank error: {e}")
            yield StreamStep(type="thought", content=f"[VLM-Reranker] Échec de l'analyse visuelle : {str(e)}").model_dump()
            
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
        
        # --- MESURE D'INCERTITUDE ---
        if not ctx.knowledge_acquired:
            confidence = self.uncertainty_service.measure_confidence(ctx.query, ctx.full_answer)
            if confidence < 0.6:
                yield StreamStep(type="thought", content=f"[Uncertainty] Basse confiance détectée ({confidence:.2f}). Déclenchement du Librarian...").model_dump()
                ctx.knowledge_acquired = True
                ctx.current_state = RAGState.ACQUIRE_KNOWLEDGE
                return

        ctx.current_state = RAGState.JUDGE

    def _handle_judge(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[Swarm] Début du débat multi-agents...").model_dump()
        judge_start = time.time()
        
        # Conduire le débat via le DebateManager
        outcome = self.debate_manager.conduct_debate(ctx.query, ctx.truth_path, ctx.full_answer)
        ctx.debate_outcome = outcome
        
        logger.info(f"PERF: Multi-Agent Debate took {(time.time() - judge_start)*1000:.2f}ms")
        
        yield StreamStep(
            type="thought", 
            content=f"[Swarm] Consensus : {outcome.consensus_action}. Raisonnement : {outcome.final_reasoning}"
        ).model_dump()
        
        # Yield d'un step eval avec le résultat complet
        yield StreamStep(type="eval", content=outcome.model_dump()).model_dump()
        
        action = outcome.consensus_action
        
        # Best-effort : Si on a déjà trop d'itérations, on force l'approbation
        if ctx.iteration >= 3 and action == JudgeAction.REWRITE:
            yield StreamStep(type="thought", content="[Swarm] Seuil de correction atteint. Livraison de la meilleure réponse actuelle.").model_dump()
            ctx.current_state = RAGState.FINALIZE
            return

        if action == JudgeAction.APPROVE:
            ctx.current_state = RAGState.FINALIZE
        elif action == JudgeAction.REWRITE:
            ctx.correction_feedback = f"DÉFAUT DÉTECTÉ: {outcome.final_reasoning}. Corrige en restant fidèle au contexte."
            ctx.current_state = RAGState.SYNTHESIZE
        elif action == JudgeAction.RESEARCH_MORE:
            if len(ctx.truth_path) < 200 and not ctx.knowledge_acquired:
                yield StreamStep(type="thought", content="[Judge] Contexte local insuffisant. Bascule vers Librarian pour chercher des infos fraîches...").model_dump()
                ctx.current_state = RAGState.ACQUIRE_KNOWLEDGE
            else:
                ctx.current_state = RAGState.RESEARCH
        elif action == JudgeAction.REPLAN:
            ctx.current_state = RAGState.PLAN
        else:
            ctx.current_state = RAGState.FINALIZE

    def _handle_fallback_rag(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        """Mode de secours : RAG classique simplifié sans agents complexes."""
        yield StreamStep(type="thought", content="[Fallback] Exécution d'une recherche hybride standard...").model_dump()
        
        # Recherche hybride directe
        results = self.rag_service.hybrid_search(ctx.query, ctx.media_type)
        fallback_context = "\n".join([f"- {r.get('title')}: {r.get('description', '')[:500]}" for r in results])
        
        yield StreamStep(type="thought", content="[Fallback] Synthèse de la réponse de secours...").model_dump()
        
        # Prompt simplifié pour la synthèse
        prompt = f"Réponds à la question suivante en utilisant UNIQUEMENT le contexte fourni.\nQUESTION: {ctx.query}\nCONTEXTE:\n{fallback_context}"
        system = "Tu es un assistant expert. Sois concis et factuel."
        
        ctx.full_answer = ""
        for token in self.inference_engine.stream_generate(prompt, system):
            ctx.full_answer += token
            yield StreamStep(type="token", content=token).model_dump()
            
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

    def _execute_search(self, plan, media_type: str) -> tuple[List[Dict], str]:
        if plan.requires_web:
            results = self.web_search.search(plan.optimized_query)
            context = "\n".join([f"WEB - {r['title']}: {r['snippet']}" for r in results])
            return results, context
        
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
        return results, ctx

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

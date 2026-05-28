import logging
import time
import yaml
import os
from typing import List, Dict, Optional, Generator, Any
from core.ports.inference_port import InferencePort
from core.ports.web_search_port import WebSearchPort
from core.ports.graph_persistence_port import GraphPersistencePort
from core.ports.mlops_port import MlopsPort
from .prompt_manager import PromptManager
from .llm_service import LLMService
from .xai_service import UncertaintyService
from .advanced_rag_service import AdvancedRAGService
from ..exceptions import (
    InfrastructureError, InferenceError, AnimetixError,
    InferenceTimeoutError, AgentLogicalFailure, ParsingError
)
from ..entities.ai_schemas import (
    StreamStep, JudgeAction, RAGState, RAGContext
)
from .rag.agents import SearchPlanner, ResponseCritic, ResponseSynthesizer, ResponseJudge, ScoutAgent, GraphExpert, SemanticRouter, RetrievalEvaluator, ContextCompressor
from .rag.agents.debate_manager import DebateManager
from .rag.agents.librarian import LibrarianAgent
from .rag.agents.forge import ForgeAgent
from .rag.agents.saga_agent import SagaAgent
from .rag.agents.chronicler import ChroniclerAgent
from pipeline.mlops.graph_community_partitioner import GraphCommunityPartitioner

logger = logging.getLogger("animetix.rag_workflow")

class RAGWorkflowManager:
    """
    Gère la machine à états et les transitions du workflow RAG agentique.
    """
    def __init__(
        self,
        planner: SearchPlanner,
        critic: ResponseCritic,
        synthesizer: ResponseSynthesizer,
        judge: ResponseJudge,
        scout: ScoutAgent,
        semantic_router: SemanticRouter,
        retrieval_evaluator: RetrievalEvaluator,
        community_partitioner: GraphCommunityPartitioner,
        graph_expert: GraphExpert,
        debate_manager: DebateManager,
        librarian: LibrarianAgent,
        forge: ForgeAgent,
        saga_agent: SagaAgent,
        chronicler: ChroniclerAgent,
        uncertainty_service: UncertaintyService,
        inference_engine: InferencePort,
        web_search: WebSearchPort,
        prompt_manager: PromptManager,
        rag_service: AdvancedRAGService,
        neo4j_manager: Optional[GraphPersistencePort] = None,
        context_compressor: Optional[ContextCompressor] = None,
        mlops_port: Optional[MlopsPort] = None,
        colbert_adapter: Any = None
    ):
        self.planner = planner
        self.critic = critic
        self.synthesizer = synthesizer
        self.judge = judge
        self.scout = scout
        self.semantic_router = semantic_router
        self.retrieval_evaluator = retrieval_evaluator
        self.community_partitioner = community_partitioner
        self.graph_expert = graph_expert
        self.debate_manager = debate_manager
        self.librarian = librarian
        self.forge = forge
        self.saga_agent = saga_agent
        self.chronicler = chronicler
        self.uncertainty_service = uncertainty_service
        self.inference_engine = inference_engine
        self.web_search = web_search
        self.prompt_manager = prompt_manager
        self.rag_service = rag_service
        self.neo4j_manager = neo4j_manager
        self.mlops_port = mlops_port
        self.colbert_adapter = colbert_adapter
        
        # SOTA 2026 Context Compressor (Task 5.3)
        self.context_compressor = context_compressor or ContextCompressor(self.rag_service.llm_service, self.prompt_manager)
        self.expert_facts = self._load_expert_facts()

    def _load_expert_facts(self) -> List[Dict]:
        """Charge les faits experts depuis le fichier YAML."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            yaml_path = os.path.join(current_dir, "prompts", "expert_facts.yaml")
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    return data.get('expert_facts', [])
            return []
        except Exception as e:
            logger.error(f"Erreur lors du chargement des faits experts: {e}")
            return []


    def _async_log_dpo(self, query: str, chosen: str, rejected: str):
        """Journalisation asynchrone des paires de préférence DPO via Celery."""
        if self.mlops_port:
            project_root = getattr(self.rag_service.repository, 'project_root', '')
            self.mlops_port.log_dpo_preference(query, chosen, rejected, project_root)
        else:
            logger.warning("💾 [DPO Logging] MlopsPort not available. Skipping log.")


    def run_workflow(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        """Exécute la boucle de la machine à états."""
        rejected_responses = []
        while ctx.current_state not in [RAGState.FINALIZE, RAGState.FAILED] and ctx.iteration < ctx.max_iterations:
            ctx.iteration += 1
            yield StreamStep(type="thought", content=f"[State Machine] Itération {ctx.iteration} - État: {ctx.current_state}").model_dump()

            try:
                if ctx.current_state == RAGState.PLAN:
                    yield from self._handle_plan(ctx)
                elif ctx.current_state == RAGState.SAGA_LOOKUP:
                    yield from self._handle_saga_lookup(ctx)
                elif ctx.current_state == RAGState.GRAPH_EXPLORE:
                    yield from self._handle_graph_explore(ctx)
                elif ctx.current_state == RAGState.RESEARCH:
                    yield from self._handle_research(ctx)
                elif ctx.current_state == RAGState.ACQUIRE_KNOWLEDGE:
                    yield from self._handle_acquire_knowledge(ctx)
                elif ctx.current_state == RAGState.SPECULATE:
                    yield from self._handle_speculate(ctx)
                elif ctx.current_state == RAGState.VLM_RERANK:
                    yield from self._handle_vlm_rerank(ctx)
                elif ctx.current_state == RAGState.SYNTHESIZE:
                    yield from self._handle_synthesize(ctx)
                elif ctx.current_state == RAGState.JUDGE:
                    yield from self._handle_judge(ctx)
                    if ctx.current_state == RAGState.SYNTHESIZE and ctx.full_answer:
                        rejected_responses.append(ctx.full_answer)
                elif ctx.current_state == RAGState.FALLBACK_RAG:
                    yield from self._handle_fallback_rag(ctx)
                else:
                    ctx.current_state = RAGState.FINALIZE
            except (InferenceTimeoutError, AgentLogicalFailure) as e:
                logger.warning(
                    "Agent logic or timeout failure",
                    extra={
                        "current_state": str(ctx.current_state),
                        "iteration": ctx.iteration,
                        "query": ctx.query,
                        "error_type": type(e).__name__
                    }
                )
                yield StreamStep(type="thought", content=f"[Recovery] Erreur de logique ou timeout ({type(e).__name__}) dans {ctx.current_state}. Bascule vers le mode RAG classique de secours...").model_dump()
                ctx.current_state = RAGState.FALLBACK_RAG
            except AnimetixError as e:
                logger.error(
                    f"Erreur critique dans l'état {ctx.current_state}: {e}",
                    extra={
                        "current_state": str(ctx.current_state),
                        "iteration": ctx.iteration,
                        "query": ctx.query
                    },
                    exc_info=True
                )
                if ctx.current_state != RAGState.FALLBACK_RAG:
                    yield StreamStep(type="thought", content=f"[Recovery] Erreur fatale dans {ctx.current_state}. Tentative de repli...").model_dump()
                    ctx.current_state = RAGState.FALLBACK_RAG
                else:
                    ctx.current_state = RAGState.FAILED

        # Logging DPO asynchrone autonome si une réécriture a eu lieu
        if ctx.current_state == RAGState.FINALIZE and rejected_responses and ctx.full_answer:
            self._async_log_dpo(ctx.query, ctx.full_answer, rejected_responses[0])

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
        
        if ctx.plan.requires_saga:
            ctx.current_state = RAGState.SAGA_LOOKUP
        elif ctx.plan.requires_graph:
            ctx.current_state = RAGState.GRAPH_EXPLORE
        else:
            ctx.current_state = RAGState.RESEARCH

    def _handle_saga_lookup(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[World-Brain] Analyse globale de la saga...").model_dump()
        
        saga_name = self.saga_agent.lookup_saga(ctx.query)
        if saga_name:
            ctx.saga_name = saga_name
            yield StreamStep(type="thought", content=f"[World-Brain] Saga détectée : {saga_name}. Récupération du résumé exécutif...").model_dump()
            
            summary = self.saga_agent.get_saga_context(saga_name)
            if summary:
                ctx.truth_path += f"\n\n### RÉSUMÉ GLOBAL DE LA SAGA ({saga_name}) ###\n{summary}\n"
                yield StreamStep(type="thought", content="[World-Brain] Contexte macro-temporel intégré.").model_dump()
            else:
                yield StreamStep(type="thought", content=f"[World-Brain] Aucun résumé trouvé pour la saga {saga_name}.").model_dump()
        else:
            yield StreamStep(type="thought", content="[World-Brain] Aucune saga macro-temporelle identifiée pour cette requête.").model_dump()

        if ctx.plan.requires_graph:
            ctx.current_state = RAGState.GRAPH_EXPLORE
        else:
            ctx.current_state = RAGState.RESEARCH

    def _handle_graph_explore(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if not ctx.plan:
            ctx.current_state = RAGState.PLAN
            return

        yield StreamStep(type="thought", content="[GraphRAG] Recherche de communautés thématiques transversales...").model_dump()
        communities = self.community_partitioner.search_communities(ctx.query)
        if communities:
            comm_ctx = "\n\n### CONTEXTE GRAPHRAG (COMMUNAUTÉS THÉMATIQUES) ###\n"
            for comm in communities:
                comm_ctx += f"- Communauté : {comm['name']}\n  Résumé : {comm['summary']}\n  Entités clés : {', '.join(comm['entities'])}\n"
            if ctx.truth_path is None:
                ctx.truth_path = ""
            ctx.truth_path += comm_ctx
            yield StreamStep(type="thought", content=f"[GraphRAG] Intégration de {len(communities)} résumé(s) de communauté(s) macro-conceptuelle(s).").model_dump()

        if not self.neo4j_manager:
            yield StreamStep(type="thought", content="[Graph-Agent] Neo4j non disponible pour l'exploration détaillée. Poursuite avec GraphRAG Communautaire...").model_dump()
            ctx.current_state = RAGState.RESEARCH
            return

        yield StreamStep(type="thought", content="[Graph-Agent] Génération d'une requête Cypher...").model_dump()
        cypher = self.graph_expert.generate_cypher(ctx.query, ctx.plan.reasoning)
        
        if cypher:
            yield StreamStep(type="thought", content=f"[Graph-Agent] Exécution Cypher : {cypher}").model_dump()
            try:
                results = self.neo4j_manager.execute_read(cypher)
                if results:
                    res_str = f"\n[Graph-Agent Results]:\n{results}\n"
                    if ctx.truth_path is None:
                        ctx.truth_path = ""
                    ctx.truth_path += res_str
                else:
                    yield StreamStep(type="thought", content="[Graph-Agent] Aucun résultat trouvé dans le graphe.").model_dump()
            except InfrastructureError as e:
                logger.error(f"Graph execution failed: {e}")
                yield StreamStep(type="thought", content=f"[Graph-Agent] Erreur d'exécution Cypher : {e}").model_dump()
            except (InferenceError, InfrastructureError) as e:
                logger.error(f"Unexpected Graph error: {e}")
                yield StreamStep(type="thought", content=f"[Graph-Agent] Erreur inattendue : {e}").model_dump()
        else:
            yield StreamStep(type="thought", content="[Graph-Agent] Impossible de générer une requête Cypher pertinente.").model_dump()
        
        ctx.current_state = RAGState.RESEARCH

    def _handle_research(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if not ctx.plan:
            ctx.current_state = RAGState.PLAN
            return

        if "théorie" in ctx.query.lower() or "theory" in ctx.query.lower() or "vrai que" in ctx.query.lower():
            logger.info(f"🔎 [Chronicler] Theory intent detected. Searching FanTheories...")
            yield StreamStep(type="thought", content="[Chronicler] Vérification des théories de fans dans la base...").model_dump()
            
            cypher = """
            MATCH (s:Saga)-[:HAS_THEORY]->(t:FanTheory)
            WHERE any(entity IN $entities WHERE toLower(s.name) CONTAINS toLower(entity) OR toLower(t.title) CONTAINS toLower(entity))
            RETURN t.title as title, t.description as desc, t.plausibility as plausibility
            LIMIT 3
            """
            
            cypher_fallback = """
            MATCH (t:FanTheory) 
            WHERE any(entity IN $entities WHERE toLower(t.title) CONTAINS toLower(entity) OR toLower(t.description) CONTAINS toLower(entity)) 
            RETURN t.title as title, t.description as desc, t.plausibility as plausibility 
            LIMIT 3
            """
            try:
                if ctx.plan.entities:
                    theories = self.neo4j_manager.execute_read(cypher, parameters={"entities": ctx.plan.entities})
                    if not theories:
                        theories = self.neo4j_manager.execute_read(cypher_fallback, parameters={"entities": ctx.plan.entities})
                    if theories:
                        theory_text = "### CONSENSUS DE FANS (THÉORIES) ###\n"
                        for th in theories:
                            theory_text += f"- {th['title']} (Plausibilité : {th['plausibility']}) : {th['desc']}\n"
                        if ctx.truth_path is None:
                            ctx.truth_path = ""
                        ctx.truth_path += f"\n{theory_text}"
                        yield StreamStep(type="thought", content=f"[Chronicler] Trouvé {len(theories)} théorie(s) pertinente(s).").model_dump()
            except InfrastructureError as e:
                logger.error(f"Failed to fetch fan theories: {e}")
            except (InferenceError, InfrastructureError, RuntimeError) as e:
                logger.error(f"Unexpected error in Chronicler: {e}")

        source = 'Web' if ctx.plan.requires_web else 'Local'
        yield StreamStep(type="thought", content=f"[Searcher] Exécution recherche ({source})...").model_dump()
        
        search_start = time.time()
        results, ctx_str = self._execute_search(ctx.plan, ctx.media_type)
        ctx.candidates = results
        ctx.raw_context = ctx_str
        logger.info(f"PERF: Searcher ({source}) took {(time.time() - search_start)*1000:.2f}ms")
        
        # --- COMPRESSION DE CONTEXTE SÉMANTIQUE (SOTA 2026 / Task 5.3) ---
        yield StreamStep(type="thought", content="[Context Compressor] Compression sémantique du contexte brut...").model_dump()
        ctx.raw_context = self.context_compressor.compress(ctx.query, ctx.raw_context)
        
        yield StreamStep(type="thought", content="[CRAG Evaluator] Évaluation de la pertinence et de la complétude du contexte extrait...").model_dump()
        eval_res = self.retrieval_evaluator.evaluate(ctx.query, ctx.raw_context)
        
        if not eval_res.is_sufficient and not ctx.plan.requires_web:
            yield StreamStep(
                type="thought", 
                content=f"[CRAG Evaluator] Contexte insuffisant (Score: {eval_res.relevance_score:.2f}). Déclenchement d'une recherche corrective ciblée sur le Web : \"{eval_res.corrective_query}\"..."
            ).model_dump()
            try:
                web_results = self.web_search.search(eval_res.corrective_query)
                if web_results:
                    web_ctx = "\n".join([f"- [Web Corrective]: {r.get('title')}: {r.get('snippet', '')}" for r in web_results[:4]])
                    ctx.raw_context += f"\n\n### RÉSULTATS CORRECTIFS WEB (CRAG) ###\n{web_ctx}\n"
                    yield StreamStep(type="thought", content="[CRAG Evaluator] Résultats correctifs web injectés avec succès.").model_dump()
                else:
                    yield StreamStep(type="thought", content="[CRAG Evaluator] Aucun résultat correctif web trouvé.").model_dump()
            except Exception as e:
                logger.error(f"❌ CRAG Web search failed: {e}")
                
        yield StreamStep(type="thought", content="[Scout] Distillation du contexte en Chemin de Vérité...").model_dump()
        scout_start = time.time()
        distilled = self.scout.find_truth_path(ctx.query, ctx.plan, ctx.raw_context)
        
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
                ctx.current_state = RAGState.SYNTHESIZE
            else:
                yield StreamStep(type="thought", content="[Librarian] Aucune donnée supplémentaire trouvée. Passage en mode spéculation...").model_dump()
                ctx.current_state = RAGState.SPECULATE
        else:
            yield StreamStep(type="thought", content="[Librarian] Aucune lacune critique identifiée.").model_dump()
            ctx.current_state = RAGState.SYNTHESIZE

    def _handle_speculate(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[The Forge] Lancement du moteur de spéculation logique...").model_dump()
        res = self.forge.generate_hypothesis(ctx.query, ctx.truth_path)
        
        if res and res.hypothesis:
            yield StreamStep(type="thought", content=f"[The Forge] Hypothèse générée : {res.hypothesis} (Basé sur : {res.rationale})").model_dump()
            speculation_block = f"\n\n### HYPOTHÈSE LOGIQUE (DÉDUCTION) ###\n"
            speculation_block += f"DÉDUCTION : {res.hypothesis}\n"
            speculation_block += f"RAISONNEMENT : {res.rationale}\n"
            speculation_block += f"NOTE : Cette information est une déduction logique basée sur les données disponibles et peut ne pas être factuelle à 100%.\n"
            ctx.truth_path += speculation_block
        else:
            yield StreamStep(type="thought", content="[The Forge] Impossible de forger une hypothèse cohérente.").model_dump()
            
        ctx.current_state = RAGState.SYNTHESIZE

    def _handle_vlm_rerank(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[VLM-Reranker] Analyse visuelle des images candidates...").model_dump()
        image_urls = []
        valid_candidates = []
        for c in ctx.candidates:
            url = c.get('image') or c.get('image_url') or c.get('cover_url') or c.get('poster_path')
            if url:
                image_urls.append(url)
                valid_candidates.append(c)
        
        if not image_urls:
            yield StreamStep(type="thought", content="[VLM-Reranker] Aucune image exploitable trouvée pour le reranking.").model_dump()
            ctx.current_state = RAGState.SYNTHESIZE
            return

        try:
            prompt_text, system_prompt = self.prompt_manager.get_prompt(
                "vlm_reranker", 
                query=ctx.query, 
                num_images=len(image_urls)
            )
            reranked = self.inference_engine.visual_rerank(prompt_text, image_urls, system_prompt=system_prompt)
            for item in reranked:
                idx = item.get('index')
                if idx is not None and idx < len(valid_candidates):
                    valid_candidates[idx]['visual_score'] = item.get('score', 0.0)
            valid_candidates.sort(key=lambda x: x.get('visual_score', 0.0), reverse=True)
            top_5 = valid_candidates[:5]
            vlm_context = "\n### VÉRIFICATION VISUELLE (RERANKING) ###\n"
            for i, c in enumerate(top_5):
                vlm_context += f"{i+1}. {c.get('title')} (Score Visuel: {c.get('visual_score', 0.0):.2f})\n"
                vlm_context += f"   - Description: {c.get('description', '')[:300]}...\n"
            ctx.truth_path += f"\n{vlm_context}"
            yield StreamStep(type="thought", content=f"[VLM-Reranker] Classement visuel terminé. Top match : {top_5[0].get('title')}").model_dump()
        except InferenceError as e:
            logger.error(f"VLM Rerank error: {e}")
            yield StreamStep(type="thought", content=f"[VLM-Reranker] Échec de l'analyse visuelle : {str(e)}").model_dump()
        except (InferenceError, InfrastructureError, RuntimeError) as e:
            logger.error(f"Unexpected error in VLM Reranker: {e}")
            yield StreamStep(type="thought", content="[VLM-Reranker] Une erreur inattendue est survenue.").model_dump()
            
        ctx.current_state = RAGState.SYNTHESIZE

    def _handle_synthesize(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        if ctx.correction_feedback:
            yield StreamStep(type="thought", content="[Synthesizer] Tentative d'auto-correction...").model_dump()
        else:
            yield StreamStep(type="thought", content="[Synthesizer] Rédaction de la réponse expert...").model_dump()
        
        ctx.full_answer = ""
        syn_start = time.time()
        in_thought = False
        token_count = 0

        for token in self.synthesizer.synthesize_stream(
            ctx.query, 
            ctx.truth_path, 
            thinking_budget=ctx.thinking_budget, 
            thinking_mode=ctx.thinking_mode,
            correction_feedback=ctx.correction_feedback
        ):
            token_count += 1
            if "<thought>" in token and not in_thought:
                in_thought = True
                parts = token.split("<thought>", 1)
                if parts[0]:
                    ctx.full_answer += parts[0]
                    yield StreamStep(type="token", content=parts[0]).model_dump()
                if parts[1]:
                    yield StreamStep(type="thought", content=parts[1]).model_dump()
                continue
            if "</thought>" in token and in_thought:
                in_thought = False
                parts = token.split("</thought>", 1)
                if parts[0]:
                    yield StreamStep(type="thought", content=parts[0]).model_dump()
                if parts[1]:
                    ctx.full_answer += parts[1]
                    yield StreamStep(type="token", content=parts[1]).model_dump()
                continue
            if in_thought:
                if ctx.thinking_budget > 0 and token_count > ctx.thinking_budget:
                    continue
                yield StreamStep(type="thought", content=token).model_dump()
            else:
                ctx.full_answer += token
                yield StreamStep(type="token", content=token).model_dump()
        
        logger.info(f"PERF: Synthesizer took {(time.time() - syn_start)*1000:.2f}ms")
        
        if not ctx.knowledge_acquired:
            res = self.uncertainty_service.measure_confidence(ctx.query, ctx.full_answer)
            confidence = res.get("confidence_score", 1.0) if isinstance(res, dict) else float(res)
            if confidence < 0.6:
                yield StreamStep(type="thought", content=f"[Uncertainty] Basse confiance détectée ({confidence:.2f}). Déclenchement du Librarian...").model_dump()
                ctx.knowledge_acquired = True
                ctx.current_state = RAGState.ACQUIRE_KNOWLEDGE
                return

        ctx.current_state = RAGState.JUDGE

    def _handle_judge(self, ctx: RAGContext) -> Generator[Dict, None, None]:
        yield StreamStep(type="thought", content="[Swarm] Début du débat multi-agents...").model_dump()
        judge_start = time.time()
        outcome = self.debate_manager.conduct_debate(
            ctx.query, 
            ctx.truth_path, 
            ctx.full_answer,
            thinking_budget=ctx.thinking_budget,
            thinking_mode=ctx.thinking_mode
        )
        ctx.debate_outcome = outcome
        logger.info(f"PERF: Multi-Agent Debate took {(time.time() - judge_start)*1000:.2f}ms")
        yield StreamStep(
            type="thought", 
            content=f"[Swarm] Consensus : {outcome.consensus_action}. Raisonnement : {outcome.final_reasoning}"
        ).model_dump()
        yield StreamStep(type="eval", content=outcome.model_dump()).model_dump()
        
        action = outcome.consensus_action
        if ctx.iteration >= 10 and action == JudgeAction.REWRITE:
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
        
        # Expert injection logic
        expert_injections = self._get_expert_injections(ctx.query)
        results = self.rag_service.hybrid_search(ctx.query, ctx.media_type)
        
        local_ctx_list = [f"- {r.get('title')}: {r.get('description', '')[:2000]}" for r in results]
        if expert_injections:
            fallback_context = "\n".join([f"- Fait de Repli: {f}" for f in expert_injections] + local_ctx_list)
        else:
            fallback_context = "\n".join(local_ctx_list)
        
        yield StreamStep(type="thought", content="[Fallback] Synthèse de la réponse de secours...").model_dump()
        
        prompt = f"Réponds à la question suivante en utilisant UNIQUEMENT le contexte fourni.\nQUESTION: {ctx.query}\nCONTEXTE:\n{fallback_context}"
        system = "Tu es un assistant expert. Sois concis et factuel."
        
        ctx.full_answer = ""
        for token in self.inference_engine.stream_generate(prompt, system):
            ctx.full_answer += token
            yield StreamStep(type="token", content=token).model_dump()
            
        ctx.current_state = RAGState.FINALIZE

    def _get_expert_injections(self, query: str) -> List[str]:
        """Récupère les injections d'experts basées sur les mots-clés de la requête."""
        expert_injections = []
        q_lower = query.lower()

        for rule in self.expert_facts:
            primary_keywords = rule.get('primary_keywords', [])
            secondary_keywords = rule.get('secondary_keywords', [])
            fact = rule.get('fact')

            # Match si l'un des mots-clés primaires est présent
            primary_match = any(pk in q_lower for pk in primary_keywords)
            
            if primary_match:
                # Si des mots-clés secondaires existent, l'un d'eux doit aussi être présent
                if not secondary_keywords or any(sk in q_lower for sk in secondary_keywords):
                    expert_injections.append(fact)

        return expert_injections

    def _execute_search(self, plan, media_type: str) -> tuple[List[Dict], str]:
        # Fetch a larger pool for reranking
        local_results = self.rag_service.hybrid_search(plan.optimized_query, media_type, limit=20)
        
        # --- RERANKING COLBERT (SOTA 2026 / Task 5.2) ---
        if self.colbert_adapter and local_results:
            logger.info(f"🚀 [ColBERT] Reranking {len(local_results)} candidates for query: {plan.optimized_query}")
            local_results = self.colbert_adapter.rank_documents(plan.optimized_query, local_results)[:10]
        else:
            local_results = local_results[:10]

        expert_injections = self._get_expert_injections(plan.optimized_query)
        
        local_ctx_list = [f"DB - {r.get('title')}: {r.get('description', '')[:2000]}" for r in local_results]
        if expert_injections:
            local_ctx = "\n".join([f"DB - Fait de Repli: {f}" for f in expert_injections] + local_ctx_list)
        else:
            local_ctx = "\n".join(local_ctx_list)
        
        if plan.requires_web:
            web_results = self.web_search.search(plan.optimized_query)
            web_ctx = "\n".join([f"WEB - {r['title']}: {r['snippet']}" for r in web_results])
            combined_results = local_results + web_results
            combined_ctx = f"{local_ctx}\n\n{web_ctx}"
            return combined_results, combined_ctx
        
        ctx = local_ctx
        if self.neo4j_manager and plan.entities:
            if plan.graph_traversal_steps:
                traversal = self.neo4j_manager.multi_hop_traversal(plan.entities[0], plan.graph_traversal_steps)
                ctx += f"\nGRAPH_PATH:\n{traversal}"
            else:
                graph_ctx = self.neo4j_manager.get_enriched_context(plan.entities)
                ctx += f"\nGRAPH:\n{graph_ctx}"
        return local_results, ctx

    def handle_fast_rag(self, query: str, media_type: str) -> Generator[Dict, None, None]:
        """Mode RAG Rapide ultra-optimisé."""
        yield StreamStep(type="thought", content="[Fast RAG] Récupération directe des documents pertinents...").model_dump()
        start = time.time()
        results = self.rag_service.hybrid_search(query, media_type)
        local_ctx_list = [f"- {r.get('title')}: {r.get('description', '')[:2000]}" for r in results]
        context_str = "\n".join(local_ctx_list)
        yield StreamStep(type="thought", content=f"[Fast RAG] Recherche terminée en {(time.time() - start)*1000:.2f}ms. Génération de la réponse...").model_dump()
        prompt = f"Réponds à la question suivante de manière concise et factuelle en utilisant le contexte fourni.\nQUESTION: {query}\nCONTEXTE:\n{context_str}"
        system = "Tu es un assistant expert de l'univers anime/manga. Sois extrêmement précis, direct et factuel. Pas de blabla inutile."
        for token in self.inference_engine.stream_generate(prompt, system):
            yield StreamStep(type="token", content=token).model_dump()

from core.domain.entities.ai_schemas import RAGState
import os
from dependency_injector import containers, providers

class LazyClass:
    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name
        self._class = None
    
    def __call__(self, *args, **kwargs):
        if self._class is None:
            import importlib
            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class(*args, **kwargs)

class AgenticContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    inference = providers.DependenciesContainer()

    mlops_adapter_factory = providers.Factory(LazyClass("adapters.mlops_adapter", "MlopsAdapter"))

    llm_service = providers.Singleton(
        LazyClass("core.domain.services.llm_service", "LLMService"),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        usage_port=infrastructure.usage_port,
        slm_engine=inference.compact_reasoning_adapter,
        obs_service=infrastructure.obs_service
    )

    rag_service = providers.Singleton(
        LazyClass("core.domain.services.advanced_rag_service", "AdvancedRAGService"),
        repository=persistence.repository,
        llm_service=llm_service,
        neo4j_manager=persistence.graph_persistence_port,
        colbert_adapter=persistence.colbert_adapter
    )

    graph_expert = providers.Singleton(
        LazyClass("core.domain.services.rag.agents.graph_expert", "GraphExpert"),
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    debate_manager = providers.Singleton(
        LazyClass("core.domain.services.rag.agents.debate_manager", "DebateManager"),
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    librarian = providers.Singleton(
        LazyClass("core.domain.services.rag.agents.librarian", "LibrarianAgent"),
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager,
        web_search=infrastructure.web_search
    )

    forge = providers.Singleton(
        LazyClass("core.domain.services.rag.agents.forge", "ForgeAgent"),
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager,
        neo4j_manager=persistence.graph_persistence_port
    )

    saga_agent = providers.Singleton(
        LazyClass("core.domain.services.rag.agents.saga_agent", "SagaAgent"),
        llm_service=llm_service,
        neo4j_manager=persistence.graph_persistence_port
    )

    chronicler = providers.Singleton(
        LazyClass("core.domain.services.rag.agents.chronicler", "ChroniclerAgent"),
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager,
        neo4j_manager=persistence.graph_persistence_port,
        web_search=infrastructure.web_search
    )

    xai_service = providers.Singleton(
        LazyClass("core.domain.services.xai_service", "XaiDiagnosticService"),
        inference_engine=inference.inference_engine
    )

    planner = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "SearchPlanner"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    critic = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "ResponseCritic"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    synthesizer = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "ResponseSynthesizer"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    judge = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "ResponseJudge"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    scout = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "ScoutAgent"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    semantic_router = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "SemanticRouter"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    retrieval_evaluator = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "RetrievalEvaluator"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    community_partitioner = providers.Singleton(
        LazyClass("pipeline.mlops.graph_community_partitioner", "GraphCommunityPartitioner"), 
        neo4j_manager=persistence.graph_persistence_port, 
        llm_service=llm_service
    )
    
    context_compressor = providers.Singleton(
        LazyClass("core.domain.services.rag.agents", "ContextCompressor"), 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )

    video_rag_service = providers.Singleton(
        LazyClass("core.domain.services.rag.video_rag_service", "VideoRAGService"),
        inference_engine=inference.inference_engine,
        repository=persistence.repository,
        prompt_manager=infrastructure.prompt_manager
    )

    rag_processors = providers.Dict(
        {
            RAGState.PLAN: providers.Singleton(LazyClass("core.domain.services.rag.processors.plan_processor", "PlanProcessor"), planner=planner),
            RAGState.SAGA_LOOKUP: providers.Singleton(LazyClass("core.domain.services.rag.processors.saga_lookup_processor", "SagaLookupProcessor"), saga_agent=saga_agent),
            RAGState.GRAPH_EXPLORE: providers.Singleton(LazyClass("core.domain.services.rag.processors.graph_explore_processor", "GraphExploreProcessor"), community_partitioner=community_partitioner, graph_expert=graph_expert, neo4j_manager=persistence.graph_persistence_port, xai_collector=None),
            RAGState.RESEARCH: providers.Singleton(LazyClass("core.domain.services.rag.processors.research_processor", "ResearchProcessor"), planner=planner, rag_service=rag_service, context_compressor=context_compressor, retrieval_evaluator=retrieval_evaluator, web_search=infrastructure.web_search, video_rag_service=video_rag_service, scout=scout, neo4j_manager=persistence.graph_persistence_port, xai_collector=None),
            RAGState.ACQUIRE_KNOWLEDGE: providers.Singleton(LazyClass("core.domain.services.rag.processors.acquire_knowledge_processor", "AcquireKnowledgeProcessor"), librarian=librarian, xai_collector=None),
            RAGState.SPECULATE: providers.Singleton(LazyClass("core.domain.services.rag.processors.speculate_processor", "SpeculateProcessor"), forge=forge, xai_collector=None),
            RAGState.VLM_RERANK: providers.Singleton(LazyClass("core.domain.services.rag.processors.vlm_rerank_processor", "VlmRerankProcessor"), inference_engine=inference.inference_engine, prompt_manager=infrastructure.prompt_manager, xai_collector=None),
            RAGState.SYNTHESIZE: providers.Singleton(LazyClass("core.domain.services.rag.processors.synthesize_processor", "SynthesizeProcessor"), synthesizer=synthesizer, xai_service=xai_service, rag_service=rag_service),
            RAGState.JUDGE: providers.Singleton(LazyClass("core.domain.services.rag.processors.judge_processor", "JudgeProcessor"), debate_manager=debate_manager, xai_collector=None),
            RAGState.FALLBACK_RAG: providers.Singleton(LazyClass("core.domain.services.rag.processors.fallback_rag_processor", "FallbackRagProcessor"), rag_service=rag_service, inference_engine=inference.inference_engine, expert_facts=[]),
        }
    )

    rag_orchestrator = providers.Singleton(
        LazyClass("core.domain.services.rag_orchestrator", "RAGOrchestrator"),
        processors=rag_processors
    )

    memory_service = providers.Singleton(
        LazyClass("core.domain.services.long_term_memory_service", "LongTermMemoryService"),
        chroma_resource=persistence.repository,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    semantic_cache_service = providers.Singleton(
        LazyClass("core.domain.services.semantic_cache_service", "SemanticCacheService"),
        inference_engine=inference.inference_engine,
        cache_port=persistence.semantic_cache_adapter
    )

    agentic_rag = providers.Singleton(
        LazyClass("core.domain.services.agentic_rag_service", "AgenticRAGService"),
        inference_engine=inference.inference_engine,
        rag_service=rag_service,
        web_search=infrastructure.web_search,
        prompt_manager=infrastructure.prompt_manager,
        llm_service=llm_service,
        workflow_orchestrator=rag_orchestrator,
        neo4j_manager=persistence.graph_persistence_port,
        memory_service=memory_service,
        semantic_cache=semantic_cache_service,
        obs_service=infrastructure.obs_service,
        xai_service=xai_service,
        semantic_router=semantic_router
    )

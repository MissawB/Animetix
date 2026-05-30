import os
from dependency_injector import containers, providers

from core.domain.services.llm_service import LLMService
from core.domain.services.advanced_rag_service import AdvancedRAGService
from core.domain.services.quantum_cognitive_model import QuantumCognitivePreferenceModel
from core.domain.services.synaptic_plasticity import SynapticPlasticitySimulator
from core.domain.services.rag.agents.debate_manager import DebateManager
from core.domain.services.rag.agents.librarian import LibrarianAgent
from core.domain.services.rag.agents.forge import ForgeAgent
from core.domain.services.rag.agents.saga_agent import SagaAgent
from core.domain.services.rag.agents.chronicler import ChroniclerAgent
from core.domain.services.rag.agents.graph_expert import GraphExpert
from core.domain.services.rag.video_rag_service import VideoRAGService
from core.domain.services.rag.agents import (
    SearchPlanner, ResponseCritic, ResponseSynthesizer, 
    ResponseJudge, ScoutAgent, SemanticRouter, 
    RetrievalEvaluator, ContextCompressor
)
from core.domain.services.rag_workflow_manager import RAGWorkflowManager
from core.domain.services.agentic_rag_service import AgenticRAGService
from pipeline.mlops.graph_community_partitioner import GraphCommunityPartitioner
from core.domain.services.long_term_memory_service import LongTermMemoryService
from core.domain.services.semantic_cache_service import SemanticCacheService
from core.domain.services.xai_service import XaiDiagnosticService, UncertaintyService
from adapters.mlops_adapter import MlopsAdapter

class AgenticContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    inference = providers.DependenciesContainer()

    mlops_adapter_factory = providers.Factory(MlopsAdapter)

    llm_service = providers.Singleton(
        LLMService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        usage_port=infrastructure.usage_port,
        slm_engine=inference.inference_engine,
        obs_service=infrastructure.obs_service
    )

    rag_service = providers.Singleton(
        AdvancedRAGService,
        repository=persistence.repository,
        llm_service=llm_service,
        neo4j_manager=persistence.graph_persistence_port,
        colbert_adapter=persistence.colbert_adapter
    )

    graph_expert = providers.Singleton(
        GraphExpert,
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    debate_manager = providers.Singleton(
        DebateManager,
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    librarian = providers.Singleton(
        LibrarianAgent,
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager,
        web_search=infrastructure.web_search
    )

    forge = providers.Singleton(
        ForgeAgent,
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager,
        neo4j_manager=persistence.graph_persistence_port
    )

    saga_agent = providers.Singleton(
        SagaAgent,
        llm_service=llm_service,
        neo4j_manager=persistence.graph_persistence_port
    )

    chronicler = providers.Singleton(
        ChroniclerAgent,
        llm_service=llm_service,
        prompt_manager=infrastructure.prompt_manager,
        neo4j_manager=persistence.graph_persistence_port,
        web_search=infrastructure.web_search
    )

    uncertainty_service = providers.Singleton(
        UncertaintyService,
        inference_engine=inference.inference_engine
    )

    xai_diagnostic_service = providers.Singleton(
        XaiDiagnosticService,
        inference_engine=inference.inference_engine
    )

    planner = providers.Singleton(
        SearchPlanner, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    critic = providers.Singleton(
        ResponseCritic, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    synthesizer = providers.Singleton(
        ResponseSynthesizer, 
        inference_engine=inference.inference_engine, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    judge = providers.Singleton(
        ResponseJudge, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    scout = providers.Singleton(
        ScoutAgent, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    semantic_router = providers.Singleton(
        SemanticRouter, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    retrieval_evaluator = providers.Singleton(
        RetrievalEvaluator, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )
    
    community_partitioner = providers.Singleton(
        GraphCommunityPartitioner, 
        neo4j_manager=persistence.graph_persistence_port, 
        llm_service=llm_service
    )
    
    context_compressor = providers.Singleton(
        ContextCompressor, 
        llm_service=llm_service, 
        prompt_manager=infrastructure.prompt_manager
    )

    video_rag_service = providers.Singleton(
        VideoRAGService,
        inference_engine=inference.inference_engine,
        repository=persistence.repository,
        prompt_manager=infrastructure.prompt_manager
    )

    rag_workflow_manager = providers.Singleton(
        RAGWorkflowManager,
        planner=planner,
        critic=critic,
        synthesizer=synthesizer,
        judge=judge,
        scout=scout,
        semantic_router=semantic_router,
        retrieval_evaluator=retrieval_evaluator,
        community_partitioner=community_partitioner,
        graph_expert=graph_expert,
        debate_manager=debate_manager,
        librarian=librarian,
        forge=forge,
        saga_agent=saga_agent,
        chronicler=chronicler,
        uncertainty_service=uncertainty_service,
        inference_engine=inference.inference_engine,
        web_search=infrastructure.web_search,
        prompt_manager=infrastructure.prompt_manager,
        rag_service=rag_service,
        neo4j_manager=persistence.graph_persistence_port,
        context_compressor=context_compressor,
        mlops_port=mlops_adapter_factory,
        colbert_adapter=persistence.colbert_adapter,
        video_rag_service=video_rag_service
    )

    memory_service = providers.Singleton(
        LongTermMemoryService,
        chroma_resource=persistence.repository,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    semantic_cache_service = providers.Singleton(
        SemanticCacheService,
        inference_engine=inference.inference_engine,
        cache_port=persistence.semantic_cache_adapter
    )

    agentic_rag = providers.Singleton(
        AgenticRAGService,
        inference_engine=inference.inference_engine,
        rag_service=rag_service,
        web_search=infrastructure.web_search,
        prompt_manager=infrastructure.prompt_manager,
        llm_service=llm_service,
        workflow_manager=rag_workflow_manager,
        neo4j_manager=persistence.graph_persistence_port,
        memory_service=memory_service,
        semantic_cache=semantic_cache_service,
        obs_service=infrastructure.obs_service,
        uncertainty_service=uncertainty_service,
        semantic_router=semantic_router
    )

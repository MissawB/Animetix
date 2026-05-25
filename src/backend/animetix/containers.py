import os
import logging
from django.conf import settings
from dependency_injector import containers, providers

# --- CORE SERVICES ---
from core.domain.services.prompt_manager import PromptManager
from core.domain.services.translation_service import TranslationService
from core.domain.services.game_service import GameService
from core.domain.services.catalog_service import CatalogService
from core.domain.services.similarity_service import SimilarityService
from core.domain.services.undercover_service import UndercoverService
from core.domain.services.llm_service import LLMService
from core.domain.services.advanced_rag_service import AdvancedRAGService
from core.domain.services.advanced_vision_service import AdvancedVisionService
from core.domain.services.graph_construction_service import KnowledgeGraphConstructionService
from core.domain.services.reasoning_agent_service import ReasoningAgentService
from core.domain.services.media_sync_service import MediaSyncService
from core.domain.services.achievement_service import AchievementDomainService, GameEventListener
from core.domain.services.vision_quest_service import VisionQuestDomainService
from core.domain.services.emoji_service import EmojiDomainService
from core.domain.services.paradox_service import ParadoxDomainService
from core.domain.services.animinator_service import AniminatorDomainService
from core.domain.services.akinetix_service import AkinetixDomainService
from core.domain.services.akinetix_engine import AkinetixEngine
from core.domain.services.akinetix_rl_service import AkinetixRLDomainService
from core.domain.services.blind_test_service import BlindTestDomainService
from core.domain.services.cover_test_service import CoverTestDomainService
from core.domain.services.creative.video_quest import VideoQuestService
from core.domain.services.creative.studio_transform import StudioTransformService
from core.domain.services.creative.manga_flow import MangaFlowService
from core.domain.services.creative.soundscape import SoundscapeGenerationService
from core.domain.services.guardrail_service import GuardrailService, RedTeamingAgent
from core.domain.services.akinetix_rl_env import AkinetixRLService
from core.domain.services.self_play_debate_service import SelfPlayDebateService
from core.domain.services.ragas_eval_service import RagasEvalService
from core.domain.services.orchestrator_agent_service import OrchestratorAgentService
from core.domain.services.cross_modal_service import CrossModalSearchService, VlmIndexingService
from core.domain.services.xai_service import XaiDiagnosticService, UncertaintyService
from core.domain.services.multi_agent_bus import MultiAgentBus
from core.domain.services.neuro_symbolic_service import NeuroSymbolicService
from core.domain.services.spatial_computing_service import SpatialComputingService
from core.domain.services.spatial_audio_service import VoiceCloningService, NativeSpeechLLMService
from core.domain.services.cove_oracle_service import CoveOracleService
from core.domain.services.rag.agents.debate_manager import DebateManager
from core.domain.services.rag.agents.librarian import LibrarianAgent
from core.domain.services.rag.agents.forge import ForgeAgent
from core.domain.services.rag.agents.saga_agent import SagaAgent
from core.domain.services.rag.agents.chronicler import ChroniclerAgent
from core.domain.services.rag.agents.graph_expert import GraphExpert
from core.domain.services.rag.agents import SearchPlanner, ResponseCritic, ResponseSynthesizer, ResponseJudge, ScoutAgent, SemanticRouter, RetrievalEvaluator, ContextCompressor
from core.domain.services.rag_workflow_manager import RAGWorkflowManager
from core.domain.services.agentic_rag_service import AgenticRAGService
from pipeline.mlops.graph_community_partitioner import GraphCommunityPartitioner
from core.domain.services.long_term_memory_service import LongTermMemoryService
from core.domain.services.semantic_cache_service import SemanticCacheService
from core.domain.services.star_reasoner_service import StarReasonerService
from core.domain.services.star_mlops_service import StarMLOpsDomainService
from core.domain.services.drift_service import DriftService
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop
from core.domain.services.creative.fusion_service import FusionDomainService
from core.domain.services.creative.vs_battle_service import VsBattleService
from core.domain.services.observability_service import ObservabilityService
from core.domain.services.health_dashboard_service import HealthDashboardService
from core.domain.services.game_session_service import GameSessionService
from core.domain.services.pricing_service import PricingService

# Adapters
from adapters.persistence.session_state_adapter import DjangoSessionStateAdapter
from adapters.persistence.unified_repository_adapter import UnifiedRepositoryAdapter
from adapters.persistence.django_usage_adapter import DjangoUsageAdapter
from adapters.persistence.pipeline_sync_adapter import PipelineSyncAdapter
from adapters.persistence.django_achievement_adapter import DjangoAchievementAdapter
from adapters.persistence.django_donation_adapter import DjangoDonationAdapter
from adapters.persistence.web_search_adapter import DuckDuckGoSearchAdapter
from adapters.persistence.fandom_adapter import FandomAdapter
from adapters.persistence.django_semantic_cache_adapter import DjangoSemanticCacheAdapter
from adapters.persistence.django_feedback_adapter import DjangoFeedbackAdapter
from adapters.persistence.django_eval_adapter import DjangoEvalAdapter
from adapters.persistence.django_gold_dataset_adapter import DjangoGoldDatasetAdapter
from adapters.persistence.neo4j_graph_adapter import Neo4jGraphAdapter

from adapters.mlops_adapter import MlopsAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter
from adapters.inference.vllm_adapter import VllmAdapter
from adapters.inference.local_llama_adapter import LocalLlamaAdapter
from adapters.inference.gguf_adapter import GgufAdapter
from adapters.inference.transformers_adapter import TransformersAdapter
from adapters.inference.moondream_adapter import MoondreamAdapter
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.xtts_adapter import XTTSAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter

# Clients
logger = logging.getLogger('animetix')

class Container(containers.DeclarativeContainer):
    """Dependency Injection Container using dependency-injector framework."""
    
    config = providers.Configuration()

    # --- Infrastructure Providers ---

    session_state_adapter_factory = providers.Factory(
        DjangoSessionStateAdapter
    )

    prompt_manager = providers.Singleton(
        PromptManager,
        prompts_dir=os.path.join(settings.PROJECT_ROOT, "src", "core", "domain", "services", "prompts")
    )

    translation_service = providers.Singleton(TranslationService)

    repository = providers.Singleton(
        UnifiedRepositoryAdapter,
        chroma_db_path=settings.CHROMA_DB_PATH,
        project_root=settings.PROJECT_ROOT
    )

    django_repository = providers.Callable(
        lambda repo: repo.django,
        repository
    )

    mlops_adapter_factory = providers.Factory(MlopsAdapter)

    obs_service = providers.Singleton(
        ObservabilityService,
        project_name="animetix-production"
    )

    # --- Persistence Adapters ---

    pricing_service = providers.Singleton(PricingService)
    usage_port = providers.Factory(DjangoUsageAdapter, pricing_service=pricing_service)

    semantic_cache_adapter = providers.Singleton(DjangoSemanticCacheAdapter)
    feedback_adapter = providers.Singleton(DjangoFeedbackAdapter)
    eval_adapter = providers.Singleton(DjangoEvalAdapter)
    gold_dataset_adapter = providers.Singleton(DjangoGoldDatasetAdapter)
    graph_persistence_port = providers.Singleton(Neo4jGraphAdapter)

    # --- Inference Adapters ---

    gguf_adapter = providers.Singleton(
        GgufAdapter,
        model_path=os.path.join(settings.MODELS_DIR, "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"),
        clip_model_path=os.path.join(settings.MODELS_DIR, "llava-v1.5-7b-mmproj-Q4_0.gguf")
    )

    moondream_adapter = providers.Singleton(MoondreamAdapter)

    transformers_adapter = providers.Singleton(
        TransformersAdapter,
        model_id="Qwen/Qwen2.5-1.5B-Instruct",
        use_4bit=True
    )

    diffusers_adapter = providers.Singleton(
        DiffusersAdapter,
        model_id="stabilityai/sdxl-turbo",
        use_fp16=True,
        usage_port=usage_port
    )

    xtts_adapter = providers.Singleton(
        XTTSAdapter,
        usage_port=usage_port
    )

    unified_inference_adapter = providers.Singleton(
        UnifiedInferenceAdapter,
        api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        model_name=os.getenv("LLM_MODEL_NAME", "llama3")
    )

    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            unified_inference_adapter,
            transformers_adapter,
            diffusers_adapter,
            xtts_adapter,
            providers.Factory(
                VllmAdapter,
                api_base=os.getenv("VLLM_API_BASE", "http://vllm:8000/v1"),
                model_name="meta-llama/Llama-3-8B-Instruct"
            ),
            gguf_adapter,
            providers.Factory(
                BrainAPIAdapter,
                brain_api_url=os.getenv("BRAIN_API_URL", "")
            )
        ),
        obs_service=obs_service
    )

    # --- Domain Services ---

    llm_service = providers.Singleton(
        LLMService,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager,
        usage_port=usage_port,
        slm_engine=inference_engine,
        obs_service=obs_service
    )

    agent_bus = providers.Singleton(
        MultiAgentBus,
        redis_url=os.getenv("REDIS_URL")
    )

    web_search = providers.Singleton(DuckDuckGoSearchAdapter)
    fandom_adapter = providers.Singleton(FandomAdapter)

    rag_service = providers.Singleton(
        AdvancedRAGService,
        repository=repository,
        llm_service=llm_service,
        neo4j_manager=graph_persistence_port
    )

    graph_expert = providers.Singleton(
        GraphExpert,
        llm_service=llm_service,
        prompt_manager=prompt_manager
    )

    debate_manager = providers.Singleton(
        DebateManager,
        llm_service=llm_service,
        prompt_manager=prompt_manager
    )

    librarian = providers.Singleton(
        LibrarianAgent,
        llm_service=llm_service,
        prompt_manager=prompt_manager,
        web_search=web_search
    )

    forge = providers.Singleton(
        ForgeAgent,
        llm_service=llm_service,
        prompt_manager=prompt_manager,
        neo4j_manager=graph_persistence_port
    )

    saga_agent = providers.Singleton(
        SagaAgent,
        llm_service=llm_service,
        neo4j_manager=graph_persistence_port
    )

    chronicler = providers.Singleton(
        ChroniclerAgent,
        llm_service=llm_service,
        prompt_manager=prompt_manager,
        neo4j_manager=graph_persistence_port,
        web_search=web_search
    )

    uncertainty_service = providers.Singleton(
        UncertaintyService,
        inference_engine=inference_engine
    )

    planner = providers.Singleton(SearchPlanner, llm_service=llm_service, prompt_manager=prompt_manager)
    critic = providers.Singleton(ResponseCritic, llm_service=llm_service, prompt_manager=prompt_manager)
    synthesizer = providers.Singleton(ResponseSynthesizer, inference_engine=inference_engine, prompt_manager=prompt_manager)
    judge = providers.Singleton(ResponseJudge, llm_service=llm_service, prompt_manager=prompt_manager)
    scout = providers.Singleton(ScoutAgent, llm_service=llm_service, prompt_manager=prompt_manager)
    semantic_router = providers.Singleton(SemanticRouter, llm_service=llm_service, prompt_manager=prompt_manager)
    retrieval_evaluator = providers.Singleton(RetrievalEvaluator, llm_service=llm_service, prompt_manager=prompt_manager)
    community_partitioner = providers.Singleton(GraphCommunityPartitioner, neo4j_manager=graph_persistence_port, llm_service=llm_service)
    context_compressor = providers.Singleton(ContextCompressor, llm_service=llm_service, prompt_manager=prompt_manager)

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
        inference_engine=inference_engine,
        web_search=web_search,
        prompt_manager=prompt_manager,
        rag_service=rag_service,
        neo4j_manager=graph_persistence_port,
        context_compressor=context_compressor,
        mlops_port=mlops_adapter_factory
    )

    memory_service = providers.Singleton(
        LongTermMemoryService,
        chroma_resource=repository,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager
    )

    semantic_cache_service = providers.Singleton(
        SemanticCacheService,
        inference_engine=inference_engine,
        cache_port=semantic_cache_adapter
    )

    agentic_rag = providers.Singleton(
        AgenticRAGService,
        inference_engine=inference_engine,
        rag_service=rag_service,
        web_search=web_search,
        prompt_manager=prompt_manager,
        llm_service=llm_service,
        workflow_manager=rag_workflow_manager,
        neo4j_manager=graph_persistence_port,
        memory_service=memory_service,
        semantic_cache=semantic_cache_service,
        obs_service=obs_service,
        uncertainty_service=uncertainty_service,
        semantic_router=semantic_router
    )

    reasoning_agent = providers.Singleton(
        ReasoningAgentService,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager,
        search_service=rag_service,
        graph_manager=graph_persistence_port,
        agent_bus=agent_bus
    )

    sync_service = providers.Singleton(
        MediaSyncService,
        sync_adapter=providers.Factory(
            PipelineSyncAdapter,
            brain_api_url=os.getenv("BRAIN_API_URL", "")
        ),
        repository=repository
    )

    vision_service = providers.Singleton(
        AdvancedVisionService,
        inference_engine=inference_engine
    )

    graph_builder = providers.Singleton(
        KnowledgeGraphConstructionService,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager
    )

    vision_quest_service = providers.Singleton(
        VisionQuestDomainService,
        inference_engine=moondream_adapter,
        vision_service=vision_service
    )

    emoji_service = providers.Singleton(
        EmojiDomainService,
        llm_service=llm_service
    )

    neuro_symbolic_service = providers.Singleton(
        NeuroSymbolicService,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager
    )

    paradox_service = providers.Singleton(
        ParadoxDomainService,
        llm_service=llm_service,
        neuro_symbolic_service=neuro_symbolic_service
    )

    animinator_service = providers.Singleton(
        AniminatorDomainService,
        llm_service=llm_service
    )

    blind_test_service = providers.Singleton(
        BlindTestDomainService,
        repository=repository
    )

    cover_test_service = providers.Singleton(
        CoverTestDomainService,
        repository=repository
    )

    achievement_service = providers.Singleton(
        AchievementDomainService,
        port=providers.Factory(DjangoAchievementAdapter)
    )

    achievement_listener = providers.Singleton(
        GameEventListener,
        achievement_service=achievement_service
    )

    catalog_service = providers.Singleton(
        CatalogService,
        repository=repository,
        sql_repository=django_repository,
        cache_service=providers.Object(__import__('django.core.cache').core.cache)
    )

    akinetix_engine = providers.Singleton(
        AkinetixEngine,
        catalog_service=catalog_service
    )

    akinetix_service = providers.Singleton(
        AkinetixDomainService,
        catalog_service=catalog_service,
        engine=akinetix_engine
    )

    akinetix_expert_service = providers.Singleton(
        AkinetixRLDomainService,
        catalog_service=catalog_service
    )

    game_service = providers.Singleton(
        GameService,
        repository=repository,
        catalog_service=catalog_service,
        similarity_service=providers.Factory(SimilarityService, repository=repository),
        undercover_service=providers.Factory(
            UndercoverService,
            catalog_service=catalog_service,
            similarity_service=providers.Factory(SimilarityService, repository=repository)
        )
    )

    video_quest_service = providers.Singleton(
        VideoQuestService,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager
    )

    studio_transform_service = providers.Singleton(
        StudioTransformService,
        inference_engine=diffusers_adapter
    )

    manga_flow_service = providers.Singleton(
        MangaFlowService,
        inference_engine=inference_engine
    )

    soundscape_service = providers.Singleton(
        SoundscapeGenerationService,
        inference_engine=inference_engine
    )

    guardrail_service = providers.Singleton(
        GuardrailService,
        inference_engine=inference_engine
    )

    akinetix_rl_env_service = providers.Singleton(
        AkinetixRLService,
        catalog_service=catalog_service
    )

    self_play_debate_service = providers.Singleton(
        SelfPlayDebateService,
        llm_service=llm_service
    )

    ragas_eval_service = providers.Singleton(
        RagasEvalService,
        judge_engine=inference_engine,
        eval_port=eval_adapter,
        gold_port=gold_dataset_adapter
    )

    orchestrator_agent_service = providers.Singleton(
        OrchestratorAgentService,
        llm_service=llm_service,
        prompt_manager=prompt_manager
    )

    cross_modal_search_service = providers.Singleton(
        CrossModalSearchService,
        repository=repository
    )

    vlm_indexing_service = providers.Singleton(
        VlmIndexingService,
        vision_service=vision_service,
        repository=repository
    )

    xai_diagnostic_service = providers.Singleton(
        XaiDiagnosticService,
        inference_engine=inference_engine
    )


    spatial_computing_service = providers.Singleton(
        SpatialComputingService,
        vision_service=vision_service
    )

    voice_cloning_service = providers.Singleton(
        VoiceCloningService,
        xtts_engine=xtts_adapter
    )

    native_speech_llm_service = providers.Singleton(
        NativeSpeechLLMService,
        inference_engine=inference_engine
    )

    cove_oracle_service = providers.Singleton(
        CoveOracleService,
        llm_service=llm_service,
        prompt_manager=prompt_manager
    )

    star_reasoner_service = providers.Singleton(
        StarReasonerService,
        llm_service=llm_service,
        prompt_manager=prompt_manager
    )

    star_mlops_service = providers.Singleton(
        StarMLOpsDomainService,
        eval_service=ragas_eval_service
    )

    drift_service = providers.Singleton(
        DriftService,
        repository=repository
    )

    dpo_feedback_loop = providers.Singleton(
        DPOFeedbackLoop,
        prompt_manager=prompt_manager,
        feedback_port=feedback_adapter,
        llm_service=llm_service
    )

    fusion_service = providers.Singleton(
        FusionDomainService,
        llm_service=llm_service
    )

    vs_battle_service = providers.Singleton(
        VsBattleService,
        fandom_port=fandom_adapter,
        inference_engine=inference_engine,
        prompt_manager=prompt_manager,
        web_search_port=web_search
    )

    health_dashboard_service = providers.Singleton(
        HealthDashboardService,
        donation_port=providers.Factory(DjangoDonationAdapter),
        usage_port=usage_port
    )

    game_session_service_factory = providers.Factory(
        GameSessionService
    )

# Instantiate the container
container = Container()

def get_container():
    return container

import os
from dependency_injector import containers, providers

# Services imports
from core.domain.services.game_service import GameService
from core.domain.services.catalog_service import CatalogService
from core.domain.services.similarity_service import SimilarityService
from core.domain.services.undercover_service import UndercoverService
from core.domain.services.advanced_vision_service import AdvancedVisionService
from core.domain.services.graph_construction_service import KnowledgeGraphConstructionService
from core.domain.services.graph_healer_service import GraphHealerService
from core.domain.services.reasoning_agent_service import ReasoningAgentService
from core.domain.services.media_sync_service import MediaSyncService
from core.domain.services.achievement_service import AchievementDomainService, GameEventListener
from core.domain.services.vision_quest_service import VisionQuestDomainService
from core.domain.services.emoji_service import EmojiDomainService
from core.domain.services.paradox_service import ParadoxDomainService
from core.domain.services.animinator_service import AniminatorDomainService
from core.domain.services.companion_service import CompanionService
from core.domain.services.akinetix_service import AkinetixService
from core.domain.services.akinetix_engine import AkinetixEngine
from core.domain.services.akinetix_rl_service import AkinetixRLService
from core.domain.services.blind_test_service import BlindTestDomainService
from core.domain.services.cover_test_service import CoverTestDomainService
from core.domain.services.creative.video_quest import VideoQuestService
from core.domain.services.rag.video_rag_service import VideoRAGService
from core.domain.services.creative.studio_transform import StudioTransformService
from core.domain.services.creative.manga_flow import MangaFlowService
from core.domain.services.creative.soundscape import SoundscapeGenerationService
from core.domain.services.creative.visual_novel_service import VisualNovelService
from core.domain.services.guardrail_service import GuardrailService, RedTeamingAgent
from core.domain.services.self_play_debate_service import SelfPlayDebateService
from core.domain.services.ragas_eval_service import RagasEvalService
from core.domain.services.orchestrator_agent_service import OrchestratorAgentService
from core.domain.services.cross_modal_service import CrossModalSearchService, VlmIndexingService
from core.domain.services.neuro_symbolic_service import NeuroSymbolicService
from core.domain.services.spatial_computing_service import SpatialComputingService
from core.domain.services.static_diorama_3d_service import StaticDiorama3DService
from core.domain.services.cinematic_volumetric_reconstruction_service import CinematicVolumetricReconstructionService
from core.domain.services.spatial_audio_service import VoiceCloningService, NativeSpeechLLMService
from core.domain.services.cove_oracle_service import CoveOracleService
from core.domain.services.star_reasoner_service import StarReasonerService
from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService
from core.domain.services.episodic_memory_compressor import EpisodicMemoryCompressor
from core.domain.services.neuro_symbolic_user_profiler import NeuroSymbolicUserProfiler
from core.domain.services.dspy_prompt_optimizer import DSPyPromptOptimizer
from core.domain.services.cfr_game_solver import CFRGameSolver
from core.domain.services.neuromorphic_lnn_service import LiquidNeuralNetworkService
from core.domain.services.quantum_cognitive_service import QuantumCognitiveService
from core.domain.services.swarm_consensus import SwarmConsensusOrchestrator
from core.domain.services.counterfactual_simulator import CounterfactualConversationSimulator
from core.domain.services.self_evolving_compiler import SelfEvolvingCompiler
from core.domain.services.neuromorphic_plasticity_service import SynapticPlasticityService
from core.domain.services.domain_synthesizer import AutonomousDomainSynthesizer
from core.domain.services.distillation_pipeline import ModelDistillationPipeline
from core.domain.services.synthetic_promotion_service import SyntheticDataPromotionService
from core.domain.services.star_mlops_service import StarMLOpsDomainService
from core.domain.services.drift_service import DriftService
from core.domain.services.archetype_drift_service import ArchetypeDriftService
from core.domain.services.alert_service import AlertService
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop
from core.domain.services.creative.fusion_service import FusionDomainService
from core.domain.services.creative.vs_battle_service import VsBattleService
from core.domain.services.health_dashboard_service import HealthDashboardService
from core.domain.services.sota_benchmark_service import SOTABenchmarkService
from core.domain.services.game_session_service import GameSessionService
from core.domain.services.xai_service import XaiDiagnosticService
from core.domain.services.hierarchical_graph_rag import HierarchicalGraphRAGService
from core.domain.services.complexity_analyser import ComplexityAnalyser
from core.domain.services.video_language_indexing_service import VideoLanguageIndexingService

# Adapters imports
from adapters.persistence.pipeline_sync_adapter import PipelineSyncAdapter
from adapters.persistence.django_achievement_adapter import DjangoAchievementAdapter
from adapters.infrastructure.django_notification_adapter import DjangoNotificationAdapter

class CoreServicesContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    inference = providers.DependenciesContainer()
    agentic = providers.DependenciesContainer()

    reasoning_agent = providers.Singleton(
        ReasoningAgentService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        search_service=agentic.rag_service,
        graph_manager=persistence.graph_persistence_port,
        agent_bus=providers.Singleton(
            __import__('core.domain.services.multi_agent_bus', fromlist=['MultiAgentBus']).MultiAgentBus,
            redis_url=os.getenv("REDIS_URL")
        )
    )

    sync_service = providers.Singleton(
        MediaSyncService,
        sync_adapter=providers.Factory(
            PipelineSyncAdapter,
            brain_api_url=os.getenv("BRAIN_API_URL", "")
        ),
        repository=persistence.repository
    )

    vision_service = providers.Singleton(
        AdvancedVisionService,
        inference_engine=inference.inference_engine
    )

    graph_builder = providers.Singleton(
        KnowledgeGraphConstructionService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    graph_healer_service = providers.Singleton(
        GraphHealerService,
        neo4j_manager=persistence.graph_persistence_port,
        construction_service=graph_builder,
        repository=persistence.repository,
        inference_engine=inference.inference_engine
    )

    vision_quest_service = providers.Singleton(
        VisionQuestDomainService,
        inference_engine=inference.vision_transformers_adapter,
        vision_service=vision_service
    )

    emoji_service = providers.Singleton(
        EmojiDomainService,
        llm_service=agentic.llm_service
    )

    neuro_symbolic_service = providers.Singleton(
        NeuroSymbolicService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    paradox_service = providers.Singleton(
        ParadoxDomainService,
        llm_service=agentic.llm_service,
        neuro_symbolic_service=neuro_symbolic_service
    )

    animinator_service = providers.Singleton(
        AniminatorDomainService,
        llm_service=agentic.llm_service
    )

    companion_service = providers.Singleton(
        CompanionService,
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    blind_test_service = providers.Singleton(
        BlindTestDomainService,
        repository=persistence.repository
    )

    cover_test_service = providers.Singleton(
        CoverTestDomainService,
        repository=persistence.repository
    )

    achievement_service = providers.Singleton(
        AchievementDomainService,
        port=providers.Factory(DjangoAchievementAdapter),
        notification_port=infrastructure.notification_port
    )

    achievement_listener = providers.Singleton(
        GameEventListener,
        achievement_service=achievement_service
    )

    catalog_service = providers.Singleton(
        CatalogService,
        repository=persistence.repository,
        sql_repository=persistence.django_repository,
        cache_service=providers.Object(__import__('django.core.cache', fromlist=['cache']).cache)
    )

    similarity_service = providers.Singleton(
        SimilarityService,
        repository=persistence.repository
    )

    cfr_game_solver = providers.Singleton(
        CFRGameSolver,
        num_actions=4
    )

    akinetix_engine = providers.Singleton(
        AkinetixEngine,
        catalog_service=catalog_service,
        cfr_solver=cfr_game_solver
    )

    akinetix_service = providers.Singleton(
        AkinetixService,
        catalog_service=catalog_service,
        engine=akinetix_engine
    )

    akinetix_expert_service = providers.Singleton(
        AkinetixRLService,
        catalog_service=catalog_service
    )

    game_service = providers.Singleton(
        GameService,
        repository=persistence.repository,
        catalog_service=catalog_service,
        similarity_service=providers.Factory(SimilarityService, repository=persistence.repository),
        undercover_service=providers.Factory(
            UndercoverService,
            catalog_service=catalog_service,
            similarity_service=providers.Factory(SimilarityService, repository=persistence.repository)
        )
    )

    game_session_service_factory = providers.Factory(
        GameSessionService
    )

    video_quest_service = providers.Singleton(
        VideoQuestService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    visual_novel_service = providers.Singleton(
        VisualNovelService,
        llm_service=agentic.llm_service,
        repository=persistence.repository
    )

    studio_transform_service = providers.Singleton(
        StudioTransformService,
        inference_engine=inference.diffusers_adapter,
        prompt_manager=infrastructure.prompt_manager
    )

    manga_flow_service = providers.Singleton(
        MangaFlowService,
        inference_engine=inference.inference_engine,
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    soundscape_service = providers.Singleton(
        SoundscapeGenerationService,
        inference_engine=inference.inference_engine,
        video_service=video_quest_service,
        prompt_manager=infrastructure.prompt_manager
    )

    guardrail_service = providers.Singleton(
        GuardrailService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        neo4j_manager=persistence.graph_persistence_port,
        safety_engine=inference.local_guardrail_adapter
    )

    red_teaming_agent = providers.Singleton(
        RedTeamingAgent,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    akinetix_rl_env_service = providers.Singleton(
        AkinetixRLService,
        catalog_service=catalog_service
    )

    self_play_debate_service = providers.Singleton(
        SelfPlayDebateService,
        llm_service=agentic.llm_service
    )

    ragas_eval_service = providers.Singleton(
        RagasEvalService,
        judge_engine=inference.inference_engine,
        eval_port=persistence.eval_adapter,
        gold_port=persistence.gold_dataset_adapter
    )

    orchestrator_agent_service = providers.Singleton(
        OrchestratorAgentService,
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    cross_modal_search_service = providers.Singleton(
        CrossModalSearchService,
        repository=persistence.repository
    )

    vlm_indexing_service = providers.Singleton(
        VlmIndexingService,
        vision_service=vision_service,
        repository=persistence.repository
    )


    spatial_computing_service = providers.Singleton(
        SpatialComputingService,
        vision_service=vision_service
    )

    static_diorama_3d_service = providers.Singleton(
        StaticDiorama3DService,
        vision_service=vision_service
    )

    cinematic_volumetric_reconstruction_service = providers.Singleton(
        CinematicVolumetricReconstructionService,
        vision_service=vision_service
    )


    liquid_neural_network = providers.Singleton(
        LiquidNeuralNetworkService,
        state_dimension=4,
        input_dimension=2
    )

    voice_cloning_service = providers.Singleton(
        VoiceCloningService,
        inference_engine=inference.inference_engine,
        lnn_simulator=liquid_neural_network
    )

    native_speech_llm_service = providers.Singleton(
        NativeSpeechLLMService,
        inference_engine=inference.inference_engine
    )

    cove_oracle_service = providers.Singleton(
        CoveOracleService,
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager
    )

    star_reasoner_service = providers.Singleton(
        StarReasonerService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        gold_dataset_port=persistence.gold_dataset_adapter
    )

    tree_of_thoughts_service = providers.Singleton(
        TreeOfThoughtsSearchService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager
    )

    episodic_memory_compressor = providers.Singleton(
        EpisodicMemoryCompressor,
        chroma_resource=persistence.repository,
        inference_engine=inference.inference_engine,
        neo4j_manager=persistence.graph_persistence_port
    )

    neuro_symbolic_user_profiler = providers.Singleton(
        NeuroSymbolicUserProfiler,
        feedback_adapter=persistence.feedback_adapter
    )

    dspy_prompt_optimizer = providers.Singleton(
        DSPyPromptOptimizer,
        inference_engine=inference.inference_engine
    )

    swarm_consensus_orchestrator = providers.Singleton(
        SwarmConsensusOrchestrator,
        agent_names=["VisualExpert", "AcousticExpert", "LoreExpert"],
        inference_engine=inference.inference_engine
    )

    counterfactual_simulator = providers.Singleton(
        CounterfactualConversationSimulator,
        inference_engine=inference.inference_engine
    )

    self_evolving_compiler = providers.Singleton(
        SelfEvolvingCompiler
    )

    autonomous_domain_synthesizer = providers.Singleton(
        AutonomousDomainSynthesizer,
        inference_engine=inference.inference_engine,
        neo4j_manager=persistence.graph_persistence_port,
        gold_dataset_port=persistence.gold_dataset_adapter
    )

    model_distillation_pipeline = providers.Singleton(
        ModelDistillationPipeline,
        teacher_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        gold_dataset_port=persistence.gold_dataset_adapter
    )

    star_mlops_service = providers.Singleton(
        StarMLOpsDomainService,
        prompt_manager=infrastructure.prompt_manager,
        gold_dataset_port=persistence.gold_dataset_adapter,
        eval_service=ragas_eval_service
    )

    synthetic_promotion_service = providers.Singleton(
        SyntheticDataPromotionService,
        gold_dataset_port=persistence.gold_dataset_adapter,
        domain_synthesizer=autonomous_domain_synthesizer,
        star_mlops_service=star_mlops_service
    )

    drift_service = providers.Singleton(
        DriftService,
        repository=persistence.repository
    )

    archetype_drift_service = providers.Singleton(
        ArchetypeDriftService,
        feedback_port=persistence.feedback_adapter,
        memory_service=agentic.memory_service,
        repository=persistence.repository
    )

    alert_service = providers.Singleton(
        AlertService,
        notification_port=infrastructure.notification_port,
        drift_service=drift_service
    )

    dpo_feedback_loop = providers.Singleton(
        DPOFeedbackLoop,
        prompt_manager=infrastructure.prompt_manager,
        feedback_port=persistence.feedback_adapter,
        llm_service=agentic.llm_service
    )

    fusion_service = providers.Singleton(
        FusionDomainService,
        llm_service=agentic.llm_service
    )

    vs_battle_service = providers.Singleton(
        VsBattleService,
        fandom_port=persistence.fandom_adapter,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        web_search_port=infrastructure.web_search
    )

    sota_benchmark_service = providers.Singleton(
        SOTABenchmarkService
    )

    health_dashboard_service = providers.Singleton(
        HealthDashboardService,
        usage_port=infrastructure.usage_port,
        sota_service=sota_benchmark_service
    )

    quantum_cognitive_model = providers.Singleton(
        QuantumCognitiveService,
        dimension=4
    )

    synaptic_plasticity_simulator = providers.Singleton(
        SynapticPlasticityService,
        num_concepts=10,
        checkpoint_path=os.path.join(os.getcwd(), "data", "artifacts", "synaptic_state.json")
    )

    xai_service = providers.Singleton(
        XaiDiagnosticService,
        inference_engine=inference.inference_engine
    )

    hierarchical_graph_rag_service = providers.Singleton(
        HierarchicalGraphRAGService,
        neo4j_manager=persistence.graph_persistence_port,
        llm_service=agentic.llm_service
    )

    complexity_analyser = providers.Singleton(
        ComplexityAnalyser,
        prompt_manager=infrastructure.prompt_manager,
        llm_service=agentic.llm_service
    )

    video_language_indexing_service = providers.Singleton(
        VideoLanguageIndexingService,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        repository=persistence.repository
    )

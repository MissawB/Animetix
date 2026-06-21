import os

from dependency_injector import containers, providers

from .lazy import LazyClass


class CoreServicesContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    inference = providers.DependenciesContainer()
    agentic = providers.DependenciesContainer()

    reasoning_agent = providers.Singleton(
        LazyClass(
            "core.domain.services.reasoning_agent_service", "ReasoningAgentService"
        ),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        search_service=agentic.rag_service,
        graph_manager=persistence.graph_persistence_port,
        agent_bus=providers.Singleton(
            LazyClass("core.domain.services.multi_agent_bus", "MultiAgentBus"),
            redis_url=os.getenv("REDIS_URL"),
        ),
    )

    sync_service = providers.Singleton(
        LazyClass("core.domain.services.media_sync_service", "MediaSyncService"),
        sync_adapter=providers.Factory(
            LazyClass(
                "adapters.persistence.pipeline_sync_adapter", "PipelineSyncAdapter"
            ),
            brain_api_url=os.getenv("BRAIN_API_URL", ""),
        ),
        repository=persistence.repository,
    )

    vision_service = providers.Singleton(
        LazyClass(
            "core.domain.services.advanced_vision_service", "AdvancedVisionService"
        ),
        inference_engine=inference.inference_engine,
    )

    graph_builder = providers.Singleton(
        LazyClass(
            "core.domain.services.graph_construction_service",
            "KnowledgeGraphConstructionService",
        ),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
    )

    graph_healer_service = providers.Singleton(
        LazyClass("core.domain.services.graph_healer_service", "GraphHealerService"),
        neo4j_manager=persistence.graph_persistence_port,
        construction_service=graph_builder,
        repository=persistence.repository,
        inference_engine=inference.inference_engine,
    )

    vision_quest_service = providers.Singleton(
        LazyClass(
            "core.domain.services.vision_quest_service", "VisionQuestDomainService"
        ),
        inference_engine=inference.vision_transformers_adapter,
        vision_service=vision_service,
    )

    emoji_service = providers.Singleton(
        LazyClass("core.domain.services.emoji_service", "EmojiDomainService"),
        llm_service=agentic.llm_service,
    )

    neuro_symbolic_service = providers.Singleton(
        LazyClass(
            "core.domain.services.neuro_symbolic_service", "NeuroSymbolicService"
        ),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
    )

    paradox_service = providers.Singleton(
        LazyClass("core.domain.services.paradox_service", "ParadoxDomainService"),
        llm_service=agentic.llm_service,
        neuro_symbolic_service=neuro_symbolic_service,
    )

    animinator_service = providers.Singleton(
        LazyClass("core.domain.services.animinator_service", "AniminatorDomainService"),
        llm_service=agentic.llm_service,
    )

    companion_service = providers.Singleton(
        LazyClass("core.domain.services.companion_service", "CompanionService"),
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager,
    )

    blind_test_service = providers.Singleton(
        LazyClass("core.domain.services.blind_test_service", "BlindTestDomainService"),
        repository=persistence.repository,
    )

    cover_test_service = providers.Singleton(
        LazyClass("core.domain.services.cover_test_service", "CoverTestDomainService"),
        repository=persistence.repository,
    )

    achievement_service = providers.Singleton(
        LazyClass(
            "core.domain.services.achievement_service", "AchievementDomainService"
        ),
        port=providers.Factory(
            LazyClass(
                "adapters.persistence.django_achievement_adapter",
                "DjangoAchievementAdapter",
            )
        ),
        notification_port=infrastructure.notification_port,
    )

    achievement_listener = providers.Singleton(
        LazyClass("core.domain.services.achievement_service", "GameEventListener"),
        achievement_service=achievement_service,
    )

    catalog_service = providers.Singleton(
        LazyClass("core.domain.services.catalog_service", "CatalogService"),
        repository=persistence.repository,
        sql_repository=persistence.django_repository,
        cache_service=providers.Object(
            __import__("django.core.cache", fromlist=["cache"]).cache
        ),
    )

    similarity_service = providers.Singleton(
        LazyClass("core.domain.services.similarity_service", "SimilarityService"),
        repository=persistence.repository,
    )

    cfr_game_solver = providers.Singleton(
        LazyClass("core.domain.services.cfr_game_solver", "CFRGameSolver"),
        num_actions=4,
    )

    akinetix_engine = providers.Singleton(
        LazyClass("core.domain.services.akinetix_engine", "AkinetixEngine"),
        catalog_service=catalog_service,
        cfr_solver=cfr_game_solver,
    )

    akinetix_service = providers.Singleton(
        LazyClass("core.domain.services.akinetix_service", "AkinetixService"),
        catalog_service=catalog_service,
        engine=akinetix_engine,
    )

    game_service = providers.Singleton(
        LazyClass("core.domain.services.game_service", "GameService"),
        repository=persistence.repository,
        catalog_service=catalog_service,
        similarity_service=providers.Factory(
            LazyClass("core.domain.services.similarity_service", "SimilarityService"),
            repository=persistence.repository,
        ),
        undercover_service=providers.Factory(
            LazyClass("core.domain.services.undercover_service", "UndercoverService"),
            catalog_service=catalog_service,
            similarity_service=providers.Factory(
                LazyClass(
                    "core.domain.services.similarity_service", "SimilarityService"
                ),
                repository=persistence.repository,
            ),
        ),
    )

    game_session_service_factory = providers.Factory(
        LazyClass("core.domain.services.game_session_service", "GameSessionService")
    )

    video_quest_service = providers.Singleton(
        LazyClass("core.domain.services.creative.video_quest", "VideoQuestService"),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
    )

    visual_novel_service = providers.Singleton(
        LazyClass(
            "core.domain.services.creative.visual_novel_service", "VisualNovelService"
        ),
        llm_service=agentic.llm_service,
        repository=persistence.repository,
    )

    studio_transform_service = providers.Singleton(
        LazyClass(
            "core.domain.services.creative.studio_transform", "StudioTransformService"
        ),
        inference_engine=inference.diffusers_adapter,
        prompt_manager=infrastructure.prompt_manager,
    )

    manga_flow_service = providers.Singleton(
        LazyClass("core.domain.services.creative.manga_flow", "MangaFlowService"),
        inference_engine=inference.inference_engine,
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager,
    )

    soundscape_service = providers.Singleton(
        LazyClass(
            "core.domain.services.creative.soundscape", "SoundscapeGenerationService"
        ),
        inference_engine=inference.inference_engine,
        video_service=video_quest_service,
        prompt_manager=infrastructure.prompt_manager,
    )

    # Défini dans le conteneur `agentic` (cf. dépendance circulaire core ↔ agentic).
    # Alias rétro-compatible : `Container.core.guardrail_service` reste valide.
    guardrail_service = agentic.guardrail_service

    red_teaming_agent = providers.Singleton(
        LazyClass("core.domain.services.guardrail_service", "RedTeamingAgent"),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
    )

    akinetix_rl_env_service = providers.Singleton(
        LazyClass("core.domain.services.akinetix_rl_service", "AkinetixRLService"),
        catalog_service=catalog_service,
    )

    self_play_debate_service = providers.Singleton(
        LazyClass(
            "core.domain.services.self_play_debate_service", "SelfPlayDebateService"
        ),
        llm_service=agentic.llm_service,
        neo4j_manager=persistence.graph_persistence_port,
    )

    ragas_eval_service = providers.Singleton(
        LazyClass("core.domain.services.ragas_eval_service", "RagasEvalService"),
        judge_engine=inference.inference_engine,
        eval_port=persistence.eval_adapter,
        gold_port=persistence.gold_dataset_adapter,
    )

    orchestrator_agent_service = providers.Singleton(
        LazyClass(
            "core.domain.services.orchestrator_agent_service",
            "OrchestratorAgentService",
        ),
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager,
    )

    cross_modal_search_service = providers.Singleton(
        LazyClass(
            "core.domain.services.cross_modal_service", "CrossModalSearchService"
        ),
        repository=persistence.repository,
    )

    spatial_computing_service = providers.Singleton(
        LazyClass(
            "core.domain.services.spatial_computing_service", "SpatialComputingService"
        ),
        vision_service=vision_service,
    )

    cinematic_volumetric_reconstruction_service = providers.Singleton(
        LazyClass(
            "core.domain.services.cinematic_volumetric_reconstruction_service",
            "CinematicVolumetricReconstructionService",
        ),
        vision_service=vision_service,
    )

    liquid_neural_network = providers.Singleton(
        LazyClass(
            "core.domain.services.neuromorphic_lnn_service",
            "LiquidNeuralNetworkService",
        ),
        state_dimension=4,
        input_dimension=2,
    )

    voice_cloning_service = providers.Singleton(
        LazyClass("core.domain.services.spatial_audio_service", "VoiceCloningService"),
        inference_engine=inference.inference_engine,
        lnn_simulator=liquid_neural_network,
    )

    native_speech_llm_service = providers.Singleton(
        LazyClass(
            "core.domain.services.spatial_audio_service", "NativeSpeechLLMService"
        ),
        inference_engine=inference.inference_engine,
    )

    cove_oracle_service = providers.Singleton(
        LazyClass("core.domain.services.cove_oracle_service", "CoveOracleService"),
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager,
    )

    star_reasoner_service = providers.Singleton(
        LazyClass("core.domain.services.star_reasoner_service", "StarReasonerService"),
        llm_service=agentic.llm_service,
        prompt_manager=infrastructure.prompt_manager,
        gold_dataset_port=persistence.gold_dataset_adapter,
    )

    tree_of_thoughts_service = providers.Singleton(
        LazyClass(
            "core.domain.services.tree_of_thoughts_service",
            "TreeOfThoughtsSearchService",
        ),
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
    )

    episodic_memory_compressor = providers.Singleton(
        LazyClass(
            "core.domain.services.episodic_memory_compressor",
            "EpisodicMemoryCompressor",
        ),
        chroma_resource=persistence.repository,
        inference_engine=inference.inference_engine,
        neo4j_manager=persistence.graph_persistence_port,
    )

    neuro_symbolic_user_profiler = providers.Singleton(
        LazyClass(
            "core.domain.services.neuro_symbolic_user_profiler",
            "NeuroSymbolicUserProfiler",
        ),
        feedback_adapter=persistence.feedback_adapter,
    )

    dspy_prompt_optimizer = providers.Singleton(
        LazyClass("core.domain.services.dspy_prompt_optimizer", "DSPyPromptOptimizer"),
        inference_engine=inference.inference_engine,
    )

    swarm_consensus_orchestrator = providers.Singleton(
        LazyClass("core.domain.services.swarm_consensus", "SwarmConsensusOrchestrator"),
        agent_names=["VisualExpert", "AcousticExpert", "LoreExpert"],
        inference_engine=inference.inference_engine,
    )

    counterfactual_simulator = providers.Singleton(
        LazyClass(
            "core.domain.services.counterfactual_simulator",
            "CounterfactualConversationSimulator",
        ),
        inference_engine=inference.inference_engine,
    )

    self_evolving_compiler = providers.Singleton(
        LazyClass("core.domain.services.self_evolving_compiler", "SelfEvolvingCompiler")
    )

    autonomous_domain_synthesizer = providers.Singleton(
        LazyClass(
            "core.domain.services.domain_synthesizer", "AutonomousDomainSynthesizer"
        ),
        inference_engine=inference.inference_engine,
        neo4j_manager=persistence.graph_persistence_port,
        gold_dataset_port=persistence.gold_dataset_adapter,
    )

    model_distillation_pipeline = providers.Singleton(
        LazyClass(
            "core.domain.services.distillation_pipeline", "ModelDistillationPipeline"
        ),
        teacher_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        gold_dataset_port=persistence.gold_dataset_adapter,
    )

    star_mlops_service = providers.Singleton(
        LazyClass("core.domain.services.star_mlops_service", "StarMLOpsDomainService"),
        prompt_manager=infrastructure.prompt_manager,
        gold_dataset_port=persistence.gold_dataset_adapter,
        eval_service=ragas_eval_service,
    )

    synthetic_promotion_service = providers.Singleton(
        LazyClass(
            "core.domain.services.synthetic_promotion_service",
            "SyntheticDataPromotionService",
        ),
        gold_dataset_port=persistence.gold_dataset_adapter,
        domain_synthesizer=autonomous_domain_synthesizer,
        star_mlops_service=star_mlops_service,
    )

    drift_service = providers.Singleton(
        LazyClass("core.domain.services.drift_service", "DriftService"),
        vector_store=persistence.chroma_vector_store,
        config_port=infrastructure.config_port,
    )

    archetype_drift_service = providers.Singleton(
        LazyClass(
            "core.domain.services.archetype_drift_service", "ArchetypeDriftService"
        ),
        feedback_port=persistence.feedback_adapter,
        memory_service=agentic.memory_service,
        repository=persistence.repository,
    )

    alert_service = providers.Singleton(
        LazyClass("core.domain.services.alert_service", "AlertService"),
        notification_port=infrastructure.notification_port,
        drift_service=drift_service,
        observability_service=infrastructure.obs_service,
    )

    dpo_feedback_loop = providers.Singleton(
        LazyClass("core.domain.services.dpo_feedback_loop", "DPOFeedbackLoop"),
        prompt_manager=infrastructure.prompt_manager,
        feedback_port=persistence.feedback_adapter,
        llm_service=agentic.llm_service,
    )

    fusion_service = providers.Singleton(
        LazyClass(
            "core.domain.services.creative.fusion_service", "FusionDomainService"
        ),
        llm_service=agentic.llm_service,
    )

    vs_battle_service = providers.Singleton(
        LazyClass("core.domain.services.creative.vs_battle_service", "VsBattleService"),
        fandom_port=persistence.fandom_adapter,
        inference_engine=inference.inference_engine,
        prompt_manager=infrastructure.prompt_manager,
        web_search_port=infrastructure.web_search,
    )

    sota_benchmark_service = providers.Singleton(
        LazyClass("core.domain.services.sota_benchmark_service", "SOTABenchmarkService")
    )

    health_dashboard_service = providers.Singleton(
        LazyClass(
            "core.domain.services.health_dashboard_service", "HealthDashboardService"
        ),
        usage_port=infrastructure.usage_port,
        sota_service=sota_benchmark_service,
        inference_engine=inference.inference_engine,
        graph_port=persistence.graph_persistence_port,
        cache_port=infrastructure.cache_port,
    )

    quantum_cognitive_model = providers.Singleton(
        LazyClass(
            "core.domain.services.quantum_cognitive_service", "QuantumCognitiveService"
        ),
        dimension=4,
    )

    synaptic_plasticity_simulator = providers.Singleton(
        LazyClass(
            "core.domain.services.neuromorphic_plasticity_service",
            "SynapticPlasticityService",
        ),
        num_concepts=10,
        checkpoint_path=os.path.join(
            os.getcwd(), "data", "artifacts", "synaptic_state.json"
        ),
    )

    xai_service = providers.Singleton(
        LazyClass("core.domain.services.xai_service", "XaiDiagnosticService"),
        inference_engine=inference.inference_engine,
    )

    hierarchical_graph_rag_service = providers.Singleton(
        LazyClass(
            "core.domain.services.hierarchical_graph_rag", "HierarchicalGraphRAGService"
        ),
        neo4j_manager=persistence.graph_persistence_port,
        llm_service=agentic.llm_service,
        partitioner=agentic.community_partitioner,
    )

    complexity_analyser = providers.Singleton(
        LazyClass("core.domain.services.complexity_analyser", "ComplexityAnalyser"),
        prompt_manager=infrastructure.prompt_manager,
        llm_service=agentic.llm_service,
    )

    manga_service = providers.Singleton(
        LazyClass("core.domain.services.manga_service", "MangaService"),
        suwayomi_adapter=persistence.suwayomi_adapter,
    )

    synthetic_validation_service = providers.Singleton(
        LazyClass("core.domain.services.validation_gate", "SyntheticValidationService"),
        inference_engine=inference.inference_engine,
        gold_dataset_port=persistence.gold_dataset_adapter,
        guardrail_service=guardrail_service,
        xai_service=xai_service,
    )

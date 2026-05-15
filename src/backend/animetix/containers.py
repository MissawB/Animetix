import os
import logging
from django.conf import settings

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
from core.domain.services.agentic_rag_service import AgenticRAGService
from core.domain.services.long_term_memory_service import LongTermMemoryService
from core.domain.services.semantic_cache_service import SemanticCacheService
from core.domain.services.observability_service import ObservabilityService

# Adapters
from adapters.persistence.unified_repository_adapter import UnifiedRepositoryAdapter
from adapters.persistence.django_usage_adapter import DjangoUsageAdapter
from adapters.persistence.pipeline_sync_adapter import PipelineSyncAdapter
from adapters.persistence.django_achievement_adapter import DjangoAchievementAdapter
from adapters.persistence.web_search_adapter import DuckDuckGoSearchAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter
from adapters.inference.vllm_adapter import VllmAdapter
from adapters.inference.local_llama_adapter import LocalLlamaAdapter
from adapters.inference.gguf_adapter import GgufAdapter
from adapters.inference.moondream_adapter import MoondreamAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter

# Clients
from pipeline.neo4j_client import neo4j_manager

logger = logging.getLogger('animetix')

class Container:
    """Dependency Injection Container with full Lazy Loading."""
    
    def __init__(self):
        # Initialiser les caches de propriétés
        self._cache = {}

    def _get(self, key, factory):
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    @property
    def prompt_manager(self):
        return self._get('prompt_manager', lambda: PromptManager(prompts_dir=os.path.join(settings.PROJECT_ROOT, "src", "core", "domain", "services", "prompts")))

    @property
    def repository(self):
        return self._get('repository', lambda: UnifiedRepositoryAdapter(chroma_db_path=settings.CHROMA_DB_PATH, project_root=settings.PROJECT_ROOT))

    @property
    def django_repository(self):
        return self.repository.django

    @property
    def obs_service(self):
        return self._get('obs_service', lambda: ObservabilityService(project_name="animetix-production"))

    @property
    def gguf_adapter(self):
        return self._get('gguf_adapter', lambda: GgufAdapter(model_path=os.path.join(settings.MODELS_DIR, "qwen2.5-1.5b-instruct.Q4_K_M.gguf")) if os.path.exists(os.path.join(settings.MODELS_DIR, "qwen2.5-1.5b-instruct.Q4_K_M.gguf")) else None)

    @property
    def moondream_adapter(self):
        return self._get('moondream_adapter', lambda: MoondreamAdapter())

    @property
    def inference_engine(self):
        return self._get('inference_engine', lambda: FallbackInferenceAdapter(adapters=[
            BrainAPIAdapter(brain_api_url=os.getenv("BRAIN_API_URL", "")),
            VllmAdapter(api_base=os.getenv("VLLM_API_BASE", "http://vllm:8000/v1"), model_name="meta-llama/Llama-3-8B-Instruct"),
            self.gguf_adapter,
            LocalLlamaAdapter(model_path=os.path.join(settings.MODELS_DIR, "llama-3-8b"), hf_token=os.getenv("HUGGINGFACE_TOKEN"), use_4bit=True)
        ]))

    @property
    def reranker(self):
        return self._get('reranker', lambda: __import__('sentence_transformers').CrossEncoder('BAAI/bge-reranker-base'))

    @property
    def llm_service(self):
        return self._get('llm_service', lambda: LLMService(inference_engine=self.inference_engine, prompt_manager=self.prompt_manager, usage_port=DjangoUsageAdapter(), slm_engine=self.gguf_adapter, obs_service=self.obs_service))

    @property
    def agent_bus(self):
        return self._get('agent_bus', lambda: MultiAgentBus(redis_url=os.getenv("REDIS_URL")))

    @property
    def rag_service(self):
        return self._get('rag_service', lambda: AdvancedRAGService(repository=self.repository, llm_service=self.llm_service, neo4j_manager=neo4j_manager, reranker=self.reranker))

    @property
    def agentic_rag(self):
        return self._get('agentic_rag', lambda: AgenticRAGService(inference_engine=self.inference_engine, rag_service=self.rag_service, web_search=DuckDuckGoSearchAdapter(), prompt_manager=self.prompt_manager, llm_service=self.llm_service, neo4j_manager=neo4j_manager, memory_service=self.memory_service, semantic_cache=self.semantic_cache_service, obs_service=self.obs_service))

    @property
    def reasoning_agent(self):
        return self._get('reasoning_agent', lambda: ReasoningAgentService(inference_engine=self.inference_engine, search_service=self.rag_service, graph_manager=neo4j_manager, agent_bus=self.agent_bus))

    @property
    def memory_service(self):
        return self._get('memory_service', lambda: LongTermMemoryService(chroma_resource=self.repository, inference_engine=self.inference_engine))

    @property
    def semantic_cache_service(self):
        return self._get('semantic_cache_service', lambda: SemanticCacheService(chroma_resource=self.repository))

    @property
    def sync_adapter(self):
        return self._get('sync_adapter', lambda: PipelineSyncAdapter(brain_api_url=os.getenv("BRAIN_API_URL", "")))

    @property
    def sync_service(self):
        return self._get('sync_service', lambda: MediaSyncService(sync_adapter=self.sync_adapter, repository=self.repository))

    @property
    def vision_service(self):
        return self._get('vision_service', lambda: AdvancedVisionService(inference_engine=self.inference_engine))

    @property
    def graph_builder(self):
        return self._get('graph_builder', lambda: KnowledgeGraphConstructionService(inference_engine=self.inference_engine))

    @property
    def vision_quest_service(self):
        return self._get('vision_quest_service', lambda: VisionQuestDomainService(inference_engine=self.moondream_adapter, vision_service=self.vision_service))

    @property
    def emoji_service(self):
        return self._get('emoji_service', lambda: EmojiDomainService(llm_service=self.llm_service))

    @property
    def paradox_service(self):
        return self._get('paradox_service', lambda: ParadoxDomainService(llm_service=self.llm_service, neuro_symbolic_service=self.neuro_symbolic_service))

    @property
    def animinator_service(self):
        return self._get('animinator_service', lambda: AniminatorDomainService(llm_service=self.llm_service))

    @property
    def akinetix_service(self):
        return self._get('akinetix_service', lambda: AkinetixDomainService(catalog_service=self.catalog_service))

    @property
    def blind_test_service(self):
        return self._get('blind_test_service', lambda: BlindTestDomainService(repository=self.repository))

    @property
    def cover_test_service(self):
        return self._get('cover_test_service', lambda: CoverTestDomainService(repository=self.repository))

    @property
    def achievement_service(self):
        return self._get('achievement_service', lambda: AchievementDomainService(port=DjangoAchievementAdapter()))

    @property
    def achievement_listener(self):
        return self._get('achievement_listener', lambda: GameEventListener(self.achievement_service))

    @property
    def neuro_symbolic_service(self):
        return self._get('neuro_symbolic_service', lambda: NeuroSymbolicService(inference_engine=self.inference_engine))

    @property
    def video_quest_service(self):
        return self._get('video_quest_service', lambda: VideoQuestService(inference_engine=self.inference_engine))

    @property
    def studio_transform_service(self):
        return self._get('studio_transform_service', lambda: StudioTransformService(inference_engine=self.inference_engine))

    @property
    def manga_flow_service(self):
        return self._get('manga_flow_service', lambda: MangaFlowService(inference_engine=self.inference_engine, llm_service=self.llm_service))

    @property
    def soundscape_service(self):
        return self._get('soundscape_service', lambda: SoundscapeGenerationService(inference_engine=self.inference_engine, video_service=self.video_quest_service))

    @property
    def spatial_computing_service(self):
        return self._get('spatial_computing_service', lambda: SpatialComputingService(inference_engine=self.inference_engine))

    @property
    def guardrail_service(self):
        return self._get('guardrail_service', lambda: GuardrailService(inference_engine=self.inference_engine))

    @property
    def red_teaming_agent(self):
        return self._get('red_teaming_agent', lambda: RedTeamingAgent(inference_engine=self.inference_engine))

    @property
    def akinetix_rl_service(self):
        return self._get('akinetix_rl_service', lambda: AkinetixRLService(catalog_service=self.game_service))

    @property
    def self_play_debate_service(self):
        return self._get('self_play_debate_service', lambda: SelfPlayDebateService(inference_engine=self.inference_engine))

    @property
    def ragas_eval_service(self):
        return self._get('ragas_eval_service', lambda: RagasEvalService(judge_engine=self.inference_engine))

    @property
    def orchestrator(self):
        return self._get('orchestrator', lambda: OrchestratorAgentService(inference_engine=self.inference_engine, services_factory=self))

    @property
    def cross_modal_search(self):
        return self._get('cross_modal_search', lambda: CrossModalSearchService(inference_engine=self.inference_engine, vector_db=self.repository))

    @property
    def vlm_indexing(self):
        return self._get('vlm_indexing', lambda: VlmIndexingService(inference_engine=self.inference_engine))

    @property
    def xai_diagnostic_service(self):
        return self._get('xai_diagnostic_service', lambda: XaiDiagnosticService(inference_engine=self.inference_engine))

    @property
    def uncertainty_service(self):
        return self._get('uncertainty_service', lambda: UncertaintyService(inference_engine=self.inference_engine))

    @property
    def voice_cloning_service(self):
        return self._get('voice_cloning_service', lambda: VoiceCloningService(inference_engine=self.inference_engine))

    @property
    def native_speech_llm_service(self):
        return self._get('native_speech_llm_service', lambda: NativeSpeechLLMService(inference_engine=self.inference_engine))

    @property
    def translation_service(self):
        return self._get('translation_service', lambda: TranslationService())

    @property
    def catalog_service(self):
        from django.core.cache import cache
        return CatalogService(repository=self.repository, sql_repository=self.django_repository, cache_service=cache)

    @property
    def game_service(self):
        sim = SimilarityService(repository=self.repository)
        und = UndercoverService(catalog_service=self.catalog_service, similarity_service=sim)
        return GameService(repository=self.repository, catalog_service=self.catalog_service, similarity_service=sim, undercover_service=und)

# Global container instance
_container = None

def get_container():
    global _container
    if _container is None:
        _container = Container()
    return _container

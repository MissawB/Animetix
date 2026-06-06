from django.conf import settings
from dependency_injector import containers, providers

from adapters.persistence.unified_repository_adapter import UnifiedRepositoryAdapter
from adapters.persistence.neo4j_graph_adapter import Neo4jGraphAdapter
from adapters.persistence.django_semantic_cache_adapter import DjangoSemanticCacheAdapter
from adapters.persistence.django_feedback_adapter import DjangoFeedbackAdapter
from adapters.persistence.django_eval_adapter import DjangoEvalAdapter
from adapters.persistence.django_gold_dataset_adapter import DjangoGoldDatasetAdapter
from adapters.persistence.colbert_adapter import LateInteractionColBERTAdapter
from adapters.persistence.fandom_adapter import FandomAdapter
from adapters.persistence.session_state_adapter import DjangoSessionStateAdapter

from adapters.persistence.django_safety_adapter import DjangoSafetyAdapter

class PersistenceContainer(containers.DeclarativeContainer):
    repository = providers.Singleton(
        UnifiedRepositoryAdapter,
        chroma_db_path=settings.CHROMA_DB_PATH,
        project_root=settings.PROJECT_ROOT
    )

    django_repository = providers.Callable(
        lambda repo: repo.django,
        repository
    )

    graph_persistence_port = providers.Singleton(Neo4jGraphAdapter)

    semantic_cache_adapter = providers.Singleton(DjangoSemanticCacheAdapter)
    feedback_adapter = providers.Singleton(DjangoFeedbackAdapter)
    eval_adapter = providers.Singleton(DjangoEvalAdapter)
    gold_dataset_adapter = providers.Singleton(DjangoGoldDatasetAdapter)
    colbert_adapter = providers.Singleton(LateInteractionColBERTAdapter)
    fandom_adapter = providers.Singleton(FandomAdapter)
    
    safety_adapter = providers.Singleton(DjangoSafetyAdapter)

    session_state_adapter_factory = providers.Factory(
        DjangoSessionStateAdapter
    )

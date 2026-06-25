from dependency_injector import containers, providers
from django.conf import settings

from .lazy import LazyClass


class PersistenceContainer(containers.DeclarativeContainer):
    repository = providers.Singleton(
        LazyClass(
            "adapters.persistence.unified_repository_adapter",
            "UnifiedRepositoryAdapter",
        ),
        project_root=settings.PROJECT_ROOT,
    )

    django_repository = providers.Callable(lambda repo: repo.django, repository)

    vector_store = providers.Singleton(
        "adapters.persistence.pg_vector_store_adapter.PgVectorStoreAdapter"
    )

    graph_persistence_port = providers.Singleton(
        LazyClass("adapters.persistence.neo4j_graph_adapter", "Neo4jGraphAdapter")
    )

    semantic_cache_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.django_semantic_cache_adapter",
            "DjangoSemanticCacheAdapter",
        )
    )
    feedback_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.django_feedback_adapter", "DjangoFeedbackAdapter"
        )
    )
    eval_adapter = providers.Singleton(
        LazyClass("adapters.persistence.django_eval_adapter", "DjangoEvalAdapter")
    )
    gold_dataset_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.django_gold_dataset_adapter",
            "DjangoGoldDatasetAdapter",
        )
    )
    colbert_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.colbert_adapter", "LateInteractionColBERTAdapter"
        )
    )
    fandom_adapter = providers.Singleton(
        LazyClass("adapters.persistence.fandom_adapter", "FandomAdapter")
    )

    suwayomi_adapter = providers.Singleton(
        LazyClass("adapters.persistence.suwayomi_adapter", "SuwayomiAdapter")
    )

    voice_profile_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.django_voice_profile_adapter",
            "DjangoVoiceProfileAdapter",
        )
    )

    manga_repository_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.django_manga_repository_adapter",
            "DjangoMangaRepositoryAdapter",
        )
    )

    safety_adapter = providers.Singleton(
        LazyClass("adapters.persistence.django_safety_adapter", "DjangoSafetyAdapter")
    )

    session_state_adapter_factory = providers.Factory(
        LazyClass(
            "adapters.persistence.session_state_adapter", "DjangoSessionStateAdapter"
        )
    )

    feature_store_adapter = providers.Singleton(
        LazyClass(
            "adapters.persistence.feature_store_adapter",
            "FeatureStoreAdapter",
        )
    )

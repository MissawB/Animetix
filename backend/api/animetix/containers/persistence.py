from django.conf import settings
from dependency_injector import containers, providers


class LazyClass:
    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name
        self._class = None

    def __call__(self, *args, **kwargs):
        if self._class is None:
            import importlib  # noqa: E402

            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class(*args, **kwargs)


class PersistenceContainer(containers.DeclarativeContainer):
    repository = providers.Singleton(
        LazyClass(
            "adapters.persistence.unified_repository_adapter",
            "UnifiedRepositoryAdapter",
        ),
        project_root=settings.PROJECT_ROOT,
    )

    django_repository = providers.Callable(lambda repo: repo.django, repository)

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

    safety_adapter = providers.Singleton(
        LazyClass("adapters.persistence.django_safety_adapter", "DjangoSafetyAdapter")
    )

    session_state_adapter_factory = providers.Factory(
        LazyClass(
            "adapters.persistence.session_state_adapter", "DjangoSessionStateAdapter"
        )
    )

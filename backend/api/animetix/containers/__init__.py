from dependency_injector import containers, providers

from .agentic import AgenticContainer
from .core_services import CoreServicesContainer
from .inference import InferenceContainer
from .infrastructure import InfrastructureContainer
from .persistence import PersistenceContainer


class Container(containers.DeclarativeContainer):
    infrastructure = providers.Container(InfrastructureContainer)
    persistence = providers.Container(PersistenceContainer)
    inference = providers.Container(InferenceContainer, infrastructure=infrastructure)
    agentic = providers.Container(
        AgenticContainer,
        infrastructure=infrastructure,
        persistence=persistence,
        inference=inference,
    )
    core = providers.Container(
        CoreServicesContainer,
        infrastructure=infrastructure,
        persistence=persistence,
        inference=inference,
        agentic=agentic,
    )


class ProviderDelegate:
    """Wrapper to expose sub-container providers directly on the root container
    without being detected as a Provider by dependency_injector's wiring.
    """

    def __init__(self, provider):
        self._provider = provider

    def __call__(self, *args, **kwargs):
        return self._provider(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._provider(), name)


container = Container()


# Expose shortcuts for backward compatibility with legacy scripts/commands
container.agentic_rag = ProviderDelegate(container.agentic.agentic_rag)
container.rag_service = ProviderDelegate(container.agentic.rag_service)
container.prompt_manager = ProviderDelegate(container.infrastructure.prompt_manager)
container.red_teaming_agent = ProviderDelegate(container.core.red_teaming_agent)
container.catalog_service = ProviderDelegate(container.core.catalog_service)
container.video_quest_service = ProviderDelegate(container.core.video_quest_service)
container.inference_engine = ProviderDelegate(container.inference.inference_engine)
container.neo4j_manager = ProviderDelegate(container.persistence.graph_persistence_port)


def get_container():
    return container

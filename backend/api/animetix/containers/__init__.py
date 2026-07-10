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


container = Container()


def get_container():
    return container

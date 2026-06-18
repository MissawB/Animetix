from dependency_injector.wiring import inject, Provide
from animetix.containers import Container


@inject
def get_session_service(
    request,
    session_factory=Provide[Container.core.game_session_service_factory.provider],
    port_factory=Provide[Container.persistence.session_state_adapter_factory.provider],
):
    port = port_factory(session=request.session)
    return session_factory(state_port=port)

from dependency_injector.wiring import inject, Provide
from animetix.containers import Container
from core.domain.services.game_session_service import GameSessionService

@inject
def get_session_service(request, 
                        session_factory: GameSessionService = Provide[Container.core.game_session_service_factory],
                        port_factory = Provide[Container.persistence.session_state_adapter_factory]):
    port = port_factory(session=request.session)
    return session_factory(state_port=port)

def get_session_service(request):
    """Resolve game-session factories dynamically from the container.

    Previous implementation used ``@inject`` with ``Provide[...]`` markers,
    which broke under ``--cov=animetix.views.api``: coverage-instrumenting
    the views module forced an early import of this file before
    ``container.wire()`` ran, leaving the markers as unwired ``_Marker``
    objects that re-wiring could not repair.

    Resolving directly from the live container instance at call time
    side-steps the import-order sensitivity entirely and is fully
    compatible with per-test ``provider.override()`` scoping.
    """
    from animetix.containers import container

    session_factory = container.core.game_session_service_factory.provider()
    port_factory = container.persistence.session_state_adapter_factory.provider()
    port = port_factory(session=request.session)
    return session_factory(state_port=port)

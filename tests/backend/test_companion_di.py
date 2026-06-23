def test_companion_service_provider_wires_memory_service():
    from animetix.containers import get_container

    provider = get_container().core.companion_service
    assert "memory_service" in provider.kwargs

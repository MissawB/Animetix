from django.conf import settings


def test_cognitive_boosters_setting_defaults_true():
    assert getattr(settings, "RAG_COGNITIVE_BOOSTERS_ENABLED") is True


def test_rag_service_provider_wires_the_flag():
    from animetix.containers import get_container

    rag_provider = get_container().agentic.rag_service
    assert rag_provider.kwargs.get("cognitive_boosters_enabled") is True

"""Smoke test du conteneur DI : vérifie l'absence de dépendance circulaire après
le déplacement de `guardrail_service` vers le conteneur `agentic` (suppression de
l'anti-pattern `get_container()` dans AgenticRAGService)."""


def test_guardrail_alias_resolves_to_agentic():
    from animetix.containers import container

    core_guardrail = container.core.guardrail_service()
    agentic_guardrail = container.agentic.guardrail_service()
    # Même singleton exposé des deux côtés (alias dans core_services).
    assert core_guardrail is agentic_guardrail


def test_agentic_rag_receives_guardrail_without_get_container():
    from animetix.containers import container

    agentic_rag = container.agentic.agentic_rag()
    # Le guardrail est injecté par le conteneur, plus via get_container().
    assert agentic_rag.guardrail_service is container.agentic.guardrail_service()


def test_drift_and_hierarchical_wiring_resolve():
    """Le nouveau câblage (VectorStorePort, partitioner injecté) se résout sans erreur."""
    from animetix.containers import container

    drift = container.core.drift_service()
    assert drift.vector_store is container.persistence.vector_store()

    hgr = container.core.hierarchical_graph_rag_service()
    assert hgr.partitioner is container.agentic.community_partitioner()

"""Tests de l'abstraction de cache (CachePort) et de son intégration dans le core.

Vérifie que le `core` reste utilisable sans le cache Django (isolation hexagonale).
"""

from core.ports.generic_cache_port import InMemoryCache


def test_inmemory_cache_get_set():
    c = InMemoryCache()
    assert c.get("missing") is None
    assert c.get("missing", "fallback") == "fallback"
    c.set("k", 42)
    assert c.get("k") == 42


def test_inmemory_cache_many():
    c = InMemoryCache()
    c.set_many({"a": 1, "b": 2})
    assert c.get_many(["a", "b", "absent"]) == {"a": 1, "b": 2}


def test_reranking_cache_uses_injected_port():
    """RerankingCache fonctionne avec un port injecté, sans Django."""
    from core.domain.services.rag.rerank_cache import RerankingCache

    cache = InMemoryCache()
    rc = RerankingCache(cache_port=cache)
    rc.set_scores("ma requete", {"doc1": 0.9, "doc2": 0.5})

    scores = rc.get_scores("ma requete", ["doc1", "doc2", "doc3"])
    assert scores == {"doc1": 0.9, "doc2": 0.5}


def test_reranking_cache_defaults_to_inmemory():
    """Sans port injecté, RerankingCache se rabat sur un cache en mémoire (pas de Django)."""
    from core.domain.services.rag.rerank_cache import RerankingCache

    rc = RerankingCache()
    assert isinstance(rc.cache, InMemoryCache)

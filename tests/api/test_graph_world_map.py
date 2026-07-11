"""Regression tests for the Lore World Map endpoint.

Prod bug (2026-07-11): the view generated the map *inside the request* — one
sequential LLM call per community — which always outran the request timeout
(observed: HTTP 503 after 43s on animetix.xyz). The cache was therefore never
populated, the 120s anti-stampede lock stayed held, and every other caller got
the 202 ``{"status": "generating"}`` body, which the frontend rendered straight
into ``communities.map(...)`` → "e?.map is not a function".

The view is now read-only: it serves the cache, and never generates. Generation
belongs to the ``generate_world_map`` management command (run by the MLOps job).
"""

from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

CACHE_KEY = "graph:world_map:v1"

COMMUNITIES = [
    {
        "id": "community_0",
        "name": "Communauté Anime",
        "summary": "Un résumé.",
        "entities": ["Naruto"],
    }
]


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.delete(CACHE_KEY)
    cache.delete(f"{CACHE_KEY}:lock")
    yield
    cache.delete(CACHE_KEY)
    cache.delete(f"{CACHE_KEY}:lock")


@pytest.fixture
def partitioner():
    p = MagicMock()
    p.run_partitioning.return_value = COMMUNITIES
    container.agentic.community_partitioner.override(providers.Object(p))
    yield p
    container.agentic.community_partitioner.reset_last_overriding()


@pytest.mark.django_db
def test_world_map_serves_the_cached_communities(partitioner):
    cache.set(CACHE_KEY, COMMUNITIES, timeout=60)

    resp = APIClient().get(reverse("api_graph_world_map"))

    assert resp.status_code == 200
    assert resp.json() == COMMUNITIES
    # Serving must never trigger generation (that is what blew the timeout).
    partitioner.run_partitioning.assert_not_called()


@pytest.mark.django_db
def test_world_map_reports_generating_without_blocking_on_a_cold_cache(partitioner):
    resp = APIClient().get(reverse("api_graph_world_map"))

    assert resp.status_code == 202
    assert resp.json() == {"status": "generating"}
    # The killer: the request must NOT run the LLM partitioning inline.
    partitioner.run_partitioning.assert_not_called()


@pytest.mark.django_db
def test_generate_world_map_command_populates_the_cache(partitioner):
    call_command("generate_world_map")

    partitioner.run_partitioning.assert_called_once()
    assert cache.get(CACHE_KEY) == COMMUNITIES


@pytest.mark.django_db
def test_generate_world_map_command_keeps_the_previous_map_on_failure(partitioner):
    cache.set(CACHE_KEY, COMMUNITIES, timeout=60)
    partitioner.run_partitioning.side_effect = RuntimeError("neo4j down")

    with pytest.raises(RuntimeError):
        call_command("generate_world_map")

    # A failed refresh must not wipe a usable map.
    assert cache.get(CACHE_KEY) == COMMUNITIES


@pytest.mark.django_db
def test_generate_world_map_command_refuses_to_cache_a_non_list(partitioner):
    partitioner.run_partitioning.return_value = {"status": "weird"}

    with pytest.raises(ValueError):
        call_command("generate_world_map")

    # The frontend contract is a JSON array — never cache anything else.
    assert cache.get(CACHE_KEY) is None

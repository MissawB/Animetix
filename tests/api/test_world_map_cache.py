from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.core.cache import cache
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_second_hit_serves_cache_without_partitioning():
    partitioner = MagicMock()
    partitioner.run_partitioning.return_value = [{"name": "C1"}]

    with container.agentic.community_partitioner.override(
        providers.Object(partitioner)
    ):
        c = APIClient()
        r1 = c.get("/api/v1/graph/world-map/")
        r2 = c.get("/api/v1/graph/world-map/")

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.data == r2.data == [{"name": "C1"}]
    # Only the first hit ran the LLM partitioning.
    partitioner.run_partitioning.assert_called_once()

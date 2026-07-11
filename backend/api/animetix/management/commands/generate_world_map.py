"""Pre-computes the Lore World Map and stores it in the cache.

The partitioning chains one LLM call per community, which is far too slow to run
inside an HTTP request (prod served a 503 after 43s, so the cache never filled
and the endpoint answered "generating" forever). Generation therefore lives here
and is driven by the MLOps job; ``GraphWorldMapView`` only ever reads the cache.
"""

import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand

from animetix.api.graph import WORLD_MAP_CACHE_KEY

logger = logging.getLogger("animetix.graph.world_map")

# The map is a shared artifact: keep the previous one servable well past the
# daily refresh, so one failed run never empties the page.
CACHE_TTL_SECONDS = 7 * 24 * 3600


class Command(BaseCommand):
    help = "Generates the Lore World Map (graph communities) and caches it."

    def handle(self, *args, **options):
        from animetix.containers import get_container

        partitioner = get_container().agentic.community_partitioner()

        self.stdout.write("Partitioning the knowledge graph...")
        communities = partitioner.run_partitioning()

        # The endpoint's contract with the frontend is a JSON array. Caching
        # anything else is what surfaced as "e?.map is not a function".
        if not isinstance(communities, list):
            raise ValueError(
                f"run_partitioning() must return a list, got {type(communities).__name__}"
            )

        cache.set(WORLD_MAP_CACHE_KEY, communities, timeout=CACHE_TTL_SECONDS)
        logger.info("World map cached: %d communities", len(communities))
        self.stdout.write(
            self.style.SUCCESS(f"World map cached: {len(communities)} communities.")
        )

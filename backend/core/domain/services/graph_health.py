"""Shared knowledge-graph health detection.

Used by the RAG services to tell a genuine Neo4j outage apart from a
deployment with no graph wired, so callers can fall back (to the pgvector
memory store / web) and surface a degraded-state signal instead of silently
proceeding with empty context.
"""

import logging
from typing import Optional

from core.ports.graph_persistence_port import GraphPersistencePort

logger = logging.getLogger("animetix.graph_health")


def is_graph_degraded(neo4j_manager: Optional[GraphPersistencePort]) -> bool:
    """True iff a graph backend is configured but currently unreachable.

    Returns False when no manager is wired (a valid deployment, not an outage)
    or when the manager exposes no health probe (can't tell — don't false-alarm).
    Any error raised while probing is treated as degraded.
    """
    if neo4j_manager is None:
        return False
    check = getattr(neo4j_manager, "check_health", None)
    if not callable(check):
        return False
    try:
        return not check()
    except Exception:
        return True

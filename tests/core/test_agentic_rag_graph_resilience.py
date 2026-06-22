"""Unit tests for Neo4j graph-outage resilience in AgenticRAGService.

When the knowledge graph is unavailable, the service must NOT silently proceed
with an empty user-preference context (which the old code did — it could not
tell "user has no history" apart from "graph is down"). Instead it must:
  * detect the outage via the graph adapter's health check,
  * surface a degraded-state signal (so callers/observability know), and
  * fall back to the pgvector memory store for preference context.

These are fast unit tests (no live LLM/orchestrator), so they are NOT marked
integration and run in CI.
"""

from unittest.mock import MagicMock

from core.domain.services.agentic_rag_service import (
    AgenticRAGService,
    _graph_is_degraded,
)

# --- _graph_is_degraded: pure outage detection -------------------------------


def test_graph_not_degraded_when_no_manager_configured():
    # No graph backend wired at all is a valid deployment, not an outage.
    assert _graph_is_degraded(None) is False


def test_graph_not_degraded_when_healthy():
    mgr = MagicMock()
    mgr.check_health.return_value = True
    assert _graph_is_degraded(mgr) is False


def test_graph_degraded_when_health_check_false():
    mgr = MagicMock()
    mgr.check_health.return_value = False
    assert _graph_is_degraded(mgr) is True


def test_graph_degraded_when_health_check_raises():
    mgr = MagicMock()
    mgr.check_health.side_effect = RuntimeError("bolt connection refused")
    assert _graph_is_degraded(mgr) is True


def test_graph_not_degraded_when_manager_has_no_health_check():
    # A manager without check_health can't be probed; assume up (don't false-alarm).
    mgr = MagicMock(spec=["get_user_preferences_context"])
    assert _graph_is_degraded(mgr) is False


# --- _load_user_preferences: signal + pgvector fallback ----------------------


def _build_service(neo4j_manager=None, memory_service=None, obs_service=None):
    return AgenticRAGService(
        inference_engine=MagicMock(),
        rag_service=MagicMock(),
        web_search=MagicMock(),
        prompt_manager=MagicMock(),
        llm_service=MagicMock(),
        workflow_orchestrator=MagicMock(),
        neo4j_manager=neo4j_manager,
        memory_service=memory_service,
        obs_service=obs_service,
        xai_service=MagicMock(),
        semantic_router=MagicMock(),
        config_port=MagicMock(),
    )


def test_load_prefs_healthy_graph_returns_context_not_degraded():
    mgr = MagicMock()
    mgr.check_health.return_value = True
    mgr.get_user_preferences_context.return_value = "[Prefs]: likes Naruto."
    svc = _build_service(neo4j_manager=mgr)

    context, degraded = svc._load_user_preferences("u1", "query")

    assert context == "[Prefs]: likes Naruto."
    assert degraded is False


def test_load_prefs_empty_healthy_graph_is_not_degraded():
    # Genuinely no history (graph up, no rows) must NOT be flagged as an outage.
    mgr = MagicMock()
    mgr.check_health.return_value = True
    mgr.get_user_preferences_context.return_value = ""
    svc = _build_service(neo4j_manager=mgr)

    context, degraded = svc._load_user_preferences("u1", "query")

    assert context == ""
    assert degraded is False


def test_load_prefs_graph_down_falls_back_to_vector_memory_and_signals():
    mgr = MagicMock()
    mgr.check_health.return_value = False
    mgr.get_user_preferences_context.return_value = ""  # outage surfaces as empty
    memory = MagicMock()
    memory.retrieve_relevant_memories.return_value = "[Vector memory]: watched Bleach."
    obs = MagicMock()
    svc = _build_service(neo4j_manager=mgr, memory_service=memory, obs_service=obs)

    context, degraded = svc._load_user_preferences("u1", "best shonen?")

    assert degraded is True
    # Fell back to the pgvector memory store for the preference context.
    assert context == "[Vector memory]: watched Bleach."
    memory.retrieve_relevant_memories.assert_called_once_with("u1", "best shonen?")
    # The outage is reported to observability, not swallowed silently.
    assert obs.log_error.called
    err_kwargs = obs.log_error.call_args.kwargs
    assert err_kwargs.get("error_type") == "GraphDegraded"


def test_load_prefs_no_user_or_no_manager_is_noop():
    svc = _build_service(neo4j_manager=None)
    assert svc._load_user_preferences(None, "q") == ("", False)
    assert svc._load_user_preferences("u1", "q") == ("", False)

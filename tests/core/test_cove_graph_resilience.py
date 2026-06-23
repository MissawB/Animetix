"""Neo4j graph-outage resilience for the CoVe oracle.

CoVe verifies claims against the knowledge graph. When the graph is down the
old code either crashed (the adapter call is unguarded) or silently marked
every claim ``context_found=False`` — biasing the verdict toward "unverified".
The resilient version probes health, skips/guards the graph queries on outage,
and records a ``graph_degraded`` flag in the trace.
"""

from unittest.mock import MagicMock

from core.domain.services.cove_oracle_service import CoveOracleService


def _svc(neo4j_manager=None, inference_engine=None, prompt_manager=None):
    return CoveOracleService(
        inference_engine=inference_engine or MagicMock(),
        prompt_manager=prompt_manager or MagicMock(),
        neo4j_manager=neo4j_manager,
    )


# --- _gather_graph_context ---------------------------------------------------


def test_gather_no_manager_returns_empty_not_degraded():
    assert _svc(None)._gather_graph_context(["Naruto"]) == ("", False)


def test_gather_degraded_skips_queries_and_signals():
    mgr = MagicMock()
    mgr.check_health.return_value = False
    context, degraded = _svc(mgr)._gather_graph_context(["Naruto"])
    assert context == ""
    assert degraded is True
    mgr.get_creator_network_context.assert_not_called()


def test_gather_healthy_collects_context():
    mgr = MagicMock()
    mgr.check_health.return_value = True
    mgr.get_creator_network_context.return_value = "Naruto -> Studio Pierrot"
    context, degraded = _svc(mgr)._gather_graph_context(["Naruto"])
    assert "Studio Pierrot" in context
    assert degraded is False


def test_gather_healthy_filters_no_data_sentinel():
    mgr = MagicMock()
    mgr.check_health.return_value = True
    mgr.get_creator_network_context.return_value = "Pas de données pour cette entité"
    context, degraded = _svc(mgr)._gather_graph_context(["Unknown"])
    assert context == ""
    assert degraded is False


def test_gather_query_raising_midway_marks_degraded():
    mgr = MagicMock()
    mgr.check_health.return_value = True  # passes the initial probe...
    mgr.get_creator_network_context.side_effect = RuntimeError("bolt dropped")
    _context, degraded = _svc(mgr)._gather_graph_context(["Naruto"])
    assert degraded is True  # ...but the live query failure is caught


# --- trace_verification records the degraded flag ----------------------------


def _keyed_prompt(key, **kwargs):
    # cove_plan / cove_final return (prompt, system) tuples; others a bare string.
    if key in ("cove_plan", "cove_final"):
        return (f"{key}-prompt", f"{key}-system")
    return f"{key}-prompt"


def test_trace_verification_records_graph_degraded_flag():
    mgr = MagicMock()
    mgr.check_health.return_value = False

    pm = MagicMock()
    pm.get_prompt.side_effect = _keyed_prompt

    def gen(prompt, system_prompt="sys"):
        r = MagicMock()
        if prompt == "cove_plan-prompt":
            r.text = '{"verification_questions": ["Is Naruto a ninja?"]}'
        elif prompt == "cove_entities-prompt":
            r.text = "Naruto"
        else:
            r.text = "some text"
        return r

    engine = MagicMock()
    engine.generate.side_effect = gen

    async def agenerate(prompt, system_prompt="sys", **kwargs):
        return engine.generate(prompt, system_prompt=system_prompt)

    engine.agenerate = agenerate

    trace = _svc(mgr, engine, pm).trace_verification("Is Naruto a ninja?", "Anime")

    assert trace["graph_degraded"] is True
    # Graph queries are skipped while degraded (no false "unverified" bias).
    mgr.get_creator_network_context.assert_not_called()

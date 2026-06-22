"""Behavior tests for the Neo4jManager driver wrapper.

The neo4j ``GraphDatabase`` driver is patched in the module namespace; no real
bolt connection is opened. We provide a fake driver whose ``session()`` is a
context manager exposing:
  * ``run(query, ...)`` -> returns a crafted result (list of record-like objects)
  * ``execute_write(fn, *args)`` -> immediately invokes ``fn(tx, *args)`` with a
    mock ``tx`` (mirroring real Neo4j semantics) so we can assert the exact
    Cypher and parameters the transaction functions build.

Assertions target the REAL Cypher built (including the whitelisted relationship/
label interpolation and the AI_RELATION fallback), the parameters passed, the
parsing of records into the returned strings/lists, and the
``is_safe_read_query`` guard.
"""

from unittest.mock import MagicMock

import pipeline.neo4j_client as nc
import pytest
from pipeline.neo4j_client import Neo4jManager

# --- fakes ---------------------------------------------------------------


class FakeRecord(dict):
    """A neo4j Record stand-in: dict access + ``.data()``."""

    def data(self):
        return dict(self)


class FakeResult(list):
    """Iterable result that also supports ``.single()``."""

    def single(self):
        return self[0] if self else None


class FakeSession:
    def __init__(self, run_results=None):
        # run_results: list consumed FIFO, or a single result reused.
        self._run_results = run_results
        self.run = MagicMock(side_effect=self._run)
        self.executed_writes = []

    def _run(self, query, *args, **kwargs):
        # A *plain* list is a FIFO queue of per-call results. A FakeResult
        # (also a list subclass) is a single result reused for every call,
        # so we must distinguish by exact type, not isinstance.
        if type(self._run_results) is list:
            return self._run_results.pop(0)
        return self._run_results if self._run_results is not None else FakeResult()

    def execute_write(self, fn, *args, **kwargs):
        tx = MagicMock(name="tx")
        self.executed_writes.append(tx)
        return fn(tx, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def make_manager(session):
    """Return a Neo4jManager whose driver is a mock yielding ``session``."""
    mgr = Neo4jManager(uri="bolt://x", user="u", password="p")
    driver = MagicMock(name="driver")
    driver.session.return_value = session
    mgr._driver = driver  # bypass the lazy verify_connectivity property
    return mgr


# --- driver property / connectivity -------------------------------------


def test_driver_property_connects_and_caches(mocker):
    fake_driver = MagicMock()
    gdb = mocker.patch.object(nc, "GraphDatabase")
    gdb.driver.return_value = fake_driver

    mgr = Neo4jManager(uri="bolt://h", user="neo4j", password="pw")
    d = mgr.driver

    assert d is fake_driver
    gdb.driver.assert_called_once_with(
        "bolt://h",
        auth=("neo4j", "pw"),
        connection_timeout=5.0,
        max_transaction_retry_time=10.0,
    )
    fake_driver.verify_connectivity.assert_called_once()
    # Cached: a second access does not reconnect.
    assert mgr.driver is fake_driver
    gdb.driver.assert_called_once()


def test_driver_property_returns_none_on_failure(mocker):
    gdb = mocker.patch.object(nc, "GraphDatabase")
    gdb.driver.side_effect = RuntimeError("refused")
    mgr = Neo4jManager()
    assert mgr.driver is None


def test_methods_noop_without_driver(mocker):
    # Force the lazy ``driver`` property to None deterministically. Setting
    # ``_driver = None`` alone is not enough: the property reconnects on access,
    # so on a host where Neo4j IS reachable (e.g. CI) the methods would run for
    # real instead of no-op'ing. Patching the property guarantees "no driver".
    mocker.patch.object(Neo4jManager, "driver", new=None)
    mgr = Neo4jManager()
    # All write/read paths short-circuit and never raise when driver is None.
    assert mgr.sync_media_to_graph({"id": 1}, "Anime") is None
    assert mgr.sync_character_to_graph({"id": 1}) is None
    assert mgr.sync_ai_extracted_graph("1", {"entities": []}) is None
    assert mgr.sync_combat_lore("1", [{}]) is None
    assert mgr.sync_saga("S", "sum", ["1"]) is None
    assert mgr.sync_fan_theory("S", {}) is None
    assert mgr.find_logical_connections("1") == []
    assert mgr.get_community_summary("Studio", "X") == ""
    assert mgr.multi_hop_traversal("n", ["HAS_THEME"]) == ""
    assert mgr.get_studio_trends("S") == ""
    assert mgr.get_creator_network_context("P") == ""
    assert mgr.get_enriched_context(["1"]) == ""
    assert mgr.execute_read("MATCH (n) RETURN n") == []
    assert mgr.execute_query("MATCH (n) RETURN n") == []


def test_close_calls_driver_close():
    sess = FakeSession()
    mgr = make_manager(sess)
    mgr.close()
    mgr.driver.close.assert_called_once()


# --- sync_media_to_graph (_sync_tx) -------------------------------------


def test_sync_media_builds_media_studio_theme_author_cypher():
    sess = FakeSession()
    mgr = make_manager(sess)
    item = {
        "id": 7,
        "title": "Naruto",
        "year": 2002,
        "studios": ["Pierrot"],
        "micro_tags": ["ninja"],
        "graph_nodes": {"author": "Kishimoto"},
    }
    mgr.sync_media_to_graph(item, "Anime")

    tx = sess.executed_writes[0]
    queries = [c.args[0] for c in tx.run.call_args_list]
    # Root MERGE on Media with id/type and SET title/year.
    assert "MERGE (m:Media {id: $id, type: $type})" in queries[0]
    assert tx.run.call_args_list[0].kwargs == {
        "id": "7",
        "type": "Anime",
        "title": "Naruto",
        "year": 2002,
    }
    # Studio, theme and author relationships each issue their own tx.run.
    assert any("PRODUCED_BY" in q for q in queries)
    assert any("HAS_THEME" in q for q in queries)
    assert any("CREATED_BY" in q for q in queries)


def test_sync_media_director_used_when_no_author():
    sess = FakeSession()
    mgr = make_manager(sess)
    mgr.sync_media_to_graph(
        {"id": 1, "title": "Film", "graph_nodes": {"director": "Miyazaki"}}, "Movie"
    )
    tx = sess.executed_writes[0]
    author_calls = [c for c in tx.run.call_args_list if "CREATED_BY" in c.args[0]]
    assert author_calls[0].kwargs["author_name"] == "Miyazaki"


# --- sync_character_to_graph (_sync_character_tx) ------------------------


def test_sync_character_merges_and_links_appearances():
    sess = FakeSession()
    mgr = make_manager(sess)
    mgr.sync_character_to_graph({"id": 99, "name": "Goku", "anime_appearances": [3, 4]})
    tx = sess.executed_writes[0]
    first = tx.run.call_args_list[0]
    assert "MERGE (c:Character {id: $id})" in first.args[0]
    assert first.kwargs == {"id": "99", "name": "Goku"}
    # One APPEARS_IN link per appearance id.
    links = [c for c in tx.run.call_args_list if "APPEARS_IN" in c.args[0]]
    assert [c.kwargs["mid"] for c in links] == ["3", "4"]


# --- sync_ai_extracted_graph (entity / relation / link txs) -------------


def test_sync_ai_extracted_graph_entities_relations_and_link():
    sess = FakeSession()
    mgr = make_manager(sess)
    data = {
        "entities": [{"name": "Konoha", "type": "Place", "description": "village"}],
        "relations": [{"type": "FEATURES", "source": "Konoha", "target": "Naruto"}],
    }
    mgr.sync_ai_extracted_graph("55", data)

    # 3 execute_write calls: entity, relation, link-to-parent.
    assert len(sess.executed_writes) == 3
    ent_q = sess.executed_writes[0].run.call_args.args[0]
    assert "MERGE (e:Entity {name: $name})" in ent_q
    assert sess.executed_writes[0].run.call_args.kwargs["type"] == "Place"

    rel_call = sess.executed_writes[1].run.call_args
    # Whitelisted relation interpolated literally into the query.
    assert "[r:FEATURES]" in rel_call.args[0]
    assert rel_call.kwargs == {"source": "Konoha", "target": "Naruto"}

    link_call = sess.executed_writes[2].run.call_args
    assert "MERGE (m)-[:FEATURES]->(e)" in link_call.args[0]
    assert link_call.kwargs == {"m_id": "55", "e_name": "Konoha"}


def test_create_relation_falls_back_to_ai_relation_for_unknown_type():
    sess = FakeSession()
    mgr = make_manager(sess)
    mgr.sync_ai_extracted_graph(
        "1",
        {
            "entities": [],
            "relations": [{"type": "loves", "source": "A", "target": "B"}],
        },
    )
    rel_call = sess.executed_writes[0].run.call_args
    # Unknown relation -> generic AI_RELATION carrying the original (un-uppercased)
    # type param; only the whitelist check upper-cases internally.
    assert "[r:AI_RELATION {type: $rel_type}]" in rel_call.args[0]
    assert rel_call.kwargs["rel_type"] == "loves"


# --- sync_combat_lore (_sync_combat_tx) ---------------------------------


def test_sync_combat_lore_builds_combat_event():
    sess = FakeSession()
    mgr = make_manager(sess)
    lore = {
        "character": "Goku",
        "technique": "Kamehameha",
        "timestamp": "12:00",
        "visual_description": "blue beam",
    }
    mgr.sync_combat_lore(404, [lore])

    call = sess.executed_writes[0].run.call_args
    q = call.args[0]
    assert "CREATE (e:CombatEvent" in q
    assert "MERGE (m)-[:CONTAINS_COMBAT]->(e)" in q
    assert call.kwargs == {
        "media_id": "404",
        "character": "Goku",
        "technique": "Kamehameha",
        "timestamp": "12:00",
        "description": "blue beam",
    }


def test_sync_combat_lore_logs_and_continues_on_tx_error():
    sess = FakeSession()
    sess.execute_write = MagicMock(side_effect=RuntimeError("tx fail"))
    mgr = make_manager(sess)
    # Error per-lore is swallowed (logged) — no propagation.
    mgr.sync_combat_lore("1", [{"character": "X"}])


# --- sync_saga ----------------------------------------------------------


def test_sync_saga_builds_unwind_query():
    sess = FakeSession()
    mgr = make_manager(sess)
    mgr.sync_saga("Akatsuki", "summary text", ["1", "2"])

    call = sess.run.call_args
    assert "MERGE (s:Saga {name: $saga_name})" in call.args[0]
    assert "UNWIND $ids as mid" in call.args[0]
    assert call.kwargs == {
        "saga_name": "Akatsuki",
        "summary": "summary text",
        "ids": ["1", "2"],
    }


def test_sync_saga_swallows_error():
    sess = FakeSession()
    sess.run = MagicMock(side_effect=RuntimeError("boom"))
    mgr = make_manager(sess)
    mgr.sync_saga("S", "sum", ["1"])  # no raise


# --- sync_fan_theory (_sync_fan_theory_tx) ------------------------------


def test_sync_fan_theory_builds_query():
    sess = FakeSession()
    mgr = make_manager(sess)
    mgr.sync_fan_theory(
        "OnePiece",
        {
            "title": "Joyboy",
            "description": "d",
            "popularity": 9,
            "plausibility": 7,
            "source_url": "http://x",
        },
    )
    call = sess.executed_writes[0].run.call_args
    assert "MERGE (t:FanTheory {title: $title})" in call.args[0]
    assert call.kwargs["title"] == "Joyboy"
    assert call.kwargs["popularity"] == 9


def test_sync_fan_theory_swallows_error():
    sess = FakeSession()
    sess.execute_write = MagicMock(side_effect=RuntimeError("boom"))
    mgr = make_manager(sess)
    mgr.sync_fan_theory("S", {"title": "T"})


# --- find_logical_connections -------------------------------------------


def test_find_logical_connections_parses_records():
    result = FakeResult(
        [FakeRecord(title="Bleach", strength=3), FakeRecord(title="Naruto", strength=2)]
    )
    sess = FakeSession(run_results=result)
    mgr = make_manager(sess)

    out = mgr.find_logical_connections(7)

    assert sess.run.call_args.kwargs == {"id": "7"}
    assert out == [
        {"title": "Bleach", "strength": 3},
        {"title": "Naruto", "strength": 2},
    ]


# --- get_community_summary ----------------------------------------------


def test_get_community_summary_formats_result():
    res = FakeResult(
        [FakeRecord(total_works=12, top_themes=["a", "b"], key_studios=["S1"])]
    )
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)

    out = mgr.get_community_summary("Studio", "Pierrot")
    # Whitelisted label interpolated; record fields rendered.
    assert "MATCH (cat:Studio {name: $name})" in sess.run.call_args.args[0]
    assert "12 œuvres" in out
    assert "a, b" in out


def test_get_community_summary_empty_when_no_works():
    res = FakeResult([FakeRecord(total_works=0, top_themes=[], key_studios=[])])
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)
    assert "Aucune donnée" in mgr.get_community_summary("Studio", "X")


def test_get_community_summary_rejects_bad_label():
    sess = FakeSession()
    mgr = make_manager(sess)
    with pytest.raises(ValueError):
        mgr.get_community_summary("DROP", "X")


# --- multi_hop_traversal ------------------------------------------------


def test_multi_hop_traversal_builds_rel_chain_and_parses():
    res = FakeResult(
        [
            FakeRecord(name="Goku", type="Character"),
            FakeRecord(name="DBZ", type="Media"),
        ]
    )
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)

    out = mgr.multi_hop_traversal("Akira", ["HAS_THEME", "FEATURES"])
    query = sess.run.call_args.args[0]
    # Two whitelisted rels chained: -[:HAS_THEME]-() -[:FEATURES]-
    assert "-[:HAS_THEME]-() -[:FEATURES]-" in query
    assert "Character: Goku" in out and "Media: DBZ" in out


def test_multi_hop_traversal_no_results_message():
    sess = FakeSession(run_results=FakeResult([]))
    mgr = make_manager(sess)
    out = mgr.multi_hop_traversal("Akira", ["HAS_THEME"])
    assert "n'a mené à aucun résultat" in out


def test_multi_hop_traversal_empty_steps_returns_empty():
    sess = FakeSession()
    mgr = make_manager(sess)
    assert mgr.multi_hop_traversal("Akira", []) == ""


# --- get_studio_trends ---------------------------------------------------


def test_get_studio_trends_formats_themes():
    res = FakeResult(
        [
            FakeRecord(theme="action", weight=5),
            FakeRecord(theme="drama", weight=3),
        ]
    )
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)
    out = mgr.get_studio_trends("Bones", years_back=2)
    assert sess.run.call_args.kwargs == {"name": "Bones", "years": 2}
    assert "action (5)" in out and "drama (3)" in out


def test_get_studio_trends_empty_message():
    sess = FakeSession(run_results=FakeResult([]))
    mgr = make_manager(sess)
    assert "Pas de tendances" in mgr.get_studio_trends("X")


# --- get_creator_network_context ----------------------------------------


def test_get_creator_network_context_formats():
    res = FakeResult([FakeRecord(studio="MAPPA", collab_count=4)])
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)
    out = mgr.get_creator_network_context("Gege")
    assert "MAPPA (4 œuvres)" in out


def test_get_creator_network_context_empty():
    sess = FakeSession(run_results=FakeResult([]))
    mgr = make_manager(sess)
    assert "Pas de données de réseau" in mgr.get_creator_network_context("X")


# --- get_enriched_context -----------------------------------------------


def test_get_enriched_context_builds_parts():
    res = FakeResult(
        [
            FakeRecord(
                title="Naruto",
                studios=["Pierrot"],
                creators=["Kishimoto"],
                themes=["ninja"],
            ),
            FakeRecord(title="Bleach", studios=[], creators=[], themes=[]),
        ]
    )
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)

    out = mgr.get_enriched_context([1, 2])
    # ids coerced to strings.
    assert sess.run.call_args.kwargs == {"ids": ["1", "2"]}
    assert (
        "Oeuvre: Naruto | Studios: Pierrot | Créateurs: Kishimoto | Thèmes: ninja"
        in out
    )
    assert "Oeuvre: Bleach" in out  # second has no extras appended


def test_get_enriched_context_empty_ids():
    sess = FakeSession()
    mgr = make_manager(sess)
    assert mgr.get_enriched_context([]) == ""


# --- verify_claims ------------------------------------------------------


def test_verify_claims_verified_and_unauthorized():
    # First claim uses whitelisted relation -> runs the query.
    sess = FakeSession(run_results=[FakeResult([FakeRecord(verified=True)])])
    mgr = make_manager(sess)
    claims = [
        {"subject": "Naruto", "relation": "features", "object": "Sasuke"},
        {"subject": "X", "relation": "loves", "object": "Y"},  # not whitelisted
    ]
    out = mgr.verify_claims(claims)

    assert out[0]["verified"] is True
    # Whitelisted FEATURES interpolated into the query.
    assert "[:FEATURES]" in sess.run.call_args_list[0].args[0]
    # Unauthorized relation short-circuits with an error flag, no query.
    assert out[1]["verified"] is False
    assert out[1]["error"] == "Unauthorized relation type"
    assert sess.run.call_count == 1


# --- is_safe_read_query / execute_read / execute_query ------------------


@pytest.mark.parametrize(
    "query,safe",
    [
        ("MATCH (n) RETURN n", True),
        ("MATCH (n) DELETE n", False),
        ("CREATE (n)", False),
        ("MATCH (n) SET n.x = 1", False),
        ("CALL db.labels()", False),
        ("LOAD CSV FROM 'x'", False),
    ],
)
def test_is_safe_read_query(query, safe):
    assert Neo4jManager.is_safe_read_query(query) is safe


def test_execute_read_rejects_dangerous_query():
    mgr = Neo4jManager()
    mgr._driver = MagicMock()
    with pytest.raises(ValueError):
        mgr.execute_read("MATCH (n) DELETE n")


def test_execute_read_returns_record_data():
    res = FakeResult([FakeRecord(n=1), FakeRecord(n=2)])
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)
    out = mgr.execute_read("MATCH (n) RETURN n", {"p": 1})
    assert sess.run.call_args.args == ("MATCH (n) RETURN n", {"p": 1})
    assert out == [{"n": 1}, {"n": 2}]


def test_execute_read_swallows_cypher_error():
    sess = FakeSession()
    sess.run = MagicMock(side_effect=RuntimeError("syntax"))
    mgr = make_manager(sess)
    assert mgr.execute_read("MATCH (n) RETURN n") == []


def test_execute_query_returns_record_data():
    res = FakeResult([FakeRecord(x="a")])
    sess = FakeSession(run_results=res)
    mgr = make_manager(sess)
    out = mgr.execute_query("MATCH (n) RETURN n", None)
    # parameters None -> empty dict passed to session.run.
    assert sess.run.call_args.args == ("MATCH (n) RETURN n", {})
    assert out == [{"x": "a"}]


def test_execute_query_swallows_error():
    sess = FakeSession()
    sess.run = MagicMock(side_effect=RuntimeError("boom"))
    mgr = make_manager(sess)
    assert mgr.execute_query("MATCH (n) RETURN n") == []

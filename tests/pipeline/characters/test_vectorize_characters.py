"""Behavior tests for the character multimodal vectorization pipeline.

Covers ``run_vectorization``: missing source DB, up-to-date short-circuit, the
full text + vision embedding/upsert path (asserting the real records and
metadata persisted), per-field branching (popularity dict, affiliations join,
empty image), per-item image-fetch and Neo4j-sync resilience, the
existing-id-per-collection logic, and multi-batch processing.

All external I/O is mocked in the module namespace: the repository, the
embedding models (via models_registry), neo4j_manager, HTTP image fetches, and
PIL image decoding. Real (small) JSON is fed via ``tmp_path``. No real network,
DB, GPU, or model download happens.
"""

import json
from unittest.mock import MagicMock

import numpy as np
import pipeline.characters.vectorize_characters as vc
import pytest


def _item(cid, **over):
    base = {
        "id": cid,
        "name": f"Char {cid}",
        "image": f"http://img/{cid}.jpg",
        "clean_description": f"Vibe of {cid}",
        "popularity": 7,
        "metadata": {"affiliations": ["Survey Corps", "Scouts"]},
    }
    base.update(over)
    return base


class _Encoder:
    def __init__(self, vec=(0.1, 0.2, 0.3)):
        self.vec = list(vec)
        self.calls = []

    def encode(self, inputs, convert_to_numpy=True):
        self.calls.append(list(inputs))
        return np.array([self.vec for _ in inputs])


@pytest.fixture
def repo():
    r = MagicMock()
    r.get_all_ids.return_value = set()
    return r


@pytest.fixture
def resources():
    registry = MagicMock()
    registry.text_model = _Encoder()
    registry.vision_model = _Encoder([0.9, 0.8, 0.7])
    neo4j = MagicMock()
    return registry, neo4j


@pytest.fixture
def wire(mocker, repo, resources):
    registry, neo4j = resources
    mocker.patch.object(vc, "get_repo", return_value=repo)
    mocker.patch.object(vc, "get_pipeline_resources", return_value=(registry, neo4j))
    fake_img = MagicMock(name="PILImage")
    fake_img.convert.return_value = fake_img
    mocker.patch.object(vc.Image, "open", return_value=fake_img)

    def _http_ok(method, url, timeout=5):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\xff\xd8\xff"
        return resp

    http = mocker.patch.object(vc, "safe_http_request", side_effect=_http_ok)
    return {
        "repo": repo,
        "registry": registry,
        "neo4j": neo4j,
        "http": http,
        "fake_img": fake_img,
    }


def _write_db(tmp_path, mocker, items):
    path = tmp_path / "filtered_characters.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    mocker.patch.object(vc, "CLEAN_DB", str(path))
    return path


def _upserts(repo):
    out = {}
    for call in repo.upsert_items.call_args_list:
        coll, ids, embs, metas = call.args
        out[coll] = (ids, embs, metas)
    return out


# --- lazy resource getters ----------------------------------------------


def test_get_repo_returns_container_repository(mocker):
    repo = MagicMock()
    container = MagicMock()
    container.persistence.repository.return_value = repo
    containers = MagicMock()
    containers.get_container.return_value = container
    mocker.patch.dict("sys.modules", {"animetix.containers": containers})
    assert vc.get_repo() is repo


def test_get_pipeline_resources_returns_registry_and_manager(mocker):
    reg_mod = MagicMock()
    neo_mod = MagicMock()
    mocker.patch.dict(
        "sys.modules",
        {
            "pipeline.models_registry": reg_mod,
            "pipeline.neo4j_client": neo_mod,
        },
    )
    registry, manager = vc.get_pipeline_resources()
    assert registry is reg_mod.models_registry
    assert manager is neo_mod.neo4j_manager


# --- missing / up-to-date ------------------------------------------------


def test_missing_clean_db_returns_without_work(mocker, wire, tmp_path):
    mocker.patch.object(vc, "CLEAN_DB", str(tmp_path / "nope.json"))
    vc.run_vectorization()
    wire["repo"].upsert_items.assert_not_called()


def test_all_ids_present_short_circuits(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1), _item(2)])
    wire["repo"].get_all_ids.return_value = {"1", "2"}
    vc.run_vectorization()
    wire["repo"].upsert_items.assert_not_called()
    assert wire["registry"].text_model.calls == []


# --- full multimodal happy path -----------------------------------------


def test_full_path_upserts_text_and_vision(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1)])
    vc.run_vectorization()

    ups = _upserts(wire["repo"])
    assert set(ups) == {"character_vibe", "character_visual_vibe"}

    t_ids, t_embs, t_metas = ups["character_vibe"]
    assert t_ids == ["1"]
    assert t_embs == [[0.1, 0.2, 0.3]]
    assert t_metas[0] == {
        "id": "1",
        "title": "Char 1",
        "image": "http://img/1.jpg",
        "popularity": 7,
        "type": "Character",
        "affiliations": "Survey Corps, Scouts",
    }
    # Text input combines the vibe prefix with the name + description.
    assert wire["registry"].text_model.calls[0] == ["Character Vibe: Char 1. Vibe of 1"]

    v_ids, v_embs, _ = ups["character_visual_vibe"]
    assert v_ids == ["1"]
    assert v_embs == [[0.9, 0.8, 0.7]]
    assert wire["registry"].vision_model.calls[-1] == [wire["fake_img"]]

    wire["neo4j"].sync_character_to_graph.assert_called_once()


def test_popularity_dict_uses_favourites(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1, popularity={"favourites": 999})])
    vc.run_vectorization()
    meta = _upserts(wire["repo"])["character_vibe"][2][0]
    assert meta["popularity"] == 999


def test_missing_affiliations_yields_empty_string(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1, metadata={})])
    vc.run_vectorization()
    meta = _upserts(wire["repo"])["character_vibe"][2][0]
    assert meta["affiliations"] == ""


# --- per-field branching -------------------------------------------------


def test_empty_image_skips_vision_and_http(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1, image="")])
    vc.run_vectorization()
    wire["http"].assert_not_called()
    ups = _upserts(wire["repo"])
    assert "character_visual_vibe" not in ups
    assert ups["character_vibe"][2][0]["image"] == ""


def test_existing_text_id_skips_only_that_collection(mocker, wire, tmp_path):
    """Id present in character_vibe but not visual -> only vision upserted."""

    def get_all_ids(coll):
        return {"1"} if coll == "character_vibe" else set()

    wire["repo"].get_all_ids.side_effect = get_all_ids
    _write_db(tmp_path, mocker, [_item(1)])
    vc.run_vectorization()

    ups = _upserts(wire["repo"])
    assert "character_vibe" not in ups
    assert ups["character_visual_vibe"][0] == ["1"]


def test_existing_vision_id_skips_only_vision(mocker, wire, tmp_path):
    def get_all_ids(coll):
        return {"1"} if coll == "character_visual_vibe" else set()

    wire["repo"].get_all_ids.side_effect = get_all_ids
    _write_db(tmp_path, mocker, [_item(1)])
    vc.run_vectorization()

    ups = _upserts(wire["repo"])
    assert ups["character_vibe"][0] == ["1"]
    assert "character_visual_vibe" not in ups
    wire["http"].assert_not_called()  # no image fetch when vision id exists


# --- resilience ----------------------------------------------------------


def test_non_200_image_skips_vision_only(mocker, wire, tmp_path):
    resp = MagicMock()
    resp.status_code = 404
    wire["http"].side_effect = lambda *a, **k: resp
    _write_db(tmp_path, mocker, [_item(1)])
    vc.run_vectorization()
    ups = _upserts(wire["repo"])
    assert "character_visual_vibe" not in ups
    assert "character_vibe" in ups


def test_image_fetch_exception_swallowed(mocker, wire, tmp_path):
    wire["http"].side_effect = RuntimeError("network down")
    _write_db(tmp_path, mocker, [_item(1)])
    vc.run_vectorization()  # must not raise
    ups = _upserts(wire["repo"])
    assert "character_visual_vibe" not in ups
    assert "character_vibe" in ups


def test_neo4j_sync_exception_swallowed(mocker, wire, tmp_path):
    wire["neo4j"].sync_character_to_graph.side_effect = RuntimeError("graph down")
    _write_db(tmp_path, mocker, [_item(1)])
    vc.run_vectorization()  # must not raise
    assert "character_visual_vibe" in _upserts(wire["repo"])


# --- batching ------------------------------------------------------------


def test_batches_processed_in_chunks(mocker, wire, tmp_path):
    mocker.patch.object(vc, "BATCH_SIZE", 2)
    items = [_item(i) for i in range(1, 6)]  # 5 items -> 3 batches (2,2,1)
    _write_db(tmp_path, mocker, items)
    vc.run_vectorization()

    vibe_calls = [
        c
        for c in wire["repo"].upsert_items.call_args_list
        if c.args[0] == "character_vibe"
    ]
    assert len(vibe_calls) == 3
    all_ids = [i for c in vibe_calls for i in c.args[1]]
    assert all_ids == ["1", "2", "3", "4", "5"]
    assert [len(c.args[1]) for c in vibe_calls] == [2, 2, 1]

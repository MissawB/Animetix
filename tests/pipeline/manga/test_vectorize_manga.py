"""Behavior tests for the manga multimodal vectorization pipeline.

Covers ``run_vectorization``: missing source DB, up-to-date short-circuit, the
full text/plot/vision embedding + upsert path (asserting the real records and
metadata persisted), per-item image-fetch and Neo4j-sync resilience, multi-batch
processing, and the top-level critical-error handler.

All external I/O is mocked: the repository, the embedding models, the pipeline
resources (models_registry / neo4j_manager), HTTP image fetches, and PIL image
decoding. No real network, DB, GPU, or model download happens.
"""

import json
from unittest.mock import MagicMock

import numpy as np
import pipeline.manga.vectorize_manga as vm
import pytest

# --- helpers -------------------------------------------------------------


def _item(mid, **over):
    """Build a clean_root_mangas-style record with sensible defaults."""
    base = {
        "id": mid,
        "title": f"Title {mid}",
        "image": f"http://img/{mid}.jpg",
        "year": 2020,
        "popularity": 5,
        "genres": ["Action", "Drama"],
        "tags": ["dark", "epic"],
        "description": f"Plot of {mid}",
    }
    base.update(over)
    return base


class _Encoder:
    """Deterministic stand-in for a sentence/vision encoder.

    ``encode`` returns a numpy array (one small row per input) so the real
    ``.tolist()`` call in the module is exercised, not mocked away.
    """

    def __init__(self, vec=(0.1, 0.2, 0.3)):
        self.vec = list(vec)
        self.calls = []

    def encode(self, inputs, convert_to_numpy=True):
        self.calls.append(list(inputs))
        return np.array([self.vec for _ in inputs])


@pytest.fixture
def repo():
    r = MagicMock()
    # No existing ids anywhere -> everything is "new" by default.
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
    """Patch the lazy resource getters + module-level I/O collaborators."""
    registry, neo4j = resources
    mocker.patch.object(vm, "get_repo", return_value=repo)
    mocker.patch.object(vm, "get_pipeline_resources", return_value=(registry, neo4j))
    # PIL decode returns a sentinel "image" object; convert() returns itself.
    fake_img = MagicMock(name="PILImage")
    fake_img.convert.return_value = fake_img
    mocker.patch.object(vm.Image, "open", return_value=fake_img)

    def _http_ok(method, url, timeout=2):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\xff\xd8\xff"  # nonempty bytes
        return resp

    http = mocker.patch.object(vm, "safe_http_request", side_effect=_http_ok)
    return {
        "repo": repo,
        "registry": registry,
        "neo4j": neo4j,
        "http": http,
        "fake_img": fake_img,
    }


def _write_db(tmp_path, mocker, items):
    path = tmp_path / "clean_root_mangas.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    mocker.patch.object(vm, "CLEAN_DB", str(path))
    return path


def _upserts(repo):
    """Return {collection: (ids, embeddings, metas)} from repo.upsert_items."""
    out = {}
    for call in repo.upsert_items.call_args_list:
        coll, ids, embs, metas = call.args
        out[coll] = (ids, embs, metas)
    return out


# --- missing / empty input ----------------------------------------------


def test_missing_clean_db_returns_without_work(mocker, wire, tmp_path):
    """No source file -> early return, nothing fetched or upserted."""
    mocker.patch.object(vm, "CLEAN_DB", str(tmp_path / "does_not_exist.json"))
    vm.run_vectorization()
    wire["repo"].upsert_items.assert_not_called()


def test_all_ids_already_present_short_circuits(mocker, wire, tmp_path):
    """When every id exists in all three collections, nothing is processed."""
    _write_db(tmp_path, mocker, [_item(1), _item(2)])
    wire["repo"].get_all_ids.return_value = {"1", "2"}
    vm.run_vectorization()
    wire["repo"].upsert_items.assert_not_called()
    # Models never touched.
    assert wire["registry"].text_model.calls == []


# --- full multimodal happy path -----------------------------------------


def test_full_path_upserts_all_three_collections(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1)])
    vm.run_vectorization()

    ups = _upserts(wire["repo"])
    assert set(ups) == {"manga_thematic", "manga_plot", "manga_visual_vibe"}

    # Thematic record: ids, the .tolist()-ed deterministic embedding, metadata.
    t_ids, t_embs, t_metas = ups["manga_thematic"]
    assert t_ids == ["1"]
    assert t_embs == [[0.1, 0.2, 0.3]]
    meta = t_metas[0]
    assert meta == {
        "id": "1",
        "title": "Title 1",
        "image": "http://img/1.jpg",
        "year": "2020",
        "popularity": 5,
        "type": "Manga",
        "genres": "Action, Drama",
    }

    # Plot collection uses the raw description as its text input.
    p_ids, _, _ = ups["manga_plot"]
    assert p_ids == ["1"]
    assert wire["registry"].text_model.calls[-1] == ["Plot of 1"]

    # Vision collection used the vision encoder's distinct vector.
    v_ids, v_embs, _ = ups["manga_visual_vibe"]
    assert v_ids == ["1"]
    assert v_embs == [[0.9, 0.8, 0.7]]
    # Vision encoder received the decoded PIL image object.
    assert wire["registry"].vision_model.calls[-1] == [wire["fake_img"]]

    # Neo4j sync attempted for the (vision-eligible) item.
    wire["neo4j"].sync_media_to_graph.assert_called_once_with(mocker.ANY, "Manga")


def test_thematic_text_input_combines_tags_genres_description(mocker, wire, tmp_path):
    _write_db(tmp_path, mocker, [_item(1)])
    vm.run_vectorization()
    # First text_model.encode call is the thematic batch.
    thematic_text = wire["registry"].text_model.calls[0][0]
    assert thematic_text == "Manga Themes: dark, epic. Genres: Action, Drama. Plot of 1"


# --- per-field branching -------------------------------------------------


def test_plot_skipped_when_no_description(mocker, wire, tmp_path):
    """Item without a description must not produce a plot record."""
    _write_db(tmp_path, mocker, [_item(1, description="")])
    vm.run_vectorization()
    ups = _upserts(wire["repo"])
    assert "manga_plot" not in ups
    assert "manga_thematic" in ups  # thematic still runs


def test_vision_skipped_when_no_image(mocker, wire, tmp_path):
    """Empty image -> no HTTP fetch, no vision record; meta image is ''."""
    _write_db(tmp_path, mocker, [_item(1, image="")])
    vm.run_vectorization()
    wire["http"].assert_not_called()
    ups = _upserts(wire["repo"])
    assert "manga_visual_vibe" not in ups
    assert ups["manga_thematic"][2][0]["image"] == ""


def test_existing_thematic_id_skips_only_that_collection(mocker, wire, tmp_path):
    """If id present in thematic but not plot/vision, only thematic is skipped."""

    def get_all_ids(coll):
        return {"1"} if coll == "manga_thematic" else set()

    wire["repo"].get_all_ids.side_effect = get_all_ids
    _write_db(tmp_path, mocker, [_item(1)])
    vm.run_vectorization()

    ups = _upserts(wire["repo"])
    assert "manga_thematic" not in ups
    assert ups["manga_plot"][0] == ["1"]
    assert ups["manga_visual_vibe"][0] == ["1"]


def test_year_defaults_to_zeros_when_missing(mocker, wire, tmp_path):
    item = _item(1)
    del item["year"]
    _write_db(tmp_path, mocker, [item])
    vm.run_vectorization()
    meta = _upserts(wire["repo"])["manga_thematic"][2][0]
    assert meta["year"] == "0000"


# --- resilience ----------------------------------------------------------


def test_non_200_image_response_skips_vision_only(mocker, wire, tmp_path):
    resp = MagicMock()
    resp.status_code = 404
    wire["http"].side_effect = lambda *a, **k: resp
    _write_db(tmp_path, mocker, [_item(1)])
    vm.run_vectorization()
    ups = _upserts(wire["repo"])
    assert "manga_visual_vibe" not in ups
    # Text + plot still persisted.
    assert "manga_thematic" in ups and "manga_plot" in ups


def test_image_fetch_exception_is_swallowed(mocker, wire, tmp_path):
    wire["http"].side_effect = RuntimeError("network down")
    _write_db(tmp_path, mocker, [_item(1)])
    vm.run_vectorization()  # must not raise
    ups = _upserts(wire["repo"])
    assert "manga_visual_vibe" not in ups
    assert "manga_thematic" in ups


def test_neo4j_sync_exception_is_swallowed(mocker, wire, tmp_path):
    wire["neo4j"].sync_media_to_graph.side_effect = RuntimeError("graph down")
    _write_db(tmp_path, mocker, [_item(1)])
    vm.run_vectorization()  # must not raise
    # Vision still upserted despite the graph sync failing afterwards.
    assert "manga_visual_vibe" in _upserts(wire["repo"])


def test_critical_error_logged_and_written(mocker, wire, tmp_path):
    """An unexpected failure mid-run is caught, logged, and appended to a file."""
    _write_db(tmp_path, mocker, [_item(1)])
    # Make the very first upsert blow up.
    wire["repo"].upsert_items.side_effect = ValueError("boom")
    logged = mocker.patch.object(vm.logger, "error")
    written = []
    real_open = open

    def fake_open(path, *a, **k):
        if "manga_vectorize_error.log" in str(path):
            f = MagicMock()
            f.__enter__.return_value = f
            f.write.side_effect = lambda s: written.append(s)
            return f
        return real_open(path, *a, **k)

    mocker.patch("builtins.open", side_effect=fake_open)

    vm.run_vectorization()  # swallowed by the except block

    assert logged.called
    assert any("CRITICAL ERROR" in s and "boom" in s for s in written)


# --- batching ------------------------------------------------------------


def test_batches_processed_in_chunks(mocker, wire, tmp_path):
    """With > BATCH_SIZE items, each collection is upserted once per batch."""
    mocker.patch.object(vm, "BATCH_SIZE", 2)
    items = [_item(i) for i in range(1, 6)]  # 5 items -> 3 batches (2,2,1)
    _write_db(tmp_path, mocker, items)
    vm.run_vectorization()

    thematic_calls = [
        c
        for c in wire["repo"].upsert_items.call_args_list
        if c.args[0] == "manga_thematic"
    ]
    assert len(thematic_calls) == 3
    # Batch sizes for thematic ids: 2, 2, 1 and all five ids covered in order.
    all_ids = [i for c in thematic_calls for i in c.args[1]]
    assert all_ids == ["1", "2", "3", "4", "5"]
    assert [len(c.args[1]) for c in thematic_calls] == [2, 2, 1]

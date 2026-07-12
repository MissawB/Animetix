"""Regression tests for the anime vectorization pipeline's item cap and paths.

Two bugs, both preventing a real catalog backfill:

1. ``vectorize_anime.py`` hardcoded ``items[:100]`` ("On limite pour la démo"),
   so no more than the first 100 catalog items could ever be vectorized,
   however large the real catalog (44k+ items) is. Fixed by a ``--limit`` CLI
   argument (argparse) that defaults to ``None`` == "process everything".

2. ``BASE_DIR`` was computed with one dirname() too few, landing on
   ``backend/`` instead of the repo root, so ``INPUT_FILE`` resolved to
   ``backend/data/processed/...`` -- a path that does not exist. `data/`
   lives at the repo root, one level above ``backend/``.

All external I/O (repository, embedding models, HTTP image fetches, Neo4j)
is mocked -- no real network, DB, GPU, or model download happens.
"""

import json
import os
from unittest.mock import MagicMock

import numpy as np
import pipeline.anime.vectorize_anime as va
import pytest


def _item(item_id, **overrides):
    base = {
        "id": item_id,
        "title": f"Title {item_id}",
        "description": f"Plot of {item_id}",
    }
    base.update(overrides)
    return base


class _Encoder:
    def __init__(self, vec=(0.1, 0.2, 0.3)):
        self.vec = list(vec)
        self.calls = []

    def encode(self, inputs, convert_to_numpy=True):
        self.calls.append(inputs if isinstance(inputs, list) else [inputs])
        n = len(inputs) if isinstance(inputs, list) else 1
        return np.array([self.vec for _ in range(n)])


@pytest.fixture
def repo():
    return MagicMock()


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
    mocker.patch.object(va, "get_repo", return_value=repo)
    mocker.patch.object(va, "get_pipeline_resources", return_value=(registry, neo4j))
    return {"repo": repo, "registry": registry, "neo4j": neo4j}


def _write_db(tmp_path, mocker, items):
    path = tmp_path / "clean_root_animes.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    mocker.patch.object(va, "INPUT_FILE", str(path))
    return path


def _thematic_ids(repo):
    ids = []
    for call in repo.upsert_items.call_args_list:
        if call.args[0] == "anime_thematic":
            ids.extend(call.args[1])
    return ids


# --- BASE_DIR / INPUT_FILE path resolution -------------------------------


def test_input_file_resolves_under_repo_root_not_backend():
    """`data/` lives at the repo root; it must never be nested under backend/."""
    parts = os.path.normpath(va.INPUT_FILE).split(os.sep)
    assert "backend" not in parts
    assert parts[-3:] == ["data", "processed", "clean_root_animes.json"]


def test_project_root_is_one_level_above_backend_dir():
    assert os.path.basename(va.BACKEND_DIR) == "backend"
    assert va.PROJECT_ROOT == os.path.dirname(va.BACKEND_DIR)


# --- --limit CLI argument --------------------------------------------------


def test_limit_argument_defaults_to_none(monkeypatch):
    monkeypatch.setattr("sys.argv", ["vectorize_anime.py"])
    args = va._parse_args()
    assert args.limit is None


def test_limit_argument_parses_value(monkeypatch):
    monkeypatch.setattr("sys.argv", ["vectorize_anime.py", "--limit", "7"])
    args = va._parse_args()
    assert args.limit == 7


# --- run_vectorization honours (or ignores) the limit ---------------------


def test_no_limit_processes_every_item(mocker, wire, tmp_path):
    """Absence of --limit must mean "everything", not the old hardcoded 100."""
    items = [_item(i) for i in range(1, 151)]  # more than the old demo cap
    _write_db(tmp_path, mocker, items)

    va.run_vectorization(limit=None)

    ids = _thematic_ids(wire["repo"])
    assert len(ids) == 150
    assert ids == [str(i) for i in range(1, 151)]


def test_limit_caps_number_of_processed_items(mocker, wire, tmp_path):
    items = [_item(i) for i in range(1, 11)]
    _write_db(tmp_path, mocker, items)

    va.run_vectorization(limit=3)

    ids = _thematic_ids(wire["repo"])
    assert ids == ["1", "2", "3"]


def test_default_call_with_no_limit_kwarg_processes_everything(mocker, wire, tmp_path):
    """Calling run_vectorization() with no arguments at all (as __main__ used to
    do implicitly) must also mean "everything", matching the new --limit default.
    """
    items = [_item(i) for i in range(1, 6)]
    _write_db(tmp_path, mocker, items)

    va.run_vectorization()

    ids = _thematic_ids(wire["repo"])
    assert ids == ["1", "2", "3", "4", "5"]

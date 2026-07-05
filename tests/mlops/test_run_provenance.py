"""Tests du helper de provenance des runs MLOps."""

import json

from pipeline.mlops import run_provenance


def test_get_git_commit_respects_env(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "deadbeef1234")
    assert run_provenance.get_git_commit() == "deadbeef1234"


def test_get_git_commit_returns_string_without_env(monkeypatch):
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    commit = run_provenance.get_git_commit()
    assert isinstance(commit, str) and commit  # SHA réel ou "unknown"


def test_get_registry_revisions_resolves_from_central_registry():
    # Les révisions viennent désormais du registre central (model_registry),
    # plus du manifest supprimé. Forme attendue : {kind: {version: {id, revision}}}.
    data = run_provenance.get_registry_revisions()
    assert data["text"]["v3"] == {
        "id": "jinaai/jina-embeddings-v3",
        "revision": "ab036b023d30b4d1138c4c3bfa9f0c445ab455d6",
    }
    assert data["vision"]["v2"]["id"] == "google/siglip2-so400m-patch14-384"
    for versions in data.values():
        for entry in versions.values():
            assert entry["id"] and entry["revision"]


def test_build_provenance_shape(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "cafe")
    prov = run_provenance.build_provenance(model_base="Qwen", dataset="ds.jsonl")
    assert prov["git_commit"] == "cafe"
    assert isinstance(prov["timestamp_utc"], str) and "T" in prov["timestamp_utc"]
    assert isinstance(prov["base_models"], dict)
    assert prov["model_base"] == "Qwen"
    assert prov["dataset"] == "ds.jsonl"


def test_write_run_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "feedface")
    out = tmp_path / "adapter"
    prov = run_provenance.write_run_metadata(out, model_base="Qwen")
    written = json.loads((out / "run_metadata.json").read_text(encoding="utf-8"))
    assert written == prov
    assert written["git_commit"] == "feedface"
    assert written["model_base"] == "Qwen"

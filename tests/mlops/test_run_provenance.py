"""Tests du helper de provenance des runs MLOps."""

import json

from backend.pipeline.mlops import run_provenance


def test_get_git_commit_respects_env(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "deadbeef1234")
    assert run_provenance.get_git_commit() == "deadbeef1234"


def test_get_git_commit_returns_string_without_env(monkeypatch):
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    commit = run_provenance.get_git_commit()
    assert isinstance(commit, str) and commit  # SHA réel ou "unknown"


def test_get_manifest_revisions_reads_file(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"llm": {"v3": {"revision": "abc"}}}))
    data = run_provenance.get_manifest_revisions(manifest)
    assert data["llm"]["v3"]["revision"] == "abc"


def test_get_manifest_revisions_missing_returns_empty(tmp_path):
    assert run_provenance.get_manifest_revisions(tmp_path / "nope.json") == {}


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

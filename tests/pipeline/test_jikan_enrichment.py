"""Behavior tests for the Jikan enrichment pipeline.

Covers the resilient HTTP fetch helpers (200 / non-200 / exception / 429 retry),
the media enrichment transform + idempotent file I/O, and the character no-op.
All network and sleeps are mocked — no real I/O.
"""

import json
from unittest.mock import MagicMock

import pipeline.jikan_enrichment as jk


def _resp(status, payload):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    return r


# --- fetch_jikan_details -------------------------------------------------


def test_fetch_details_returns_data_on_200(mocker):
    mocker.patch.object(
        jk, "safe_http_request", return_value=_resp(200, {"data": {"synopsis": "x"}})
    )
    assert jk.fetch_jikan_details(1, "anime") == {"synopsis": "x"}


def test_fetch_details_empty_on_non_200(mocker):
    mocker.patch.object(jk, "safe_http_request", return_value=_resp(404, {}))
    assert jk.fetch_jikan_details(1) == {}


def test_fetch_details_empty_on_exception(mocker):
    mocker.patch.object(jk, "safe_http_request", side_effect=RuntimeError("boom"))
    assert jk.fetch_jikan_details(1) == {}


def test_fetch_details_retries_on_429(mocker):
    mocker.patch("time.sleep")  # no real wait
    mocker.patch.object(
        jk,
        "safe_http_request",
        side_effect=[_resp(429, {}), _resp(200, {"data": {"ok": 1}})],
    )
    assert jk.fetch_jikan_details(1) == {"ok": 1}


# --- fetch_jikan_recommendations ----------------------------------------


def test_fetch_recommendations_returns_list(mocker):
    recs = [{"entry": {"title": "A"}, "content": "c"}]
    mocker.patch.object(
        jk, "safe_http_request", return_value=_resp(200, {"data": recs})
    )
    assert jk.fetch_jikan_recommendations(1) == recs


def test_fetch_recommendations_empty_on_error(mocker):
    mocker.patch.object(jk, "safe_http_request", side_effect=ValueError)
    assert jk.fetch_jikan_recommendations(1) == []


# --- enrich_media --------------------------------------------------------


def test_enrich_media_skips_when_input_missing(tmp_path):
    out = tmp_path / "out.json"
    jk.enrich_media(str(tmp_path / "missing.json"), str(out), "anime")
    assert not out.exists()


def test_enrich_media_transforms_and_writes(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    # Items: one valid, one with null idMal, one without idMal (both skipped).
    inp.write_text(
        json.dumps([{"idMal": 42}, {"idMal": None}, {"foo": 1}]), encoding="utf-8"
    )
    mocker.patch.object(
        jk,
        "fetch_jikan_details",
        return_value={
            "synopsis": "S",
            "titles": [{"title": "Alt"}, {"nope": 1}],
            "background": "BG",
            "themes": [{"name": "Action"}, {"x": 1}],
        },
    )
    mocker.patch.object(
        jk,
        "fetch_jikan_recommendations",
        return_value=[
            {"entry": {"title": "Rec1"}, "content": "good"},
            {"entry": {}},  # no content -> "" (the KeyError it guards against)
        ],
    )
    mocker.patch("time.sleep")

    jk.enrich_media(str(inp), str(out), "anime")

    data = json.loads(out.read_text(encoding="utf-8"))
    assert list(data.keys()) == ["42"]  # null / missing idMal skipped
    entry = data["42"]
    assert entry["synopsis_en"] == "S"
    assert entry["synopsis_fr"] is None
    assert entry["alternative_titles"] == ["Alt"]
    assert entry["background"] == "BG"
    assert entry["themes"] == ["Action"]
    assert entry["recommendations"] == [
        {"title": "Rec1", "content": "good"},
        {"title": "Unknown", "content": ""},
    ]


def test_enrich_media_skips_already_enriched(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(json.dumps([{"idMal": 7}]), encoding="utf-8")
    out.write_text(json.dumps({"7": {"existing": True}}), encoding="utf-8")
    details = mocker.patch.object(jk, "fetch_jikan_details")
    mocker.patch("time.sleep")

    jk.enrich_media(str(inp), str(out), "anime")

    details.assert_not_called()  # already present -> no fetch
    assert json.loads(out.read_text(encoding="utf-8")) == {"7": {"existing": True}}


# --- enrich_characters (currently a no-op) -------------------------------


def test_enrich_characters_returns_early_when_missing(tmp_path):
    # No exception, no output written.
    jk.enrich_characters(str(tmp_path / "missing.json"), str(tmp_path / "out.json"))


def test_enrich_characters_completes_noop(tmp_path):
    inp = tmp_path / "chars.json"
    inp.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    # The loop is intentionally a no-op for now; just assert it runs cleanly.
    jk.enrich_characters(str(inp), str(tmp_path / "out.json"))

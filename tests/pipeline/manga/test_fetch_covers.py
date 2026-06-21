"""Behavior tests for the manga cover-fetching pipeline.

Covers MAL->MangaDex id mapping (hit / no-mangadex / non-200 / exception),
cover extraction + locale filtering (ja/fr only, missing fileName skipped,
non-200 / exception resilience), and the orchestrator run_fetching
(missing input, idMal skip, already-present skip, transform + file write).
All network and sleeps are mocked — no real I/O.
"""

import json
from unittest.mock import MagicMock

import pipeline.manga.fetch_covers as fc


def _resp(status, payload):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    return r


# --- get_mangadex_id -----------------------------------------------------


def test_get_mangadex_id_returns_first_key_on_200(mocker):
    payload = {"Sites": {"Mangadex": {"uuid-1": {"x": 1}, "uuid-2": {"y": 2}}}}
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(200, payload))
    assert fc.get_mangadex_id(123) == "uuid-1"


def test_get_mangadex_id_none_when_no_mangadex_entry(mocker):
    payload = {"Sites": {"OtherSite": {"a": 1}}}
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(200, payload))
    assert fc.get_mangadex_id(123) is None


def test_get_mangadex_id_none_on_non_200(mocker):
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(404, {}))
    assert fc.get_mangadex_id(123) is None


def test_get_mangadex_id_none_on_exception(mocker):
    mocker.patch.object(fc, "safe_http_request", side_effect=RuntimeError("boom"))
    assert fc.get_mangadex_id(123) is None


# --- fetch_covers --------------------------------------------------------


def test_fetch_covers_extracts_ja_and_fr(mocker):
    data = {
        "data": [
            {"attributes": {"locale": "ja", "fileName": "j1.jpg", "volume": "1"}},
            {"attributes": {"locale": "fr", "fileName": "f1.jpg", "volume": "2"}},
        ]
    }
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(200, data))
    covers = fc.fetch_covers("MD-UUID")
    assert covers == {
        "ja": [
            {
                "url": "https://uploads.mangadex.org/covers/MD-UUID/j1.jpg",
                "volume": "1",
            }
        ],
        "fr": [
            {
                "url": "https://uploads.mangadex.org/covers/MD-UUID/f1.jpg",
                "volume": "2",
            }
        ],
    }


def test_fetch_covers_filters_other_locales_and_missing_filename(mocker):
    data = {
        "data": [
            {"attributes": {"locale": "en", "fileName": "e1.jpg", "volume": "1"}},
            {"attributes": {"locale": "ja", "fileName": None, "volume": "3"}},
            {"attributes": {"locale": "fr", "fileName": "f1.jpg", "volume": None}},
        ]
    }
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(200, data))
    covers = fc.fetch_covers("X")
    assert covers["ja"] == []  # missing fileName skipped
    assert covers["fr"] == [
        {"url": "https://uploads.mangadex.org/covers/X/f1.jpg", "volume": None}
    ]


def test_fetch_covers_empty_on_non_200(mocker):
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(500, {}))
    assert fc.fetch_covers("X") == {"ja": [], "fr": []}


def test_fetch_covers_empty_on_exception(mocker):
    mocker.patch.object(fc, "safe_http_request", side_effect=ValueError("down"))
    assert fc.fetch_covers("X") == {"ja": [], "fr": []}


# --- run_fetching --------------------------------------------------------


def test_run_fetching_missing_input_file(tmp_path, mocker):
    missing = tmp_path / "missing.json"
    mocker.patch.object(fc, "INPUT_FILE", str(missing))
    result = fc.run_fetching()
    assert result.startswith("❌ Input file not found")


def test_run_fetching_processes_and_writes(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "nested" / "out.json"  # parent created via os.makedirs
    inp.write_text(
        json.dumps(
            [
                {"id": 10, "idMal": 42, "title": "Berserk"},
                {"id": 11, "title": "NoMal"},  # no idMal -> skipped
            ]
        ),
        encoding="utf-8",
    )
    mocker.patch.object(fc, "INPUT_FILE", str(inp))
    mocker.patch.object(fc, "OUTPUT_FILE", str(out))
    mocker.patch.object(fc, "get_mangadex_id", return_value="MD-42")
    mocker.patch.object(
        fc,
        "fetch_covers",
        return_value={"ja": [{"url": "u", "volume": "1"}], "fr": []},
    )
    mocker.patch("time.sleep")

    result = fc.run_fetching(limit=10)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert list(written.keys()) == ["10"]  # idMal-less manga skipped
    assert written["10"] == {
        "title": "Berserk",
        "mangadex_id": "MD-42",
        "covers": {"ja": [{"url": "u", "volume": "1"}], "fr": []},
    }
    assert result == "✅ Finished! Added covers for 1 mangas. Total in DB: 1"


def test_run_fetching_skips_when_no_covers_found(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": 5, "idMal": 99, "title": "Empty"}]), encoding="utf-8"
    )
    mocker.patch.object(fc, "INPUT_FILE", str(inp))
    mocker.patch.object(fc, "OUTPUT_FILE", str(out))
    mocker.patch.object(fc, "get_mangadex_id", return_value="MD-99")
    mocker.patch.object(fc, "fetch_covers", return_value={"ja": [], "fr": []})
    mocker.patch("time.sleep")

    result = fc.run_fetching(limit=10)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == {}  # nothing added because no covers
    assert result == "✅ Finished! Added covers for 0 mangas. Total in DB: 0"


def test_run_fetching_skips_already_present(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": 7, "idMal": 70, "title": "Done"}]), encoding="utf-8"
    )
    out.write_text(json.dumps({"7": {"existing": True}}), encoding="utf-8")
    mocker.patch.object(fc, "INPUT_FILE", str(inp))
    mocker.patch.object(fc, "OUTPUT_FILE", str(out))
    get_id = mocker.patch.object(fc, "get_mangadex_id")
    mocker.patch("time.sleep")

    result = fc.run_fetching(limit=10)

    get_id.assert_not_called()  # already in covers_data -> no fetch
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == {"7": {"existing": True}}  # preserved, not overwritten
    # already-present manga still counts toward `processed`, none added.
    assert result == "✅ Finished! Added covers for 0 mangas. Total in DB: 1"


def test_run_fetching_tolerates_corrupt_existing_output(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": 3, "idMal": 30, "title": "Resilient"}]), encoding="utf-8"
    )
    out.write_text("{ not valid json", encoding="utf-8")  # triggers load except branch
    mocker.patch.object(fc, "INPUT_FILE", str(inp))
    mocker.patch.object(fc, "OUTPUT_FILE", str(out))
    mocker.patch.object(fc, "get_mangadex_id", return_value="MD-30")
    mocker.patch.object(
        fc,
        "fetch_covers",
        return_value={"ja": [{"url": "u", "volume": None}], "fr": []},
    )
    mocker.patch("time.sleep")

    result = fc.run_fetching(limit=10)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert "3" in written  # corrupt cache discarded, fresh run succeeds
    assert result == "✅ Finished! Added covers for 1 mangas. Total in DB: 1"


def test_run_fetching_respects_limit(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": i, "idMal": 100 + i, "title": f"M{i}"} for i in range(5)]),
        encoding="utf-8",
    )
    mocker.patch.object(fc, "INPUT_FILE", str(inp))
    mocker.patch.object(fc, "OUTPUT_FILE", str(out))
    get_id = mocker.patch.object(fc, "get_mangadex_id", return_value="MD")
    mocker.patch.object(
        fc, "fetch_covers", return_value={"ja": [{"url": "u", "volume": "1"}], "fr": []}
    )
    mocker.patch("time.sleep")

    result = fc.run_fetching(limit=2)

    # Only 2 mangas processed despite 5 in input.
    assert get_id.call_count == 2
    written = json.loads(out.read_text(encoding="utf-8"))
    assert len(written) == 2
    assert result == "✅ Finished! Added covers for 2 mangas. Total in DB: 2"

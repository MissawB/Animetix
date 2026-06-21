"""Behavior tests for the AniList manga ingestion pipeline.

Covers the resilient GraphQL fetch helper (200 / non-200 / exception) and the
incremental ``run_ingestion`` driver: cold start, incremental dedup against an
existing file, multi-page pagination, error-driven early stop, the "no new
items" no-write branch, and resilience to a corrupt existing file.

All network, sleeps and filesystem writes are mocked / redirected — no real I/O.
"""

import json
from unittest.mock import MagicMock, mock_open

import pipeline.manga.ingest_manga as im


def _resp(status, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload if payload is not None else {}
    return r


def _media(idx, has_next):
    """Build one valid AniList GraphQL page payload with given media ids."""
    return {
        "data": {
            "Page": {
                "pageInfo": {"hasNextPage": has_next},
                "media": [{"id": i} for i in idx],
            }
        }
    }


# --- fetch_page ----------------------------------------------------------


def test_fetch_page_returns_json_on_200(mocker):
    payload = {"data": {"Page": {"media": []}}}
    http = mocker.patch.object(
        im, "safe_http_request", return_value=_resp(200, payload)
    )
    assert im.fetch_page(3) == payload
    # Verify the real request shape: POST to AniList with page var threaded through.
    args, kwargs = http.call_args
    assert args[0] == "POST"
    assert args[1] == im.url
    assert kwargs["json"]["variables"] == {"page": 3, "perPage": 50}
    assert kwargs["json"]["query"] == im.query


def test_fetch_page_returns_none_on_non_200(mocker):
    mocker.patch.object(im, "safe_http_request", return_value=_resp(500))
    assert im.fetch_page(1) is None


def test_fetch_page_returns_none_on_exception(mocker):
    mocker.patch.object(im, "safe_http_request", side_effect=RuntimeError("boom"))
    assert im.fetch_page(1) is None


# --- run_ingestion: cold start (no existing file) ------------------------


def test_run_ingestion_cold_start_writes_all_new(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")
    # Single page, then stop.
    mocker.patch.object(
        im, "fetch_page", return_value=_media([1, 2, 3], has_next=False)
    )

    im.run_ingestion()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert [m["id"] for m in data] == [1, 2, 3]


# --- run_ingestion: incremental dedup vs existing file -------------------


def test_run_ingestion_incremental_appends_only_new(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    out.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")
    # Page returns ids 2 (dup) and 3 (new).
    mocker.patch.object(im, "fetch_page", return_value=_media([2, 3], has_next=False))

    im.run_ingestion()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert [m["id"] for m in data] == [1, 2, 3]  # only id 3 appended, order preserved


# --- run_ingestion: multi-page pagination --------------------------------


def test_run_ingestion_paginates_until_no_next_page(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    sleep = mocker.patch("time.sleep")
    fetch = mocker.patch.object(
        im,
        "fetch_page",
        side_effect=[
            _media([1, 2], has_next=True),
            _media([3, 4], has_next=False),
        ],
    )

    im.run_ingestion()

    assert fetch.call_count == 2
    assert [c.args[0] for c in fetch.call_args_list] == [1, 2]  # pages 1 then 2
    sleep.assert_called_with(0.7)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert [m["id"] for m in data] == [1, 2, 3, 4]


# --- run_ingestion: error / empty data stops early -----------------------


def test_run_ingestion_stops_on_fetch_error(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")
    # First page OK, second returns None (error) -> loop breaks.
    fetch = mocker.patch.object(
        im,
        "fetch_page",
        side_effect=[_media([1], has_next=True), None],
    )

    im.run_ingestion()

    assert fetch.call_count == 2
    data = json.loads(out.read_text(encoding="utf-8"))
    assert [m["id"] for m in data] == [1]  # page-1 data persisted before the break


def test_run_ingestion_stops_on_malformed_payload(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")
    # Payload missing "Page" -> treated as error, loop breaks, nothing new added.
    mocker.patch.object(im, "fetch_page", return_value={"data": {}})

    im.run_ingestion()

    assert not out.exists()  # no new items -> no write


# --- run_ingestion: no new items -> no write -----------------------------


def test_run_ingestion_no_new_items_does_not_write(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    out.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")
    mocker.patch.object(im, "fetch_page", return_value=_media([1, 2], has_next=False))
    makedirs = mocker.patch("os.makedirs")
    # Use a write-detecting open: if it writes, content changes.
    m = mock_open(read_data=json.dumps([{"id": 1}, {"id": 2}]))
    mocker.patch("builtins.open", m)

    im.run_ingestion()

    makedirs.assert_not_called()  # save branch skipped entirely
    handle = m()
    handle.write.assert_not_called()  # nothing written when no new items


# --- run_ingestion: corrupt existing file is tolerated -------------------


def test_run_ingestion_tolerates_corrupt_existing_file(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    out.write_text("{ not valid json", encoding="utf-8")
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")
    mocker.patch.object(im, "fetch_page", return_value=_media([10, 11], has_next=False))

    im.run_ingestion()  # must not raise despite the unreadable existing file

    data = json.loads(out.read_text(encoding="utf-8"))
    assert [m["id"] for m in data] == [10, 11]  # starts fresh, writes new items


# --- run_ingestion: max_pages cap stops the loop -------------------------


def test_run_ingestion_respects_max_pages_cap(tmp_path, mocker):
    out = tmp_path / "raw_manga_db.json"
    mocker.patch.object(im, "OUTPUT_FILE", str(out))
    mocker.patch("time.sleep")

    # The feed always reports hasNextPage=True; only the module's max_pages=100
    # local literal can terminate the loop. Each page yields a unique new id.
    calls = {"n": 0}

    def _capped(page):
        calls["n"] += 1
        # id is unique per page so every page adds exactly one new item.
        return _media([page], has_next=True)

    mocker.patch.object(im, "fetch_page", side_effect=_capped)

    im.run_ingestion()

    # max_pages is 100 -> exactly 100 fetches before the cap stops the loop.
    assert calls["n"] == 100
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 100

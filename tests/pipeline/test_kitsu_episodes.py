# tests/pipeline/test_kitsu_episodes.py
"""Kitsu is the substitute for plot data no other source structures. The two pure
transforms below are what the network layer feeds; they must never invent an
episode and never keep an empty one.

The network-layer tests below pin two correctness properties that a rerun's
idempotency depends on:
  - a failed page must never be mistaken for a short final page (it must abort
    the whole work, not persist a truncated episode list); and
  - a work with no Kitsu mapping is a legitimate empty result, not an error.
"""

import importlib
import json

import pytest

kitsu = importlib.import_module("pipeline.anime.fetch_kitsu_episodes")


class FakeResponse:
    """Stand-in for the httpx.Response that safe_http_request returns."""

    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _episode_page(numbers):
    return {
        "data": [
            {
                "attributes": {
                    "number": n,
                    "canonicalTitle": f"Episode {n}",
                    "synopsis": f"Synopsis {n}",
                }
            }
            for n in numbers
        ]
    }


MAPPING = {
    "data": [{"id": "9", "type": "mappings"}],
    "included": [
        {"id": "7442", "type": "anime", "attributes": {"canonicalTitle": "Kimetsu"}}
    ],
}

EPISODES = {
    "data": [
        {
            "attributes": {
                "number": 2,
                "canonicalTitle": "Trainer Sakonji",
                "synopsis": "Tanjiro meets.",
            }
        },
        {
            "attributes": {
                "number": 1,
                "canonicalTitle": "Cruelty",
                "synopsis": "The family dies.",
            }
        },
        {"attributes": {"number": 3, "canonicalTitle": None, "synopsis": None}},
    ]
}


def test_reads_the_kitsu_id_from_the_mapping():
    assert kitsu.kitsu_id_from_mapping(MAPPING) == "7442"


def test_returns_none_when_the_work_is_not_mapped():
    assert kitsu.kitsu_id_from_mapping({"data": [], "included": []}) is None


def test_episodes_are_ordered_and_empty_ones_dropped():
    episodes = kitsu.episodes_from_payload(EPISODES)

    assert [e["number"] for e in episodes] == [
        1,
        2,
    ]  # sorted, ep3 dropped (no title, no plot)
    assert episodes[0]["title"] == "Cruelty"
    assert episodes[0]["synopsis"] == "The family dies."


def test_an_episode_with_a_title_but_no_plot_is_kept():
    episodes = kitsu.episodes_from_payload(
        {
            "data": [
                {
                    "attributes": {
                        "number": 1,
                        "canonicalTitle": "Cruelty",
                        "synopsis": None,
                    }
                }
            ]
        }
    )
    assert episodes == [{"number": 1, "title": "Cruelty", "synopsis": ""}]


# --- Network-layer behaviour: a failed page must never masquerade as the end
# of the list, and a legitimate "no mapping" result must not raise. ---------


def _mapping(kitsu_id):
    return {
        "data": [{"id": "9", "type": "mappings"}],
        "included": [{"id": kitsu_id, "type": "anime", "attributes": {}}],
    }


def test_a_failed_page_aborts_the_work_instead_of_returning_a_partial_list(
    monkeypatch,
):
    monkeypatch.setattr(kitsu.time, "sleep", lambda *_: None)

    def fake_request(method, url, params=None, headers=None, timeout=None):
        if url.endswith("/mappings"):
            return FakeResponse(200, _mapping("7442"))
        # Page 1 is a full page (looks like there might be more); page 2 is a
        # transient 503. The 503 must not be read as "that was the last page".
        if params["page[offset]"] == 0:
            return FakeResponse(200, _episode_page(range(1, kitsu.PAGE_SIZE + 1)))
        return FakeResponse(503, None)

    monkeypatch.setattr(kitsu, "safe_http_request", fake_request)

    with pytest.raises(kitsu.KitsuHTTPError):
        kitsu.fetch_episodes(16498)


def test_a_work_with_no_kitsu_mapping_resolves_to_no_episodes_without_raising(
    monkeypatch,
):
    monkeypatch.setattr(kitsu.time, "sleep", lambda *_: None)
    seen_urls = []

    def fake_request(method, url, params=None, headers=None, timeout=None):
        seen_urls.append(url)
        return FakeResponse(200, {"data": [], "included": []})

    monkeypatch.setattr(kitsu, "safe_http_request", fake_request)

    assert kitsu.fetch_episodes(999999) == []
    # No episodes call should ever be attempted for an unmapped work.
    assert seen_urls == [f"{kitsu.KITSU}/mappings"]


def test_run_does_not_persist_a_truncated_entry_when_a_page_fails(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(kitsu.time, "sleep", lambda *_: None)

    catalog = [
        {"idMal": 1, "title": "Fails on page 2", "popularity": 100},
        {"idMal": 2, "title": "Succeeds", "popularity": 50},
    ]
    catalog_file = tmp_path / "clean_root_animes.json"
    output_file = tmp_path / "anime_episodes.json"
    catalog_file.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(kitsu, "CATALOG_FILE", str(catalog_file))
    monkeypatch.setattr(kitsu, "OUTPUT_FILE", str(output_file))

    def fake_request(method, url, params=None, headers=None, timeout=None):
        if url.endswith("/mappings"):
            kitsu_id = {"1": "101", "2": "202"}[params["filter[externalId]"]]
            return FakeResponse(200, _mapping(kitsu_id))
        if url.endswith("/anime/101/episodes"):
            if params["page[offset]"] == 0:
                return FakeResponse(200, _episode_page(range(1, kitsu.PAGE_SIZE + 1)))
            return FakeResponse(500, None)  # page 2 fails -> work 1 must be abandoned
        if url.endswith("/anime/202/episodes"):
            return FakeResponse(200, _episode_page([1, 2]))
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(kitsu, "safe_http_request", fake_request)

    kitsu.run()

    out = json.loads(output_file.read_text(encoding="utf-8"))
    assert "1" not in out  # truncated work is never persisted, so a rerun retries it
    assert [e["number"] for e in out["2"]] == [1, 2]

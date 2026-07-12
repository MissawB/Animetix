"""Behavior tests for the manga cover-fetching pipeline.

Covers MAL->MangaDex id mapping, paginated cover extraction + locale filtering,
enrichment (author/alt-titles), the transient-vs-permanent failure distinction
(a 429 must never be cached as "this manga has no cover"), and the orchestrator
run_fetching. All network and sleeps are mocked — no real I/O.
"""

import json
import os
from unittest.mock import MagicMock

import pipeline.manga.fetch_covers as fc
import pytest


@pytest.fixture(autouse=True)
def _no_backoff_sleep(mocker):
    """Le backoff réel dort 2+4+8+16 s : inutile de le subir en test."""
    mocker.patch.object(fc.time, "sleep")


# --- chemins -------------------------------------------------------------


def test_paths_resolve_to_repo_root_data_dir():
    """BASE_DIR remontait un cran trop peu et visait backend/data/ (inexistant) :
    le script sortait "Input file not found" sans rien ingérer."""
    assert os.path.basename(fc.BASE_DIR) != "backend"
    assert os.path.exists(fc.INPUT_FILE), fc.INPUT_FILE
    assert fc.OUTPUT_FILE.endswith(
        os.path.join("data", "processed", "manga_covers.json")
    )


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
    """404 = absence réelle (permanent) => None, pas une erreur transitoire."""
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(404, {}))
    assert fc.get_mangadex_id(123) is None


# --- backoff / transitoire vs permanent ----------------------------------


def test_throttling_raises_instead_of_looking_like_a_missing_manga(mocker):
    """LE bug à ne pas réintroduire : un 429 renvoyé comme `None` faisait passer
    le manga pour « absent de MangaDex » et l'enterrait dans le cache négatif."""
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(429, {}))

    with pytest.raises(fc.TransientAPIError):
        fc.get_mangadex_id(123)


def test_request_retries_then_succeeds(mocker):
    payload = {"Sites": {"Mangadex": {"uuid-1": {}}}}
    http = mocker.patch.object(
        fc,
        "safe_http_request",
        side_effect=[_resp(429, {}), _resp(503, {}), _resp(200, payload)],
    )

    assert fc.get_mangadex_id(123) == "uuid-1"
    assert http.call_count == 3


def test_request_honours_retry_after_header(mocker):
    ok = _resp(200, {"Sites": {"Mangadex": {"u": {}}}})
    throttled = _resp(429, {})
    throttled.headers = {"Retry-After": "30"}
    mocker.patch.object(fc, "safe_http_request", side_effect=[throttled, ok])

    fc.get_mangadex_id(123)

    # 30 s demandées par le serveur > 2 s de backoff par défaut.
    fc.time.sleep.assert_called_once_with(30.0)


def test_network_exception_is_transient_not_permanent(mocker):
    mocker.patch.object(fc, "safe_http_request", side_effect=RuntimeError("boom"))

    with pytest.raises(fc.TransientAPIError):
        fc.get_mangadex_id(123)


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


def test_fetch_covers_paginates_until_total_reached(mocker):
    """Une série longue dépasse les 100 covers/page : tout doit être ramené."""
    page1 = {
        "total": 3,
        "data": [
            {"attributes": {"locale": "ja", "fileName": f"v{i}.jpg", "volume": str(i)}}
            for i in (1, 2)
        ],
    }
    page2 = {
        "total": 3,
        "data": [{"attributes": {"locale": "ja", "fileName": "v3.jpg", "volume": "3"}}],
    }
    http = mocker.patch.object(
        fc, "safe_http_request", side_effect=[_resp(200, page1), _resp(200, page2)]
    )

    covers = fc.fetch_covers("LONG")

    assert [c["volume"] for c in covers["ja"]] == ["1", "2", "3"]
    assert http.call_count == 2
    assert http.call_args_list[1].kwargs["params"]["offset"] == 2


def test_fetch_covers_stops_on_short_page_without_total(mocker):
    """Pas de `total` renvoyé => la page incomplète marque la fin (pas de boucle)."""
    data = {
        "data": [{"attributes": {"locale": "ja", "fileName": "a.jpg", "volume": "1"}}]
    }
    http = mocker.patch.object(fc, "safe_http_request", return_value=_resp(200, data))

    covers = fc.fetch_covers("SHORT")

    assert len(covers["ja"]) == 1
    assert http.call_count == 1


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
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(404, {}))
    assert fc.fetch_covers("X") == {"ja": [], "fr": []}


def test_fetch_covers_propagates_throttling(mocker):
    """Ne surtout pas retourner {} : ce serait lu comme « aucune cover »."""
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(429, {}))

    with pytest.raises(fc.TransientAPIError):
        fc.fetch_covers("X")


# --- fetch_manga_details -------------------------------------------------


def test_fetch_manga_details_extracts_author_and_alt_titles(mocker):
    payload = {
        "data": {
            "attributes": {
                "altTitles": [
                    {"en": "Chainsaw Man"},
                    {"ko": "체인소 맨"},
                    {"en": "Chainsaw Man"},  # doublon -> dédupliqué
                ]
            },
            "relationships": [
                {"type": "artist", "attributes": {"name": "Ignored"}},
                {"type": "author", "attributes": {"name": "Fujimoto Tatsuki"}},
            ],
        }
    }
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(200, payload))

    details = fc.fetch_manga_details("MD")

    assert details["author"] == "Fujimoto Tatsuki"
    assert details["synonyms"] == ["Chainsaw Man", "체인소 맨"]


def test_fetch_manga_details_empty_on_not_found(mocker):
    mocker.patch.object(fc, "safe_http_request", return_value=_resp(404, {}))
    assert fc.fetch_manga_details("MD") == {"author": None, "synonyms": []}


# --- run_fetching --------------------------------------------------------


def _wire_paths(mocker, tmp_path, inp, out):
    """Isole les 3 fichiers du pipeline dans tmp_path."""
    mocker.patch.object(fc, "INPUT_FILE", str(inp))
    mocker.patch.object(fc, "OUTPUT_FILE", str(out))
    mocker.patch.object(fc, "FAILURES_FILE", str(tmp_path / "failures.json"))
    mocker.patch("time.sleep")


def test_run_fetching_missing_input_file(tmp_path, mocker):
    missing = tmp_path / "missing.json"
    mocker.patch.object(fc, "INPUT_FILE", str(missing))
    result = fc.run_fetching()
    assert result.startswith("❌ Input file not found")


def test_run_fetching_writes_enriched_entry(tmp_path, mocker):
    """L'entrée écrite porte les alias : sans eux l'autocomplétion du Covertest
    ne trouve la série que par son titre romaji exact."""
    inp = tmp_path / "in.json"
    out = tmp_path / "nested" / "out.json"  # parent créé via os.makedirs
    inp.write_text(
        json.dumps(
            [
                {
                    "id": 10,
                    "idMal": 42,
                    "title": "Berserk",
                    "title_english": "Berserk",
                    "title_native": "ベルセルク",
                },
                {"id": 11, "title": "NoMal"},  # pas d'idMal -> ignoré
            ]
        ),
        encoding="utf-8",
    )
    _wire_paths(mocker, tmp_path, inp, out)
    mocker.patch.object(fc, "get_mangadex_id", return_value="MD-42")
    mocker.patch.object(
        fc,
        "fetch_covers",
        return_value={"ja": [{"url": "u", "volume": "1"}], "fr": []},
    )
    mocker.patch.object(
        fc,
        "fetch_manga_details",
        return_value={"author": "Miura Kentarou", "synonyms": ["ベルセルク"]},
    )

    result = fc.run_fetching()

    written = json.loads(out.read_text(encoding="utf-8"))
    assert list(written.keys()) == ["10"]
    assert written["10"] == {
        "title": "Berserk",
        "mangadex_id": "MD-42",
        "covers": {"ja": [{"url": "u", "volume": "1"}], "fr": []},
        "author": "Miura Kentarou",
        "title_english": "Berserk",
        "title_native": "ベルセルク",
        "synonyms": ["ベルセルク"],
    }
    assert result == (
        "✅ Finished! Added covers for 1 mangas. " "Total in DB: 1. Reportés (API): 0."
    )


def test_run_fetching_records_failures_in_negative_cache(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    failures = tmp_path / "failures.json"
    inp.write_text(
        json.dumps(
            [
                {"id": 5, "idMal": 99, "title": "NoCover"},
                {"id": 6, "idMal": 98, "title": "Unmapped"},
            ]
        ),
        encoding="utf-8",
    )
    _wire_paths(mocker, tmp_path, inp, out)
    mocker.patch.object(fc, "get_mangadex_id", side_effect=["MD-99", None])
    mocker.patch.object(fc, "fetch_covers", return_value={"ja": [], "fr": []})

    result = fc.run_fetching()

    assert json.loads(out.read_text(encoding="utf-8")) == {}
    assert json.loads(failures.read_text(encoding="utf-8")) == {
        "5": "no_cover_in_locales",
        "6": "no_mangadex_mapping",
    }
    assert result == (
        "✅ Finished! Added covers for 0 mangas. " "Total in DB: 0. Reportés (API): 0."
    )


def test_run_fetching_skips_known_failures_unless_retried(tmp_path, mocker):
    """Le cache négatif évite de re-taper l'API pour rien à chaque run."""
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": 6, "idMal": 98, "title": "Unmapped"}]), encoding="utf-8"
    )
    (tmp_path / "failures.json").write_text(
        json.dumps({"6": "no_mangadex_mapping"}), encoding="utf-8"
    )
    _wire_paths(mocker, tmp_path, inp, out)
    get_id = mocker.patch.object(fc, "get_mangadex_id", return_value=None)

    fc.run_fetching()
    get_id.assert_not_called()

    fc.run_fetching(retry_failed=True)
    get_id.assert_called_once_with(98)


def test_run_fetching_skips_already_present(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": 7, "idMal": 70, "title": "Done"}]), encoding="utf-8"
    )
    out.write_text(json.dumps({"7": {"existing": True}}), encoding="utf-8")
    _wire_paths(mocker, tmp_path, inp, out)
    get_id = mocker.patch.object(fc, "get_mangadex_id")

    result = fc.run_fetching()

    get_id.assert_not_called()  # déjà en base -> aucun appel réseau
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == {"7": {"existing": True}}  # préservé, pas écrasé
    assert result == (
        "✅ Finished! Added covers for 0 mangas. " "Total in DB: 1. Reportés (API): 0."
    )


def test_run_fetching_tolerates_corrupt_existing_output(tmp_path, mocker):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": 3, "idMal": 30, "title": "Resilient"}]), encoding="utf-8"
    )
    out.write_text("{ not valid json", encoding="utf-8")  # branche except du load
    _wire_paths(mocker, tmp_path, inp, out)
    mocker.patch.object(fc, "get_mangadex_id", return_value="MD-30")
    mocker.patch.object(
        fc,
        "fetch_covers",
        return_value={"ja": [{"url": "u", "volume": None}], "fr": []},
    )
    mocker.patch.object(
        fc, "fetch_manga_details", return_value={"author": None, "synonyms": []}
    )

    result = fc.run_fetching()

    written = json.loads(out.read_text(encoding="utf-8"))
    assert "3" in written  # cache corrompu ignoré, le run repart de zéro
    assert result == (
        "✅ Finished! Added covers for 1 mangas. " "Total in DB: 1. Reportés (API): 0."
    )


def test_run_fetching_limit_counts_fetches_not_skips(tmp_path, mocker):
    """`limit` plafonne les mangas RÉELLEMENT interrogés : les entrées déjà en
    base ne consomment plus le quota (l'ancienne sémantique rendait tout re-run
    à limit=100 stérile une fois 90 covers présentes)."""
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": i, "idMal": 100 + i, "title": f"M{i}"} for i in range(5)]),
        encoding="utf-8",
    )
    out.write_text(json.dumps({"0": {"existing": True}}), encoding="utf-8")
    _wire_paths(mocker, tmp_path, inp, out)
    get_id = mocker.patch.object(fc, "get_mangadex_id", return_value="MD")
    mocker.patch.object(
        fc, "fetch_covers", return_value={"ja": [{"url": "u", "volume": "1"}], "fr": []}
    )
    mocker.patch.object(
        fc, "fetch_manga_details", return_value={"author": None, "synonyms": []}
    )

    result = fc.run_fetching(limit=2)

    # M0 est déjà en base : le quota de 2 va à M1 et M2, pas gaspillé sur M0.
    assert get_id.call_count == 2
    written = json.loads(out.read_text(encoding="utf-8"))
    assert sorted(written.keys()) == ["0", "1", "2"]
    assert result == (
        "✅ Finished! Added covers for 2 mangas. " "Total in DB: 3. Reportés (API): 0."
    )


def test_run_fetching_does_not_cache_throttled_mangas_as_failures(tmp_path, mocker):
    """Un manga sauté à cause d'un 429 doit rester repêchable au run suivant :
    l'enterrer dans le cache négatif le rendrait invisible pour toujours."""
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    failures = tmp_path / "failures.json"
    inp.write_text(
        json.dumps(
            [
                {"id": 1, "idMal": 11, "title": "Throttled"},
                {"id": 2, "idMal": 22, "title": "Ok"},
            ]
        ),
        encoding="utf-8",
    )
    _wire_paths(mocker, tmp_path, inp, out)
    mocker.patch.object(
        fc,
        "get_mangadex_id",
        side_effect=[fc.TransientAPIError("HTTP 429"), "MD-22"],
    )
    mocker.patch.object(
        fc, "fetch_covers", return_value={"ja": [{"url": "u", "volume": "1"}], "fr": []}
    )
    mocker.patch.object(
        fc, "fetch_manga_details", return_value={"author": None, "synonyms": []}
    )

    result = fc.run_fetching()

    assert json.loads(failures.read_text(encoding="utf-8")) == {}  # rien d'enterré
    assert list(json.loads(out.read_text(encoding="utf-8"))) == ["2"]  # le run continue
    assert "Reportés (API): 1" in result


def test_run_fetching_aborts_when_api_keeps_throttling(tmp_path, mocker):
    """Inutile de marteler une API qui nous jette : on s'arrête et on garde l'acquis."""
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    inp.write_text(
        json.dumps([{"id": i, "idMal": i, "title": f"M{i}"} for i in range(50)]),
        encoding="utf-8",
    )
    _wire_paths(mocker, tmp_path, inp, out)
    get_id = mocker.patch.object(
        fc, "get_mangadex_id", side_effect=fc.TransientAPIError("HTTP 429")
    )

    result = fc.run_fetching()

    assert get_id.call_count == fc.MAX_CONSECUTIVE_TRANSIENT  # arrêt, pas 50 essais
    assert result.startswith("🛑 Aborted")
    assert json.loads((tmp_path / "failures.json").read_text(encoding="utf-8")) == {}

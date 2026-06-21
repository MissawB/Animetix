"""Behavior tests for the Fandom lore scraper MLOps pipeline.

Covers ``FandomLoreScraper``: popular-franchise discovery (SQL hit / SQL error /
fallback), polite URL scraping (BeautifulSoup noise-stripping, regex fallback,
HTTP-error resilience), semantic sentence chunking, and the end-to-end
``execute_pipeline`` in both dry-run and real-ChromaDB-upsert modes plus its
skip / scrape-failure branches.

All external I/O is mocked in the module namespace: ``safe_http_request`` (HTTP),
the DI container / ChromaDB repository, and the ``MediaItem`` ORM. Real (small)
HTML strings are fed to BeautifulSoup so the real parsing runs. No real network,
DB, or model work happens.
"""

from unittest.mock import MagicMock

import pipeline.mlops.fandom_lore_scraper as fls
import pytest


def _resp(content, status=200):
    r = MagicMock()
    r.status_code = status
    r.content = content
    return r


@pytest.fixture
def scraper():
    """Dry-run scraper with no DI container by default."""
    s = fls.FandomLoreScraper(dry_run=True)
    s.container = None
    return s


# --- get_popular_franchises ---------------------------------------------


def test_popular_franchises_from_sql(mocker, scraper):
    """When MediaItem returns titles, they are lowercased/stripped + deduped."""
    qs = MagicMock()
    qs.__getitem__.return_value = ["  One Piece ", "NARUTO", "naruto"]
    values = MagicMock()
    values.return_value = qs
    media = MagicMock()
    media.objects.filter.return_value.values_list = values
    mocker.patch.object(fls, "MediaItem", media)

    result = scraper.get_popular_franchises()
    assert set(result) == {"one piece", "naruto"}
    media.objects.filter.assert_called_once_with(popularity__gt=80)


def test_popular_franchises_falls_back_on_sql_error(mocker, scraper):
    media = MagicMock()
    media.objects.filter.side_effect = RuntimeError("db down")
    mocker.patch.object(fls, "MediaItem", media)

    result = scraper.get_popular_franchises()
    assert result == list(fls.FANDOM_MAP.keys())


def test_popular_franchises_fallback_when_no_orm(mocker, scraper):
    mocker.patch.object(fls, "MediaItem", None)
    assert scraper.get_popular_franchises() == list(fls.FANDOM_MAP.keys())


def test_popular_franchises_fallback_when_sql_empty(mocker, scraper):
    """Empty result set -> static FANDOM_MAP fallback (not an empty list)."""
    qs = MagicMock()
    qs.__getitem__.return_value = []
    media = MagicMock()
    media.objects.filter.return_value.values_list.return_value = qs
    mocker.patch.object(fls, "MediaItem", media)
    assert scraper.get_popular_franchises() == list(fls.FANDOM_MAP.keys())


# --- scrape_url ----------------------------------------------------------


def test_scrape_url_strips_noise_and_targets_content(mocker, scraper):
    html = (
        b"<html><body>"
        b"<script>var x=1;</script><style>.a{}</style>"
        b"<aside>ADVERT</aside>"
        b'<div id="mw-content-text">Guts is a   mercenary.</div>'
        b"<div>FOOTER</div>"
        b"</body></html>"
    )
    mocker.patch.object(fls, "safe_http_request", return_value=_resp(html))

    text = scraper.scrape_url("https://berserk.fandom.com/wiki/Guts")
    # Targeted #mw-content-text only; noise + footer outside it dropped.
    assert text == "Guts is a mercenary."
    assert "ADVERT" not in text
    assert "FOOTER" not in text
    assert "var x" not in text


def test_scrape_url_falls_back_to_full_soup_without_content_div(mocker, scraper):
    html = b"<html><body><p>Lore   text here.</p></body></html>"
    mocker.patch.object(fls, "safe_http_request", return_value=_resp(html))
    text = scraper.scrape_url("http://x")
    assert "Lore text here." in text


def test_scrape_url_regex_fallback_without_beautifulsoup(mocker, scraper):
    """When BeautifulSoup is unavailable, the regex path strips tags + noise."""
    mocker.patch.object(fls, "BeautifulSoup", None)
    html = b"<script>junk()</script><p>Hello <b>World</b></p>"
    mocker.patch.object(fls, "safe_http_request", return_value=_resp(html))
    text = scraper.scrape_url("http://x")
    assert text == "Hello World"
    assert "junk" not in text


def test_scrape_url_returns_none_on_http_error(mocker, scraper):
    mocker.patch.object(
        fls, "safe_http_request", side_effect=RuntimeError("network down")
    )
    assert scraper.scrape_url("http://x") is None


def test_scrape_url_sends_browser_headers(mocker, scraper):
    html = b"<div id='mw-content-text'>ok</div>"
    http = mocker.patch.object(fls, "safe_http_request", return_value=_resp(html))
    scraper.scrape_url("http://x")
    _, kwargs = http.call_args
    assert "User-Agent" in kwargs["headers"]
    assert kwargs["timeout"] == 10


# --- chunk_ssemantic -----------------------------------------------------


def test_chunk_keeps_short_text_single_chunk(scraper):
    chunks = scraper.chunk_ssemantic("One sentence. Two sentence.", size=500)
    assert chunks == ["One sentence. Two sentence."]


def test_chunk_splits_on_sentence_boundaries(scraper):
    text = "Aaaa bbbb. Cccc dddd. Eeee ffff."
    chunks = scraper.chunk_ssemantic(text, size=15)
    # Each sentence ~10 chars, size 15 forces a split per sentence.
    assert len(chunks) >= 2
    # Re-joining yields back all the sentences (no content lost).
    joined = " ".join(chunks)
    for piece in ["Aaaa bbbb.", "Cccc dddd.", "Eeee ffff."]:
        assert piece in joined


def test_chunk_ignores_blank_sentences(scraper):
    chunks = scraper.chunk_ssemantic("   ", size=100)
    assert chunks == []


# --- execute_pipeline ----------------------------------------------------


def test_pipeline_skips_unmapped_franchise(mocker, scraper):
    mocker.patch.object(scraper, "get_popular_franchises", return_value=["bleach"])
    scrape = mocker.patch.object(scraper, "scrape_url")
    scraper.execute_pipeline()
    scrape.assert_not_called()  # no Fandom map entry -> skipped entirely


def test_pipeline_dry_run_does_not_upsert(mocker, scraper):
    mocker.patch.object(scraper, "get_popular_franchises", return_value=["berserk"])
    # main page + 3 subpages all return the same text.
    mocker.patch.object(
        scraper, "scrape_url", return_value="Guts fights. Griffith betrays. Done now."
    )
    scraper.container = MagicMock()
    scraper.dry_run = True

    scraper.execute_pipeline()
    # Dry-run path never touches the repository.
    scraper.container.repository.assert_not_called()


def test_pipeline_real_upsert_payload(mocker, scraper):
    """Real (non-dry) run builds ids/embeddings/metadata and upserts them."""
    mocker.patch.object(scraper, "get_popular_franchises", return_value=["naruto"])

    # Only the main page yields text; subpages return None (scrape failure).
    def fake_scrape(url):
        return (
            "Naruto trains hard. He becomes Hokage."
            if url.endswith("/Naruto")
            else None
        )

    mocker.patch.object(scraper, "scrape_url", side_effect=fake_scrape)

    container = MagicMock()
    repo = container.repository.return_value
    repo.chroma.coll_names = {"Anime": "anime_thematic"}
    repo.chroma.embedding_fn = lambda texts: [[0.1, 0.2, 0.3] for _ in texts]
    scraper.container = container
    scraper.dry_run = False

    scraper.execute_pipeline()

    repo.chroma.upsert_items.assert_called_once()
    coll, ids, embeddings, metadatas = repo.chroma.upsert_items.call_args.args
    assert coll == "anime_thematic"
    assert len(ids) == len(embeddings) == len(metadatas) >= 1
    assert all(i.startswith("fandom_naruto_") for i in ids)
    assert embeddings[0] == [0.1, 0.2, 0.3]
    meta = metadatas[0]
    assert meta["franchise"] == "naruto"
    assert meta["source"] == "Fandom Scraping"
    assert meta["title"] == "Lore Naruto"
    # Contextual-retrieval header prepended to the indexed description.
    assert meta["description"].startswith("[Source: Fandom Lore | Franchise: Naruto")


def test_pipeline_resilient_to_upsert_error(mocker, scraper):
    """An upsert failure is logged but does not crash the pipeline."""
    mocker.patch.object(scraper, "get_popular_franchises", return_value=["naruto"])
    mocker.patch.object(scraper, "scrape_url", return_value="A sentence here. Two.")
    container = MagicMock()
    repo = container.repository.return_value
    repo.chroma.coll_names = {"Anime": "anime_thematic"}
    repo.chroma.embedding_fn = lambda texts: [[0.0] for _ in texts]
    repo.chroma.upsert_items.side_effect = RuntimeError("chroma down")
    scraper.container = container
    scraper.dry_run = False
    err = mocker.patch.object(fls.logger, "error")

    scraper.execute_pipeline()  # must not raise
    assert err.called


def test_pipeline_no_texts_when_all_scrapes_fail(mocker, scraper):
    mocker.patch.object(scraper, "get_popular_franchises", return_value=["naruto"])
    mocker.patch.object(scraper, "scrape_url", return_value=None)
    container = MagicMock()
    scraper.container = container
    scraper.dry_run = False
    scraper.execute_pipeline()
    container.repository.return_value.chroma.upsert_items.assert_not_called()

"""`sync_catalog` rewritten from update_or_create()-per-item to bulk writes.

Against the remote Neon DB (us-east-1, no local replica), the old command did a
SELECT + INSERT/UPDATE round trip per item -- ~44 700 of them, all inside one
`@transaction.atomic` -- and after 70 minutes it still had not committed. These
tests pin the replacement contract: a single upfront SELECT to classify
create/update, batched bulk_create/bulk_update (one transaction per batch, not
one for the whole run), a cheap skip path for byte-identical rows so a routine
re-sync writes nothing, `--dry-run`, `--media-type`, and cache invalidation of
the `catalog_{type}` Redis key at the end (the per-process RAM cache in
CatalogService._cached_catalogs cannot be reached from here and is documented,
not silently ignored).
"""

import json
from io import StringIO

import pytest
from animetix.models import MediaItem
from django.core.cache import cache
from django.core.management import call_command


def _write_catalog(tmp_path, monkeypatch, filename, items):
    from animetix.management.commands import sync_catalog

    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    (processed / filename).write_text(json.dumps(items), encoding="utf-8")
    # Same trick the pre-existing sync_catalog tests use: abspath is mocked to
    # ignore its argument entirely, so both calls in the command (dirname(
    # abspath(__file__)) and abspath(join(...))) collapse onto tmp_path.
    monkeypatch.setattr(
        sync_catalog.os.path, "abspath", lambda _p: str(tmp_path), raising=False
    )


def _run(**kwargs):
    out = StringIO()
    call_command("sync_catalog", "--no-color", stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.django_db
def test_second_run_of_unchanged_data_writes_nothing(tmp_path, monkeypatch):
    data = [{"idMal": 1, "title": "Frieren", "popularity": 5000}]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", data)

    _run()
    assert MediaItem.objects.count() == 1

    output = _run()

    assert "created=0" in output
    assert "updated=0" in output
    assert "skipped=1" in output
    assert MediaItem.objects.get(external_id="1").title == "Frieren"


@pytest.mark.django_db
def test_new_items_created_and_changed_items_updated(tmp_path, monkeypatch):
    data = [
        {"idMal": 1, "title": "Frieren", "popularity": 5000},
        {"idMal": 2, "title": "Old Title", "popularity": 10},
    ]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", data)
    _run()

    updated_data = [
        {"idMal": 1, "title": "Frieren", "popularity": 5000},  # unchanged
        {"idMal": 2, "title": "New Title", "popularity": 999},  # changed
        {"idMal": 3, "title": "Brand New", "popularity": 42},  # new
    ]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", updated_data)
    output = _run()

    assert "created=1" in output
    assert "updated=1" in output
    assert "skipped=1" in output

    assert MediaItem.objects.count() == 3
    changed = MediaItem.objects.get(external_id="2")
    assert changed.title == "New Title"
    assert changed.popularity == 999.0
    assert MediaItem.objects.get(external_id="3").title == "Brand New"


@pytest.mark.django_db
def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    data = [{"idMal": 1, "title": "Frieren", "popularity": 5000}]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", data)

    output = _run(dry_run=True)

    assert MediaItem.objects.count() == 0
    assert "created=1" in output


@pytest.mark.django_db
def test_dry_run_on_a_changed_row_reports_update_without_writing(tmp_path, monkeypatch):
    data = [{"idMal": 1, "title": "Frieren", "popularity": 5000}]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", data)
    _run()

    changed = [{"idMal": 1, "title": "Frieren Season 2", "popularity": 5000}]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", changed)
    output = _run(dry_run=True)

    assert "updated=1" in output
    # Dry run: the row in the DB must be untouched.
    assert MediaItem.objects.get(external_id="1").title == "Frieren"


@pytest.mark.django_db
def test_media_type_filter_syncs_only_that_type(tmp_path, monkeypatch):
    from animetix.management.commands import sync_catalog

    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    (processed / "clean_root_animes.json").write_text(
        json.dumps([{"idMal": 1, "title": "Frieren", "popularity": 1}]),
        encoding="utf-8",
    )
    (processed / "clean_root_mangas.json").write_text(
        json.dumps([{"idMal": 2, "title": "Berserk", "popularity": 1}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sync_catalog.os.path, "abspath", lambda _p: str(tmp_path), raising=False
    )

    _run(media_type="Anime")

    assert MediaItem.objects.filter(media_type="Anime").count() == 1
    assert MediaItem.objects.filter(media_type="Manga").count() == 0


@pytest.mark.django_db
def test_sync_invalidates_the_catalogue_cache(tmp_path, monkeypatch):
    data = [{"idMal": 1, "title": "Frieren", "popularity": 5000}]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", data)

    cache.set("catalog_Anime", {"stale": True}, timeout=3600)
    _run()

    assert cache.get("catalog_Anime") is None


@pytest.mark.django_db
def test_dry_run_does_not_touch_the_cache(tmp_path, monkeypatch):
    data = [{"idMal": 1, "title": "Frieren", "popularity": 5000}]
    _write_catalog(tmp_path, monkeypatch, "clean_root_animes.json", data)

    cache.set("catalog_Anime", {"stale": True}, timeout=3600)
    _run(dry_run=True)

    assert cache.get("catalog_Anime") == {"stale": True}

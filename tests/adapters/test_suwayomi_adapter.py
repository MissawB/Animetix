from unittest.mock import MagicMock, patch

import pytest
from adapters.persistence.suwayomi_adapter import SuwayomiAdapter
from animetix.models import MediaItem
from core.domain.services.manga_service import MangaService


def test_suwayomi_adapter_get_sources():
    adapter = SuwayomiAdapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "sources": {
                "nodes": [
                    {"id": "1", "name": "MangaDex", "lang": "en"},
                    {"id": "2", "name": "MangaReader", "lang": "fr"},
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        sources = adapter.get_sources()
        assert len(sources) == 2
        assert sources[0]["name"] == "MangaDex"
        assert sources[1]["id"] == "2"
        mock_post.assert_called_once()


def test_suwayomi_adapter_search_manga():
    adapter = SuwayomiAdapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "fetchSourceManga": {
                "mangas": [
                    {
                        "id": "suwayomi-manga-1",
                        "title": "One Piece",
                        "thumbnailUrl": "http://image.png",
                    }
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        mangas = adapter.search_manga("1", "One Piece")
        assert len(mangas) == 1
        assert mangas[0]["title"] == "One Piece"
        mock_post.assert_called_once()


def test_suwayomi_adapter_get_manga_details():
    adapter = SuwayomiAdapter()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "manga": {
                "id": 123,
                "title": "One Piece",
                "description": "Pirates!",
                "thumbnailUrl": "http://image.png",
                "author": "Oda",
                "artist": "Oda",
                "status": "Ongoing",
            }
        }
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        details = adapter.get_manga_details("123")
        assert details["title"] == "One Piece"
        assert details["author"] == "Oda"
        mock_post.assert_called_once()


@pytest.mark.django_db
def test_manga_service_suwayomi_sync():
    # Setup mock adapter
    mock_adapter = MagicMock()
    mock_adapter.get_chapters.return_value = [
        {"id": "chapter-100", "name": "Chapter 100", "chapterNumber": 100.0}
    ]
    mock_adapter.get_pages.return_value = [
        "http://localhost:4567/page1.jpg",
        "http://localhost:4567/page2.jpg",
    ]

    service = MangaService(suwayomi_adapter=mock_adapter)

    # Create a MediaItem
    MediaItem.objects.create(
        external_id="suwayomi:1:123", media_type="Manga", title="Test Suwayomi Manga"
    )

    # Test chapter syncing
    chapters = service.get_chapters("suwayomi:1:123")
    mock_adapter.get_chapters.assert_called_once_with("123")
    assert len(chapters) == 1
    assert chapters[0].title == "Chapter 100"
    assert chapters[0].number == 100.0

    # Test page syncing
    chapter_details = service.get_chapter_details("suwayomi:1:123", 100.0)
    mock_adapter.get_pages.assert_called_once_with("chapter-100")
    pages = list(chapter_details.pages.all())
    assert len(pages) == 2
    assert pages[0].number == 1
    assert "/api/v1/media/Manga/suwayomi-image/?page_url=" in pages[0].image_url


def test_suwayomi_adapter_get_extensions():
    adapter = SuwayomiAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "extensions": {
                "nodes": [
                    {
                        "pkgName": "com.mangadex",
                        "name": "MangaDex",
                        "versionName": "1.4.15",
                        "isInstalled": True,
                        "hasUpdate": False,
                        "lang": "en",
                        "iconUrl": "http://mangadex/icon.png",
                        "isNsfw": False,
                        "isObsolete": False,
                    }
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        exts = adapter.get_extensions()
        assert len(exts) == 1
        assert exts[0]["pkgName"] == "com.mangadex"
        assert exts[0]["isInstalled"] is True
        mock_post.assert_called_once()


def test_suwayomi_adapter_update_extensions():
    adapter = SuwayomiAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "updateExtensions": {
                "extensions": [
                    {
                        "pkgName": "com.mangadex",
                        "name": "MangaDex",
                        "isInstalled": True,
                        "hasUpdate": False,
                    }
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        results = adapter.update_extensions(["com.mangadex"], "install")
        assert len(results) == 1
        assert results[0]["pkgName"] == "com.mangadex"
        assert results[0]["isInstalled"] is True

        # Verify post payload
        called_args, called_kwargs = mock_post.call_args
        assert "variables" in called_kwargs["json"]
        assert called_kwargs["json"]["variables"]["ids"] == ["com.mangadex"]
        assert called_kwargs["json"]["variables"]["patch"]["install"] is True

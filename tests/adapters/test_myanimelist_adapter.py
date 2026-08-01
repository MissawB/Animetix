from unittest.mock import MagicMock, patch

import httpx
from adapters.trackers.myanimelist_adapter import MyAnimeListAdapter


def _response(payload, status=200):
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = payload
    return mock


def test_search_uses_jikan_without_authentication():
    adapter = MyAnimeListAdapter()
    payload = {"data": [{"mal_id": 44347, "title": "One Punch-Man", "chapters": 200}]}

    with patch("httpx.Client.get", return_value=_response(payload)) as mock_get:
        results = adapter.search("one punch", token=None)

        assert results == [
            {"remote_id": "44347", "title": "One Punch-Man", "chapters": 200}
        ]
        url = mock_get.call_args.args[0]
        assert url.startswith("https://api.jikan.moe/v4/manga")
        assert "one punch" in url or "one%20punch" in url
        # Jikan est public : aucun jeton ne doit fuiter dans cette requête.
        assert "Authorization" not in (mock_get.call_args.kwargs.get("headers") or {})


def test_read_progress_reads_my_list_status():
    adapter = MyAnimeListAdapter()
    payload = {"my_list_status": {"num_chapters_read": 164}}

    with patch("httpx.Client.get", return_value=_response(payload)) as mock_get:
        assert adapter.read_progress("44347", token="tok") == 164
        assert mock_get.call_args.args[0].startswith(
            "https://api.myanimelist.net/v2/manga/44347"
        )
        assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer tok"


def test_read_progress_is_zero_when_absent_from_the_list():
    """Réponse arrivée sans `my_list_status` = l'œuvre n'est pas encore dans la
    liste : 0, pas « inconnu ». `None` est réservé aux vrais échecs (non-200,
    transport), sinon une série jamais listée ne serait jamais synchronisée."""
    adapter = MyAnimeListAdapter()
    with patch("httpx.Client.get", return_value=_response({})):
        assert adapter.read_progress("44347", token="tok") == 0


def test_write_progress_patches_num_chapters_read():
    adapter = MyAnimeListAdapter()
    with patch(
        "httpx.Client.patch", return_value=_response({"num_chapters_read": 165})
    ) as mock_patch:
        assert adapter.write_progress("44347", 165, token="tok") is True
        assert mock_patch.call_args.args[0].endswith("/v2/manga/44347/my_list_status")
        assert mock_patch.call_args.kwargs["data"] == {
            "num_chapters_read": 165,
            "status": "reading",
        }


def test_no_mock_token_shortcut():
    import inspect

    from adapters.trackers import myanimelist_adapter

    source = inspect.getsource(myanimelist_adapter)
    assert "mock-token" not in source
    assert "test-token" not in source


# Error path tests: degradation silencieuse sans exception


def test_search_returns_empty_on_non_200_response():
    """Non-200 HTTP response → search returns empty list."""
    adapter = MyAnimeListAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.get", return_value=mock_response):
        results = adapter.search("test", token=None)
        assert results == []


def test_search_returns_empty_on_transport_error():
    """Transport error (httpx.RequestError) → search returns empty list, no exception."""
    adapter = MyAnimeListAdapter()

    with patch(
        "httpx.Client.get", side_effect=httpx.RequestError("Connection refused")
    ):
        results = adapter.search("test", token=None)
        assert results == []


def test_search_ignores_items_without_mal_id():
    """Search result with missing 'mal_id' field → item is ignored, others preserved."""
    adapter = MyAnimeListAdapter()
    payload = {
        "data": [
            {"mal_id": 44347, "title": "One Punch-Man", "chapters": 200},
            {"title": "No ID Manga", "chapters": 100},
            {"mal_id": 1, "title": "Another Manga", "chapters": 150},
        ]
    }

    with patch("httpx.Client.get", return_value=_response(payload)):
        results = adapter.search("test", token=None)
        assert len(results) == 2
        assert results[0]["remote_id"] == "44347"
        assert results[1]["remote_id"] == "1"


def test_search_never_raises_on_a_malformed_item():
    """Un élément non-dict ne doit pas lever : la boucle de normalisation vit
    hors du `try` de la requête, et `TrackerPort` promet qu'un adaptateur ne
    lève jamais (sinon 500 sur l'endpoint des liaisons)."""
    adapter = MyAnimeListAdapter()
    payload = {"data": ["not-a-dict", {"mal_id": 44347, "title": "One Punch-Man"}]}

    with patch("httpx.Client.get", return_value=_response(payload)):
        results = adapter.search("test", token=None)

    assert [r["remote_id"] for r in results] == ["44347"]


def test_read_progress_refuses_a_non_numeric_remote_id():
    """Les identifiants MAL sont numériques. Interpoler la valeur brute dans le
    chemin d'URL enverrait le jeton de l'utilisateur sur un tout autre point de
    l'API MAL — AniList caste déjà en `int`, l'asymétrie était le défaut."""
    adapter = MyAnimeListAdapter()

    with patch("httpx.Client.get") as mock_get:
        assert adapter.read_progress("44347/../../users/@me", token="tok") is None
        mock_get.assert_not_called()


def test_write_progress_refuses_a_non_numeric_remote_id():
    adapter = MyAnimeListAdapter()

    with patch("httpx.Client.patch") as mock_patch:
        assert adapter.write_progress("../../x", 165, token="tok") is False
        mock_patch.assert_not_called()


def test_read_progress_returns_none_on_non_200_response():
    """Non-200 HTTP response → read_progress returns None."""
    adapter = MyAnimeListAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.get", return_value=mock_response):
        result = adapter.read_progress("44347", token="tok")
        assert result is None


def test_read_progress_returns_none_on_transport_error():
    """Transport error (httpx.RequestError) → read_progress returns None, no exception."""
    adapter = MyAnimeListAdapter()

    with patch(
        "httpx.Client.get", side_effect=httpx.RequestError("Connection refused")
    ):
        result = adapter.read_progress("44347", token="tok")
        assert result is None


def test_write_progress_returns_false_on_non_200_response():
    """Non-200 HTTP response → write_progress returns False."""
    adapter = MyAnimeListAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.patch", return_value=mock_response):
        result = adapter.write_progress("44347", 165, token="tok")
        assert result is False


def test_write_progress_returns_false_on_transport_error():
    """Transport error (httpx.RequestError) → write_progress returns False, no exception."""
    adapter = MyAnimeListAdapter()

    with patch(
        "httpx.Client.patch", side_effect=httpx.RequestError("Connection refused")
    ):
        result = adapter.write_progress("44347", 165, token="tok")
        assert result is False

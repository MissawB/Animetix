from unittest.mock import MagicMock, patch

import httpx
from adapters.trackers.anilist_adapter import AniListAdapter


def _response(payload):
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = payload
    return mock


def test_search_returns_normalised_results():
    adapter = AniListAdapter()
    payload = {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 30013,
                        "title": {
                            "romaji": "One Punch-Man",
                            "english": "One-Punch Man",
                        },
                        "chapters": 200,
                    }
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=_response(payload)) as mock_post:
        results = adapter.search("one punch", token=None)

        assert results == [
            {"remote_id": "30013", "title": "One Punch-Man", "chapters": 200}
        ]
        variables = mock_post.call_args.kwargs["json"]["variables"]
        assert variables == {"search": "one punch"}
        assert "type: MANGA" in mock_post.call_args.kwargs["json"]["query"]


def test_read_progress_returns_the_remote_counter():
    adapter = AniListAdapter()
    payload = {"data": {"Media": {"mediaListEntry": {"progress": 164}}}}

    with patch("httpx.Client.post", return_value=_response(payload)) as mock_post:
        assert adapter.read_progress("30013", token="tok") == 164
        assert mock_post.call_args.kwargs["json"]["variables"] == {"id": 30013}
        assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer tok"


def test_read_progress_is_zero_when_the_work_is_not_in_the_list():
    """Réponse arrivée, `mediaListEntry` nulle = l'œuvre n'est pas encore dans
    la liste de l'utilisateur. C'est 0, pas « inconnu » : `None` empêcherait le
    service d'écrire, donc de créer l'entrée distante — le cas le plus courant.
    `None` reste réservé aux vrais échecs (cf. les tests d'erreur plus bas)."""
    adapter = AniListAdapter()
    payload = {"data": {"Media": {"mediaListEntry": None}}}

    with patch("httpx.Client.post", return_value=_response(payload)):
        assert adapter.read_progress("30013", token="tok") == 0


def test_read_progress_is_none_when_media_list_entry_is_malformed():
    """`mediaListEntry` présent mais pas un objet (liste ici) = réponse
    illisible, pas une absence légitime. Confondre ce cas avec le `0` de
    « l'œuvre n'est pas encore dans la liste » écraserait une progression
    distante réelle avec une valeur fabriquée."""
    adapter = AniListAdapter()
    payload = {"data": {"Media": {"mediaListEntry": ["not-a-dict"]}}}

    with patch("httpx.Client.post", return_value=_response(payload)):
        assert adapter.read_progress("30013", token="tok") is None


def test_write_progress_posts_the_save_mutation():
    adapter = AniListAdapter()
    payload = {"data": {"SaveMediaListEntry": {"id": 1, "progress": 165}}}

    with patch("httpx.Client.post", return_value=_response(payload)) as mock_post:
        assert adapter.write_progress("30013", 165, token="tok") is True
        sent = mock_post.call_args.kwargs["json"]
        assert sent["variables"] == {"mediaId": 30013, "progress": 165}
        assert "SaveMediaListEntry" in sent["query"]


def test_no_mock_token_shortcut():
    """Le raccourci `token == "mock-token"` du code historique ne doit pas survivre :
    un adaptateur qui simule un succès rend les tests aveugles au vrai contrat."""
    import inspect

    from adapters.trackers import anilist_adapter

    source = inspect.getsource(anilist_adapter)
    assert "mock-token" not in source
    assert "test-token" not in source


# Error path tests: degradation silencieuse sans exception


def test_search_returns_empty_on_non_200_response():
    """Non-200 HTTP response → search returns empty list."""
    adapter = AniListAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.post", return_value=mock_response):
        results = adapter.search("test", token=None)
        assert results == []


def test_search_returns_empty_on_graphql_error():
    """GraphQL errors in response → search returns empty list."""
    adapter = AniListAdapter()
    payload = {"errors": [{"message": "Invalid query"}]}

    with patch("httpx.Client.post", return_value=_response(payload)):
        results = adapter.search("test", token=None)
        assert results == []


def test_search_returns_empty_on_transport_error():
    """Transport error (httpx.RequestError) → search returns empty list, no exception."""
    adapter = AniListAdapter()

    with patch(
        "httpx.Client.post", side_effect=httpx.RequestError("Connection refused")
    ):
        results = adapter.search("test", token=None)
        assert results == []


def test_search_ignores_items_without_id():
    """Search result with missing 'id' field → item is ignored, others preserved."""
    adapter = AniListAdapter()
    payload = {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 30013,
                        "title": {"romaji": "One Punch-Man"},
                        "chapters": 200,
                    },
                    {
                        "title": {"romaji": "No ID Manga"},
                        "chapters": 100,
                    },
                    {
                        "id": 40001,
                        "title": {"romaji": "Another Manga"},
                        "chapters": 150,
                    },
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=_response(payload)):
        results = adapter.search("test", token=None)
        assert len(results) == 2
        assert results[0]["remote_id"] == "30013"
        assert results[1]["remote_id"] == "40001"


def test_search_never_raises_on_a_malformed_item():
    """Un élément non-dict dans la réponse ne doit pas lever : `TrackerPort`
    promet qu'un adaptateur ne lève jamais, et la boucle de normalisation vit
    hors du `try` de la requête — une exception ici faisait un 500 sur
    l'endpoint des liaisons."""
    adapter = AniListAdapter()
    payload = {
        "data": {
            "Page": {
                "media": [
                    "not-a-dict",
                    {"id": 30013, "title": {"romaji": "One Punch-Man"}},
                    {"id": 40001, "title": "un titre plat, pas un objet"},
                ]
            }
        }
    }

    with patch("httpx.Client.post", return_value=_response(payload)):
        results = adapter.search("test", token=None)

    assert [r["remote_id"] for r in results] == ["30013", "40001"]
    assert results[1]["title"] == ""


def test_read_progress_returns_none_on_non_200_response():
    """Non-200 HTTP response → read_progress returns None."""
    adapter = AniListAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.post", return_value=mock_response):
        result = adapter.read_progress("30013", token="tok")
        assert result is None


def test_read_progress_returns_none_on_graphql_error():
    """GraphQL errors in response → read_progress returns None."""
    adapter = AniListAdapter()
    payload = {"errors": [{"message": "Invalid query"}]}

    with patch("httpx.Client.post", return_value=_response(payload)):
        result = adapter.read_progress("30013", token="tok")
        assert result is None


def test_read_progress_returns_none_on_transport_error():
    """Transport error (httpx.RequestError) → read_progress returns None, no exception."""
    adapter = AniListAdapter()

    with patch(
        "httpx.Client.post", side_effect=httpx.RequestError("Connection refused")
    ):
        result = adapter.read_progress("30013", token="tok")
        assert result is None


def test_read_progress_returns_none_on_invalid_remote_id():
    """Non-numeric remote_id → read_progress returns None, no exception."""
    adapter = AniListAdapter()

    with patch("httpx.Client.post"):
        result = adapter.read_progress("not-a-number", token="tok")
        assert result is None


def test_write_progress_returns_false_on_non_200_response():
    """Non-200 HTTP response → write_progress returns False."""
    adapter = AniListAdapter()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.post", return_value=mock_response):
        result = adapter.write_progress("30013", 165, token="tok")
        assert result is False


def test_write_progress_returns_false_on_graphql_error():
    """GraphQL errors in response → write_progress returns False."""
    adapter = AniListAdapter()
    payload = {"errors": [{"message": "Mutation failed"}]}

    with patch("httpx.Client.post", return_value=_response(payload)):
        result = adapter.write_progress("30013", 165, token="tok")
        assert result is False


def test_write_progress_returns_false_on_transport_error():
    """Transport error (httpx.RequestError) → write_progress returns False, no exception."""
    adapter = AniListAdapter()

    with patch(
        "httpx.Client.post", side_effect=httpx.RequestError("Connection refused")
    ):
        result = adapter.write_progress("30013", 165, token="tok")
        assert result is False


def test_write_progress_returns_false_on_invalid_remote_id():
    """Non-numeric remote_id → write_progress returns False, no exception."""
    adapter = AniListAdapter()

    with patch("httpx.Client.post"):
        result = adapter.write_progress("not-a-number", 165, token="tok")
        assert result is False


def test_write_progress_returns_false_on_missing_mutation_response():
    """Mutation response missing SaveMediaListEntry → write_progress returns False."""
    adapter = AniListAdapter()
    payload = {"data": {"SaveMediaListEntry": None}}

    with patch("httpx.Client.post", return_value=_response(payload)):
        result = adapter.write_progress("30013", 165, token="tok")
        assert result is False

from unittest.mock import MagicMock, patch

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


def test_read_progress_is_none_when_the_work_is_not_in_the_list():
    adapter = AniListAdapter()
    payload = {"data": {"Media": {"mediaListEntry": None}}}

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

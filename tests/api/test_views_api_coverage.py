"""Coverage tests for animetix.views.api.

These module-level function views (``get_task_status`` and the four
``*_stream`` SSE helpers) are legacy helpers that are not wired into the URL conf
(the routed streaming endpoints live in ``animetix.api.streams``). They are
therefore driven directly with a ``RequestFactory`` request, with the
``get_session_service`` and ``get_container`` collaborators patched at the module
level so no real DI / cache / domain service is exercised.

The streaming views return a ``StreamingHttpResponse``; the test consumes the
``streaming_content`` generator and parses the emitted ``data: {...}`` SSE frames
to assert on real content (including the error fallback frames).
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from animetix.views import api as api_mod
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory


@pytest.fixture
def rf():
    return RequestFactory()


def _sse_events(response):
    """Decode a StreamingHttpResponse into a list of parsed SSE payloads."""
    events = []
    for chunk in response.streaming_content:
        text = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


# --------------------------------------------------------------------------- #
# get_task_status
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_get_task_status_not_ready_returns_204(rf):
    cache.clear()
    request = rf.get("/x")
    with patch.object(api_mod, "get_session_service", return_value=MagicMock()):
        resp = api_mod.get_task_status(request, "task-1")
    assert resp.status_code == 204


@pytest.mark.django_db
def test_get_task_status_ready_json_result(rf):
    cache.set("task_result:task-2", {"ready": True, "result": {"answer": 42}})
    request = rf.get("/x")
    with patch.object(api_mod, "get_session_service", return_value=MagicMock()):
        resp = api_mod.get_task_status(request, "task-2")
    assert resp.status_code == 200
    assert json.loads(resp.content)["result"] == {"answer": 42}


@pytest.mark.django_db
def test_get_task_status_ready_scenario_renders_fragment(rf):
    cache.set(
        "task_result:task-3",
        {
            "ready": True,
            "result": {
                "scenario": "The Forge",
                "reasoning": "because",
                "fusion_image": "img.png",
            },
        },
    )
    session = MagicMock()
    session.get.side_effect = lambda k: {"temp_item_A": "A", "temp_item_B": "B"}.get(k)
    request = rf.get("/x")
    # render() is the dict-with-"scenario" branch; patch it so we don't depend on the
    # archetypist template being collected. Assert the view returned its result.
    sentinel = MagicMock(status_code=200)
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "render", return_value=sentinel) as render_mock,
    ):
        resp = api_mod.get_task_status(request, "task-3")
    render_mock.assert_called_once()
    # the fragment context wires the scenario through to the template
    assert render_mock.call_args.args[2]["scenario"] == "The Forge"
    assert resp is sentinel


@pytest.mark.django_db
def test_get_task_status_cache_error_returns_204(rf):
    request = rf.get("/x")
    with (
        patch.object(api_mod, "get_session_service", return_value=MagicMock()),
        patch.object(api_mod.cache, "get", side_effect=RuntimeError("boom")),
    ):
        resp = api_mod.get_task_status(request, "task-err")
    assert resp.status_code == 204


# --------------------------------------------------------------------------- #
# emoji_decode_stream
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_emoji_decode_stream_invalid_form_returns_400(rf):
    request = rf.get("/x")  # missing target_secret
    resp = api_mod.emoji_decode_stream(request)
    assert resp.status_code == 400
    assert "error" in json.loads(resp.content)


@pytest.mark.django_db
def test_emoji_decode_stream_success_events(rf):
    request = rf.get("/x", {"target_secret": "Naruto"})
    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    fake_container = MagicMock()
    fake_container.catalog_service.load_data.return_value = {
        "title_to_full_data": {"Naruto": {"description": "ninja"}}
    }
    fake_container.emoji_service.generate_emojis_stream.return_value = iter(
        [{"type": "token", "content": "🍥"}, {"type": "done"}]
    )
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.emoji_decode_stream(request)
        events = _sse_events(resp)
    assert {"type": "token", "content": "🍥"} in events


@pytest.mark.django_db
def test_emoji_decode_stream_error_event(rf):
    request = rf.get("/x", {"target_secret": "Naruto"})
    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    fake_container = MagicMock()
    # KeyError on missing title -> error frame in the generator
    fake_container.catalog_service.load_data.return_value = {"title_to_full_data": {}}
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.emoji_decode_stream(request)
        events = _sse_events(resp)
    assert events and events[-1]["type"] == "error"


# --------------------------------------------------------------------------- #
# paradox_stream
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_paradox_stream_invalid_form_returns_400(rf):
    request = rf.get("/x")  # missing item_a/item_b/intruder
    resp = api_mod.paradox_stream(request)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_paradox_stream_success_unwraps_result(rf):
    request = rf.get("/x", {"item_a": "A", "item_b": "B", "intruder": "C"})
    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    session.get.return_value = "Français"
    fake_container = MagicMock()
    fake_container.catalog_service.load_data.return_value = {
        "title_to_full_data": {"A": {}, "B": {}, "C": {}}
    }
    result_obj = SimpleNamespace(reasoning="r", scenario="s")
    fake_container.paradox_service.generate_logic_stream.return_value = iter(
        [
            {"type": "status", "content": "thinking"},
            {"type": "result", "content": result_obj},
        ]
    )
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.paradox_stream(request)
        events = _sse_events(resp)
    result_frame = [e for e in events if e["type"] == "result"][0]
    assert result_frame["content"] == {"reasoning": "r", "scenario": "s"}


@pytest.mark.django_db
def test_paradox_stream_error_event(rf):
    request = rf.get("/x", {"item_a": "A", "item_b": "B", "intruder": "C"})
    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    session.get.return_value = "Français"
    fake_container = MagicMock()
    # items present (dict access succeeds), but the service raises inside the try
    fake_container.catalog_service.load_data.return_value = {
        "title_to_full_data": {"A": {}, "B": {}, "C": {}}
    }
    fake_container.paradox_service.generate_logic_stream.side_effect = RuntimeError(
        "logic boom"
    )
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.paradox_stream(request)
        events = _sse_events(resp)
    assert events and events[-1]["type"] == "error"
    assert "logic boom" in events[-1]["content"]


# --------------------------------------------------------------------------- #
# agentic_rag_stream
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_agentic_rag_stream_invalid_form_returns_400(rf):
    request = rf.get("/x")  # missing query
    resp = api_mod.agentic_rag_stream(request)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_agentic_rag_stream_success_events(rf):
    request = rf.get("/x", {"query": "Who is Luffy?"})
    request.user = AnonymousUser()
    session = MagicMock()
    session.get_current_mode.return_value = "Manga"
    agent = MagicMock()
    agent.plan_and_solve_stream.return_value = iter(
        [{"type": "token", "content": "Luffy"}]
    )
    fake_container = MagicMock()
    fake_container.agentic_rag = agent
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.agentic_rag_stream(request)
        assert resp["Cache-Control"] == "no-cache"
        events = _sse_events(resp)
    assert {"type": "token", "content": "Luffy"} in events


@pytest.mark.django_db
def test_agentic_rag_stream_error_event(rf):
    request = rf.get("/x", {"query": "x"})
    request.user = AnonymousUser()
    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    agent = MagicMock()
    agent.plan_and_solve_stream.side_effect = RuntimeError("kaboom")
    fake_container = MagicMock()
    fake_container.agentic_rag = agent
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.agentic_rag_stream(request)
        events = _sse_events(resp)
    assert events and events[-1]["type"] == "error"
    assert "kaboom" in events[-1]["content"]


# --------------------------------------------------------------------------- #
# animinator_stream
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_animinator_stream_invalid_form_returns_400(rf):
    request = rf.get("/x")  # missing question
    resp = api_mod.animinator_stream(request)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_animinator_stream_no_secret_returns_400(rf):
    request = rf.get("/x", {"question": "Is it a hero?"})
    session = MagicMock()
    session.get.side_effect = lambda k, default=None: {"media_type": "Anime"}.get(
        k, default
    )  # animinator_secret absent -> None
    fake_container = MagicMock()
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.animinator_stream(request)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_animinator_stream_success_tokens_and_done(rf):
    request = rf.get("/x", {"question": "Is it a hero?"})
    store = {
        "media_type": "Anime",
        "animinator_secret": "Naruto",
        "animinator_chat": [],
        "animinator_questions_left": 5,
    }
    session = MagicMock()
    session.get.side_effect = lambda k, default=None: store.get(k, default)
    session.set.side_effect = lambda k, v: store.__setitem__(k, v)
    fake_container = MagicMock()
    fake_container.animinator_service.ask_oracle_stream.return_value = iter(
        ["Yes", " it ", "is"]
    )
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.animinator_stream(request)
        events = _sse_events(resp)
    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-1] == "done"
    assert events[-1]["questions_left"] == 4


@pytest.mark.django_db
def test_animinator_stream_last_question_persists_session(rf):
    """questions_left reaches 0 -> game over + GameplaySession row created."""
    from animetix.models import GameplaySession

    request = rf.get("/x", {"question": "final?"})
    store = {
        "media_type": "Anime",
        "animinator_secret": "Bleach",
        "animinator_chat": [],
        "animinator_questions_left": 1,
    }
    session = MagicMock()
    session.get.side_effect = lambda k, default=None: store.get(k, default)
    session.set.side_effect = lambda k, v: store.__setitem__(k, v)
    fake_container = MagicMock()
    fake_container.animinator_service.ask_oracle_stream.return_value = iter(["Done"])
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.animinator_stream(request)
        events = _sse_events(resp)
    assert events[-1]["type"] == "done"
    assert GameplaySession.objects.filter(
        game_mode="animinator", target_item="Bleach"
    ).exists()


@pytest.mark.django_db
def test_animinator_stream_error_event(rf):
    request = rf.get("/x", {"question": "boom?"})
    store = {"media_type": "Anime", "animinator_secret": "Naruto"}
    session = MagicMock()
    session.get.side_effect = lambda k, default=None: store.get(k, default)
    fake_container = MagicMock()
    fake_container.animinator_service.ask_oracle_stream.side_effect = RuntimeError(
        "oracle down"
    )
    with (
        patch.object(api_mod, "get_session_service", return_value=session),
        patch.object(api_mod, "get_container", return_value=fake_container),
    ):
        resp = api_mod.animinator_stream(request)
        events = _sse_events(resp)
    assert events and events[-1]["type"] == "error"

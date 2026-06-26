"""Coverage tests for animetix.views.api.

``get_task_status`` is a module-level function view that is not wired into the
URL conf via this module (the routed streaming endpoints live in
``animetix.api.streams``). It is driven directly with a ``RequestFactory``
request, with the ``get_session_service`` collaborator patched at the module
level so no real DI / cache is exercised.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from animetix.views import api as api_mod
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

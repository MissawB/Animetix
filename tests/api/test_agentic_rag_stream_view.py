import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from animetix.api import streams as streams_mod
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory


async def _sse_events(response):
    events = []
    async for chunk in response.streaming_content:
        text = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


@pytest.mark.asyncio
async def test_agentic_rag_async_stream_serializes_events():
    request = RequestFactory().get("/x", {"q": "why?"})
    request.auser = AsyncMock(return_value=AnonymousUser())

    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    session.get.return_value = "Français"

    async def _agen(query, media_type, user_id=None, language="Français"):
        yield {"type": "thought", "content": "..."}
        yield {"type": "token", "content": "hi"}

    agent = MagicMock()
    agent.aplan_and_solve_stream.side_effect = _agen

    with (
        patch.object(streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)),
        patch.object(
            streams_mod, "_charge_bx_or_402", new=AsyncMock(return_value=None)
        ),
        patch.object(streams_mod, "get_session_service", return_value=session),
    ):
        view = streams_mod.AgenticRAGStreamView(agentic_rag=agent)
        resp = await view.get(request)
        events = await _sse_events(resp)

    assert any(e["type"] == "token" and e["content"] == "hi" for e in events)
    assert not any(e.get("type") == "error" for e in events)


@pytest.mark.asyncio
async def test_agentic_rag_async_stream_no_query_returns_400():
    request = RequestFactory().get("/x")  # no q
    with patch.object(
        streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)
    ):
        view = streams_mod.AgenticRAGStreamView(agentic_rag=MagicMock())
        resp = await view.get(request)
    assert resp.status_code == 400

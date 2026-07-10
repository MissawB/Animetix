import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from animetix.api import streams as streams_mod
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
async def test_tot_async_stream_serializes_service_events():
    request = RequestFactory().get("/x", {"q": "why?", "breadth": "2", "depth": "1"})

    async def _agen(query, breadth, depth):
        yield {"type": "node_created", "data": {"id": "root", "parent_id": None}}
        yield {"type": "final_answer", "data": {"text": "ok"}}

    tot_service = MagicMock()
    tot_service.asolve_with_tree_of_thoughts_stream.side_effect = _agen

    with (
        patch.object(streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)),
        patch.object(
            streams_mod, "_charge_bx_or_402", new=AsyncMock(return_value=None)
        ),
    ):
        view = streams_mod.ToTStreamView(tot_service=tot_service)
        resp = await view.get(request)
        events = await _sse_events(resp)

    assert any(
        e["type"] == "final_answer" and e["data"]["text"] == "ok" for e in events
    )
    assert not any(e.get("type") == "error" for e in events)


@pytest.mark.asyncio
async def test_tot_async_stream_invalid_form_returns_400():
    request = RequestFactory().get("/x")  # missing q
    with patch.object(
        streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)
    ):
        view = streams_mod.ToTStreamView(tot_service=MagicMock())
        resp = await view.get(request)
    assert resp.status_code == 400

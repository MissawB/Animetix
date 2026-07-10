import json
from types import SimpleNamespace
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
async def test_paradox_async_stream_transforms_result_paradoxlogic():
    request = RequestFactory().get("/x", {"t1": "A", "t2": "B", "intruder": "I"})

    session = MagicMock()
    session.get_current_mode.return_value = "Anime"
    session.get.return_value = "Français"

    # Services are constructor-injected: pass the mocks directly.
    catalog_service = MagicMock()
    catalog_service.load_data.return_value = {
        "title_to_full_data": {
            "A": {"title": "A"},
            "B": {"title": "B"},
            "I": {"title": "I"},
        }
    }

    async def _agen(media_type, item_a, item_b, intruder, language):
        yield {"type": "thought", "content": "..."}
        yield {
            "type": "result",
            "content": SimpleNamespace(reasoning="R", scenario="S"),
        }

    paradox_service = MagicMock()
    paradox_service.agenerate_logic_stream.side_effect = _agen

    with (
        patch.object(streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)),
        patch.object(
            streams_mod, "_charge_bx_or_402", new=AsyncMock(return_value=None)
        ),
        patch.object(streams_mod, "get_session_service", return_value=session),
    ):
        view = streams_mod.ParadoxStreamView(
            catalog_service=catalog_service, paradox_service=paradox_service
        )
        resp = await view.get(request)
        events = await _sse_events(resp)

    result = [e for e in events if e["type"] == "result"]
    assert result and result[0]["content"] == {"reasoning": "R", "scenario": "S"}
    assert not any(e.get("type") == "error" for e in events)


@pytest.mark.asyncio
async def test_paradox_async_stream_missing_params_returns_400():
    request = RequestFactory().get("/x", {"t1": "A"})  # incomplet
    with patch.object(
        streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)
    ):
        view = streams_mod.ParadoxStreamView(
            catalog_service=MagicMock(), paradox_service=MagicMock()
        )
        resp = await view.get(request)
    assert resp.status_code == 400

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
async def test_emoji_async_stream_serializes_service_events():
    request = RequestFactory().get("/x", {"secret": "Naruto"})

    session = MagicMock()
    session.get_current_mode.return_value = "Anime"

    container = MagicMock()
    container.core.catalog_service.load_data.return_value = {
        "title_to_full_data": {"Naruto": {"description": "ninja"}}
    }

    async def _agen(media_type, secret, description):
        yield {"type": "thought", "content": "..."}
        yield {"type": "result", "content": ["🍥", "🦊"]}

    container.core.emoji_service.agenerate_emojis_stream.side_effect = _agen

    with (
        patch.object(streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)),
        patch.object(streams_mod, "get_session_service", return_value=session),
        patch.object(streams_mod, "get_container", return_value=container),
    ):
        resp = await streams_mod.EmojiStreamView().get(request)
        events = await _sse_events(resp)

    assert {"type": "result", "content": ["🍥", "🦊"]} in events
    assert not any(e.get("type") == "error" for e in events)


@pytest.mark.asyncio
async def test_emoji_async_stream_missing_secret_returns_400():
    request = RequestFactory().get("/x")  # no secret
    with patch.object(
        streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)
    ):
        resp = await streams_mod.EmojiStreamView().get(request)
    assert resp.status_code == 400

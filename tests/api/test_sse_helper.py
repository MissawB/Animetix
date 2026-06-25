"""Unit tests for the shared SSE async helper."""

import json
from unittest.mock import patch

import pytest
from animetix.api import sse
from django.test import RequestFactory
from django_ratelimit.exceptions import Ratelimited


async def _collect(response):
    out = []
    async for chunk in response.streaming_content:
        out.append(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk)
    return "".join(out)


@pytest.mark.asyncio
async def test_sse_stream_response_serializes_events():
    async def events():
        yield {"type": "thought", "content": "a"}
        yield {"type": "result", "content": [1, 2]}

    resp = sse.sse_stream_response(events())
    body = await _collect(resp)
    assert 'data: {"type": "thought", "content": "a"}\n\n' in body
    assert '"result"' in body
    assert resp["content-type"] == "text/event-stream"


@pytest.mark.asyncio
async def test_sse_stream_response_error_fallback():
    async def events():
        yield {"type": "thought", "content": "a"}
        raise RuntimeError("boom")

    resp = sse.sse_stream_response(events())
    body = await _collect(resp)
    frames = [
        json.loads(line[len("data: ") :])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    assert frames[0] == {"type": "thought", "content": "a"}
    assert frames[-1] == {"type": "error", "content": "boom"}


@pytest.mark.asyncio
async def test_check_rate_limit_raises_when_limited():
    request = RequestFactory().get("/x")
    with patch.object(sse, "is_ratelimited", return_value=True):
        with pytest.raises(Ratelimited):
            await sse.check_rate_limit(request, "g")


@pytest.mark.asyncio
async def test_check_rate_limit_passes_when_not_limited():
    request = RequestFactory().get("/x")
    with patch.object(sse, "is_ratelimited", return_value=False):
        await sse.check_rate_limit(request, "g")  # ne lève pas

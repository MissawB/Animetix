"""Tests for the async AniminatorStreamView (native Django async SSE view).

The view is a coroutine returning a StreamingHttpResponse with an async body.
Collaborators are patched at the streams-module namespace; the response body is
consumed via async iteration over streaming_content.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from animetix.api import streams as streams_mod
from core.domain.entities.ai_schemas import InferenceResponse
from django.test import RequestFactory
from django_ratelimit.exceptions import Ratelimited


async def _sse_events(response):
    events = []
    async for chunk in response.streaming_content:
        text = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


def _session_mock():
    session = MagicMock()

    def _sget(key, default=None):
        return {
            "media_type": "Anime",
            "animinator_secret": "Naruto",
            "animinator_chat": [],
            "animinator_questions_left": 20,
        }.get(key, default)

    session.get.side_effect = _sget
    return session


def _container_with_chunks(chunks):
    container = MagicMock()

    async def _astream(media_type, secret, question):
        for c in chunks:
            yield c

    container.core.animinator_service.aask_oracle_stream.side_effect = _astream
    return container


@pytest.mark.asyncio
async def test_animinator_async_stream_emits_text_tokens_no_error():
    request = RequestFactory().get("/x", {"q": "Is it a ninja?"})
    container = _container_with_chunks(
        [InferenceResponse(text="Hel"), InferenceResponse(text="lo")]
    )
    with (
        patch.object(streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)),
        patch.object(streams_mod, "get_session_service", return_value=_session_mock()),
        patch.object(streams_mod, "get_container", return_value=container),
    ):
        resp = await streams_mod.AniminatorStreamView().get(request)
        events = await _sse_events(resp)

    token_events = [e for e in events if e.get("type") == "token"]
    assert "".join(e["content"] for e in token_events) == "Hello"
    assert not any(e.get("type") == "error" for e in events)
    assert any(e.get("type") == "done" for e in events)


@pytest.mark.asyncio
async def test_animinator_async_stream_sets_cache_control_no_cache():
    # SSE must not be buffered/cached by intermediaries — parity with the other
    # SSE views (which set this via the shared sse_stream_response helper).
    request = RequestFactory().get("/x", {"q": "Is it a ninja?"})
    container = _container_with_chunks([InferenceResponse(text="hi")])
    with (
        patch.object(streams_mod, "check_rate_limit", new=AsyncMock(return_value=None)),
        patch.object(streams_mod, "get_session_service", return_value=_session_mock()),
        patch.object(streams_mod, "get_container", return_value=container),
    ):
        resp = await streams_mod.AniminatorStreamView().get(request)

    assert resp["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_animinator_async_stream_rate_limited_raises():
    request = RequestFactory().get("/x", {"q": "hi"})
    with patch.object(
        streams_mod, "check_rate_limit", new=AsyncMock(side_effect=Ratelimited())
    ):
        with pytest.raises(Ratelimited):
            await streams_mod.AniminatorStreamView().get(request)

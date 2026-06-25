"""Regression test for the AniminatorStreamView SSE token-type bug.

The inference engine yields InferenceResponse objects; the view must read
`.text` (not treat the chunk as a string). Driven by calling `.get()` directly
(bypassing DRF dispatch / ratelimit) with the streams-module collaborators
patched, then decoding the StreamingHttpResponse SSE frames.
"""

import json
from unittest.mock import MagicMock, patch

from animetix.api import streams as streams_mod
from core.domain.entities.ai_schemas import InferenceResponse
from django.test import RequestFactory


def _sse_events(response):
    events = []
    for chunk in response.streaming_content:
        text = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


def test_animinator_stream_view_emits_text_tokens_no_error():
    request = RequestFactory().get("/x", {"q": "Is it a ninja?"})

    session = MagicMock()

    def _sget(key, default=None):
        return {
            "media_type": "Anime",
            "animinator_secret": "Naruto",
            "animinator_chat": [],
            "animinator_questions_left": 20,
        }.get(key, default)

    session.get.side_effect = _sget

    container = MagicMock()
    container.core.animinator_service.ask_oracle_stream.return_value = iter(
        [InferenceResponse(text="Hel"), InferenceResponse(text="lo")]
    )

    with (
        patch.object(streams_mod, "get_session_service", return_value=session),
        patch.object(streams_mod, "get_container", return_value=container),
    ):
        resp = streams_mod.AniminatorStreamView().get(request)
        events = _sse_events(resp)

    token_events = [e for e in events if e.get("type") == "token"]
    assert "".join(e["content"] for e in token_events) == "Hello"
    assert not any(e.get("type") == "error" for e in events)
    assert any(e.get("type") == "done" for e in events)

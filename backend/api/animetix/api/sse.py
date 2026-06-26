"""Shared helpers for native async Server-Sent-Events (SSE) views."""

import json

from asgiref.sync import sync_to_async
from django.http import StreamingHttpResponse
from django_ratelimit.core import is_ratelimited
from django_ratelimit.exceptions import Ratelimited


async def check_rate_limit(request, group, rate="5/m"):
    """Rate-limit guard for async views (equivalent of the sync @ratelimit
    decorator). Raises Ratelimited (a PermissionDenied subclass -> 403)."""
    limited = await sync_to_async(is_ratelimited)(
        request=request,
        group=group,
        key="user_or_ip",
        rate=rate,
        method="GET",
        increment=True,
    )
    if limited:
        raise Ratelimited()


def sse_stream_response(event_aiter):
    """Wrap an async iterator of JSON-serializable dict events into an SSE
    StreamingHttpResponse, with a {'type':'error'} fallback frame on exception."""

    async def _gen():
        try:
            async for event in event_aiter:
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    response = StreamingHttpResponse(_gen(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response

import json

from asgiref.sync import sync_to_async
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views import View

from animetix.api.dependencies import get_session_service
from animetix.api.sse import check_rate_limit, sse_stream_response

from ..containers import get_container
from ..forms import ToTStreamForm


class EmojiStreamView(View):
    """Async SSE: streams emoji generation events for the UI."""

    async def get(self, request):
        await check_rate_limit(request, "animetix.api.streams.EmojiStreamView")
        secret = request.GET.get("secret")
        if not secret:
            return HttpResponse(status=400)
        session = await sync_to_async(get_session_service)(request)
        media_type = await sync_to_async(session.get_current_mode)()
        container = get_container()
        data = await sync_to_async(container.core.catalog_service.load_data)(media_type)
        description = data["title_to_full_data"][secret].get("description", "")
        return sse_stream_response(
            container.core.emoji_service.agenerate_emojis_stream(
                media_type, secret, description
            )
        )


class ParadoxStreamView(View):
    """Async SSE: streams paradox logic generation events."""

    async def get(self, request):
        await check_rate_limit(request, "animetix.api.streams.ParadoxStreamView")
        t1, t2, intruder = (
            request.GET.get("t1"),
            request.GET.get("t2"),
            request.GET.get("intruder"),
        )
        if not all([t1, t2, intruder]):
            return HttpResponse(status=400)
        session = await sync_to_async(get_session_service)(request)
        media_type = await sync_to_async(session.get_current_mode)()
        container = get_container()
        data = await sync_to_async(container.core.catalog_service.load_data)(media_type)
        item_a = data["title_to_full_data"][t1]
        item_b = data["title_to_full_data"][t2]
        item_i = data["title_to_full_data"][intruder]
        language = await sync_to_async(session.get)("language", "Français")

        async def _events():
            async for event in container.core.paradox_service.agenerate_logic_stream(
                media_type, item_a, item_b, item_i, language
            ):
                if event["type"] == "result":
                    event["content"] = {
                        "reasoning": event["content"].reasoning,
                        "scenario": event["content"].scenario,
                    }
                yield event

        return sse_stream_response(_events())


class AgenticRAGStreamView(View):
    """Async SSE: streams agentic RAG planning and solving events."""

    async def get(self, request):
        await check_rate_limit(request, "animetix.api.streams.AgenticRAGStreamView")
        query = request.GET.get("q", "")
        if not query:
            return JsonResponse({"error": "No query provided"}, status=400)

        session = await sync_to_async(get_session_service)(request)
        media_type = (
            request.GET.get("media_type")
            or await sync_to_async(session.get_current_mode)()
        )

        lang_param = request.GET.get("lang")
        if lang_param:
            language = (
                "English"
                if ("en" in lang_param.lower() or "eng" in lang_param.lower())
                else "Français"
            )
        else:
            language = await sync_to_async(session.get)("language", "Français")

        user = await request.auser()
        if user.is_authenticated:
            from core.domain.services.berrix_economy import (  # noqa: E402
                FEATURE_BX_COSTS,
            )

            from animetix.api.billing import deduct_berrix  # noqa: E402

            try:
                await sync_to_async(deduct_berrix)(
                    user, FEATURE_BX_COSTS["agentic_rag"], "Agentic RAG / Chatbot"
                )
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=402)

        agent = get_container().agentic.agentic_rag()
        user_id = str(user.id) if user.is_authenticated else None
        return sse_stream_response(
            agent.aplan_and_solve_stream(
                query, media_type, user_id=user_id, language=language
            )
        )


class AniminatorStreamView(View):
    """Async SSE: streams the Oracle's response and updates game state in session."""

    async def get(self, request):
        await check_rate_limit(request, "animetix.api.streams.AniminatorStreamView")

        session = await sync_to_async(get_session_service)(request)
        container = get_container()
        media_type = await sync_to_async(session.get)("media_type", "Anime")
        secret = await sync_to_async(session.get)("animinator_secret")
        question = request.GET.get("q")
        if not secret or not question:
            return HttpResponse(status=400)

        async def event_stream():
            full_response = ""
            try:
                async for token in container.core.animinator_service.aask_oracle_stream(
                    media_type, secret, question
                ):
                    full_response += token.text
                    yield f"data: {json.dumps({'type': 'token', 'content': token.text})}\n\n"

                chat = await sync_to_async(session.get)("animinator_chat", [])
                chat.append({"q": question, "a": full_response})
                await sync_to_async(session.set)("animinator_chat", chat)

                q_left = (
                    await sync_to_async(session.get)("animinator_questions_left", 20)
                ) - 1
                await sync_to_async(session.set)(
                    "animinator_questions_left", max(0, q_left)
                )

                if q_left <= 0:
                    await sync_to_async(session.set)("animinator_game_over", True)
                    from ..models import GameplaySession  # noqa: E402

                    await sync_to_async(GameplaySession.objects.create)(
                        game_mode="animinator",
                        media_type=media_type,
                        target_item=secret,
                        history=chat,
                        was_won=False,
                    )
                yield f"data: {json.dumps({'type': 'done', 'questions_left': q_left})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


class ToTStreamView(View):
    """Async SSE: streams Tree-of-Thoughts search node/answer events."""

    async def get(self, request):
        await check_rate_limit(request, "animetix.api.streams.ToTStreamView")
        form = ToTStreamForm(request.GET)
        if not form.is_valid():
            return JsonResponse({"error": form.errors}, status=400)
        query = form.cleaned_data["q"]
        breadth = form.cleaned_data.get("breadth") or 3
        depth = form.cleaned_data.get("depth") or 3
        tot_service = get_container().core.tree_of_thoughts_service()
        return sse_stream_response(
            tot_service.asolve_with_tree_of_thoughts_stream(
                query=query, breadth=breadth, depth=depth
            )
        )

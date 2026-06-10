import json
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from ..containers import get_container
from animetix.api.dependencies import get_session_service

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class EmojiStreamView(APIView):
    """Streams emoji generation events for the UI."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        session = get_session_service(request)
        media_type, secret = session.get_current_mode(), request.GET.get('secret')
        if not secret: return HttpResponse(status=400)
        
        container = get_container()
        data = container.core.catalog_service.load_data(media_type)
        
        def event_stream():
            try:
                for event in container.core.emoji_service.generate_emojis_stream(media_type, secret, data['title_to_full_data'][secret].get('description', '')):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class ParadoxStreamView(APIView):
    """Streams paradox logic generation events."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        session = get_session_service(request)
        container = get_container()
        media_type = session.get_current_mode()
        data = container.core.catalog_service.load_data(media_type)
        t1, t2, intruder = request.GET.get('t1'), request.GET.get('t2'), request.GET.get('intruder')
        if not all([t1, t2, intruder]): return HttpResponse(status=400)
        
        def event_stream():
            item_a, item_b, item_i = data['title_to_full_data'][t1], data['title_to_full_data'][t2], data['title_to_full_data'][intruder]
            try:
                for event in container.core.paradox_service.generate_logic_stream(media_type, item_a, item_b, item_i, session.get('language', 'Français')):
                    if event['type'] == 'result': 
                        event['content'] = {'reasoning': event['content'].reasoning, 'scenario': event['content'].scenario}
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class AgenticRAGStreamView(APIView):
    """Streams agentic RAG planning and solving events."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        session = get_session_service(request)
        query = request.GET.get('q', '')
        media_type = request.GET.get('media_type') or session.get_current_mode()
        
        if not query: 
            return JsonResponse({'error': 'No query provided'}, status=400)
            
        def event_stream():
            agent = get_container().agentic.agentic_rag()
            user_id = str(request.user.id) if request.user.is_authenticated else None
            try:
                for event in agent.plan_and_solve_stream(query, media_type, user_id=user_id):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class AniminatorStreamView(APIView):
    """Streams the Oracle's response and updates the game state in session."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        session = get_session_service(request)
        container = get_container()
        media_type = session.get('media_type', 'Anime')
        secret = session.get('animinator_secret')
        question = request.GET.get('q')
        if not secret or not question: return HttpResponse(status=400)
        
        def event_stream():
            full_response = ""
            try:
                for token in container.core.animinator_service.ask_oracle_stream(media_type, secret, question):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                chat = session.get('animinator_chat', [])
                chat.append({'q': question, 'a': full_response})
                session.set('animinator_chat', chat)
                
                q_left = session.get('animinator_questions_left', 20) - 1
                session.set('animinator_questions_left', max(0, q_left))
                
                if q_left <= 0:
                    session.set('animinator_game_over', True)
                    from ..models import GameplaySession
                    GameplaySession.objects.create(
                        game_mode='animinator', media_type=media_type, 
                        target_item=secret, history=chat, was_won=False
                    )
                yield f"data: {json.dumps({'type': 'done', 'questions_left': q_left})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

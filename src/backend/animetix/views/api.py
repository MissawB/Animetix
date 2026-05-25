import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
from .common import logger
from ..containers import get_container
from animetix.api.dependencies import get_session_service

def get_task_status(request, task_id):
    """Checks the status of a Celery task and returns a result fragment if ready."""
    session = get_session_service(request)
    try:
        res = AsyncResult(task_id)
        if res.ready():
            result = res.result
            if isinstance(result, dict) and 'scenario' in result:
                return render(request, 'animetix/archetypist/archetypist_result_fragment.html', {
                    'reasoning': result.get('reasoning'), 
                    'scenario': result.get('scenario'), 
                    'fusion_image': result.get('fusion_image'), 
                    'item_A': session.get('temp_item_A'), 
                    'item_B': session.get('temp_item_B'),
                    'fusion_id': session.get('last_fusion_id')
                })
            return JsonResponse({'ready': True, 'result': result})
    except Exception as e:
        logger.error(f"⚠️ Celery Result Backend Error: {e}")
        return HttpResponse(status=204)
    return HttpResponse(status=204)

def emoji_decode_stream(request):
    """Streams emoji generation events for the UI."""
    session = get_session_service(request)
    media_type, secret = session.get_current_mode(), request.GET.get('secret')
    if not secret: return HttpResponse(status=400)
    
    container = get_container()
    data = container.catalog_service.load_data(media_type)
    
    def event_stream():
        try:
            for event in container.emoji_service.generate_emojis_stream(media_type, secret, data['title_to_full_data'][secret].get('description', '')):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def paradox_stream(request):
    """Streams paradox logic generation events."""
    session = get_session_service(request)
    container = get_container()
    media_type = session.get_current_mode()
    data = container.catalog_service.load_data(media_type)
    t1, t2, intruder = request.GET.get('t1'), request.GET.get('t2'), request.GET.get('intruder')
    if not all([t1, t2, intruder]): return HttpResponse(status=400)
    
    def event_stream():
        item_a, item_b, item_i = data['title_to_full_data'][t1], data['title_to_full_data'][t2], data['title_to_full_data'][intruder]
        try:
            for event in container.paradox_service.generate_logic_stream(media_type, item_a, item_b, item_i, session.get('language', 'Français')):
                if event['type'] == 'result': 
                    event['content'] = {'reasoning': event['content'].reasoning, 'scenario': event['content'].scenario}
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def agentic_rag_stream(request):
    """Streams agentic RAG planning and solving events."""
    session = get_session_service(request)
    query, media_type = request.GET.get('q', ''), session.get_current_mode()
    if not query: return JsonResponse({'error': 'No query provided'}, status=400)
    def event_stream():
        agent, user_id = get_container().agentic_rag, str(request.user.id) if request.user.is_authenticated else None
        try:
            for event in agent.plan_and_solve_stream(query, media_type, user_id=user_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def animinator_stream(request):
    """Streams the Oracle's response and updates the game state in session."""
    session = get_session_service(request)
    container = get_container()
    media_type = session.get('media_type', 'Anime')
    secret = session.get('animinator_secret')
    question = request.GET.get('q')
    if not secret or not question: return HttpResponse(status=400)
    
    def event_stream():
        full_response = ""
        try:
            for token in container.animinator_service.ask_oracle_stream(media_type, secret, question):
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

@csrf_exempt
def sync_offline_data(request):
    """Synchronizes offline game results with the server profile."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if request.user.is_authenticated:
                xp_gained = 0
                for game in data:
                    if game.get('score', 0) == 100:
                        request.user.profile.add_win(is_daily=False, game_mode=game.get('game_mode', 'classic'), media_type=game.get('media_type', 'Anime'), attempts=game.get('attempts', 1))
                        xp_gained += 10
                if xp_gained > 0:
                    request.user.profile.xp += xp_gained
                    request.user.profile.save()
            return JsonResponse({'status': 'success', 'synced_items': len(data)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=405)

import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from celery.result import AsyncResult
from .common import logger
from ..forms import EmojiStreamForm, ParadoxStreamForm, AgenticRagForm, AniminatorForm
from ..containers import get_container
from animetix.api.dependencies import get_session_service

def get_task_status(request, task_id):
    """Checks the status of a task from cache and returns a result fragment if ready."""
    session = get_session_service(request)
    try:
        task_data = cache.get(f"task_result:{task_id}")
        if task_data and task_data.get("ready"):
            result = task_data.get("result")
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
        logger.error(f"⚠️ Tasks Cache Status Error: {e}")
        return HttpResponse(status=204)
    return HttpResponse(status=204)

def emoji_decode_stream(request):
    """Streams emoji generation events for the UI."""
    form = EmojiStreamForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)
        
    secret = form.cleaned_data['target_secret']
    session = get_session_service(request)
    media_type = session.get_current_mode()
    
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
    form = ParadoxStreamForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)
        
    item_a = form.cleaned_data['item_a']
    item_b = form.cleaned_data['item_b']
    intruder_item = form.cleaned_data['intruder']

    session = get_session_service(request)
    container = get_container()
    media_type = session.get_current_mode()
    data = container.catalog_service.load_data(media_type)
    
    def event_stream():
        item_a_data, item_b_data, item_i_data = data['title_to_full_data'][item_a], data['title_to_full_data'][item_b], data['title_to_full_data'][intruder_item]
        try:
            for event in container.paradox_service.generate_logic_stream(media_type, item_a_data, item_b_data, item_i_data, session.get('language', 'Français')):
                if event['type'] == 'result': 
                    event['content'] = {'reasoning': event['content'].reasoning, 'scenario': event['content'].scenario}
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def agentic_rag_stream(request):
    """Streams agentic RAG planning and solving events."""
    form = AgenticRagForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)
        
    query = form.cleaned_data['query']
    session = get_session_service(request)
    media_type = session.get_current_mode()
    
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
    form = AniminatorForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)
        
    question = form.cleaned_data['question']
    session = get_session_service(request)
    container = get_container()
    media_type = session.get('media_type', 'Anime')
    secret = session.get('animinator_secret')
    if not secret: return HttpResponse(status=400)
    
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

@ratelimit(key='user', rate='1/5m', block=True)
def sync_offline_data(request):
    """
    Synchronizes offline game results with the server profile.
    Secured with rate limiting and daily XP caps to prevent abuse.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
        
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        if not isinstance(data, list):
            return JsonResponse({'error': 'Invalid data format'}, status=400)
            
        # Hard cap on number of items per sync
        if len(data) > 50:
            return JsonResponse({'error': 'Too many items in one sync (max 50)'}, status=400)

        # Track daily gain in cache (persistence = 24h)
        today = datetime.date.today().isoformat()
        cache_key = f"offline_xp_limit_{request.user.id}_{today}"
        daily_gain = cache.get(cache_key, 0)
        
        MAX_DAILY_OFFLINE_XP = 200 # Limite de 200 XP (~20 victoires) par jour via offline sync
        
        if daily_gain >= MAX_DAILY_OFFLINE_XP:
            return JsonResponse({'error': 'Daily offline XP limit reached. Play online for more!'}, status=403)

        xp_gained = 0
        synced_count = 0
        
        for game in data:
            if daily_gain + xp_gained >= MAX_DAILY_OFFLINE_XP:
                break # On arrête l'attribution si le plafond est atteint
                
            if game.get('score', 0) == 100:
                # Validation du mode de jeu pour éviter l'injection de modes fictifs
                mode = game.get('game_mode', 'classic')
                valid_modes = ['classic', 'emoji', 'animinator', 'paradox', 'vision_quest', 'blindtest', 'covertest']
                if mode not in valid_modes:
                    continue
                    
                request.user.profile.add_win(
                    is_daily=False, 
                    game_mode=mode, 
                    media_type=game.get('media_type', 'Anime'), 
                    attempts=game.get('attempts', 1)
                )
                xp_gained += 10
                synced_count += 1

        if xp_gained > 0:
            request.user.profile.xp += xp_gained
            request.user.profile.save()
            # On met à jour le cache avec le nouveau total
            cache.set(cache_key, daily_gain + xp_gained, 60*60*24)

        return JsonResponse({
            'status': 'success', 
            'synced_items': synced_count,
            'xp_gained': xp_gained,
            'daily_total': daily_gain + xp_gained
        })
        
    except Exception as e:
        logger.error(f"❌ Offline Sync Error: {e}")
        return JsonResponse({'error': 'An internal error occurred during synchronization.'}, status=400)

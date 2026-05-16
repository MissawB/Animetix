from django.shortcuts import render, redirect
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from .common import animetix_service, handle_win_achievements, logger
from ..session_manager import GameSessionManager
from ..models import GameplaySession
from ..forms import VisionQuestForm
from core.domain.exceptions import InferenceError

def vision_quest_view(request):
    session = GameSessionManager(request)
    media_type = "Anime"
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    
    is_daily = session.get('is_daily', False)
    state = session.get_vision_state()
    
    if not state['secret_id'] or request.GET.get('new') == '1' or is_daily:
        if is_daily:
            secret_title = session.get('secret_title')
            secret = data['title_to_full_data'].get(secret_title)
        else:
            secret = animetix_service.vision_quest_service.select_secret(data)
        if not secret: return redirect('index')
        session.start_vision_game(str(secret['id']), secret['title'], secret['image'], media_type)
        if is_daily: session.set('is_daily', True)
        state = session.get_vision_state()

    return render(request, 'animetix/vision/game.html', {
        'guesses': state['guesses'], 
        'best_score': state['best_score'], 
        'game_over': state['game_over'], 
        'secret_image': state['image_url'], 
        'secret_title': state['secret_title'] if state['game_over'] else None, 
        'is_daily': is_daily
    })

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def vision_quest_guess(request):
    session = GameSessionManager(request)
    state = session.get_vision_state()
    if request.method == 'POST' and not state['game_over']:
        form = VisionQuestForm(request.POST)
        if form.is_valid():
            try:
                query, secret_id, secret_title, media_type, is_daily = form.cleaned_data['description'], state['secret_id'], state['secret_title'], state['media_type'], state['is_daily']
                score = animetix_service.vision_quest_service.calculate_score(query, secret_id, secret_title, media_type)
                
                guesses = state['guesses']
                guesses.insert(0, {'text': query, 'score': score})
                session.set('vision_guesses', guesses)
                
                if score > state['best_score']: 
                    session.set('vision_best_score', score)
                    
                if animetix_service.vision_quest_service.check_victory(score):
                    session.set('vision_game_over', True)
                    if request.user.is_authenticated:
                        newly_unlocked = request.user.profile.add_win(is_daily=is_daily, game_mode='vision_quest', media_type=media_type, attempts=len(guesses))
                        handle_win_achievements(request, newly_unlocked)
                    GameplaySession.objects.create(game_mode='vision_quest', media_type=media_type, target_item=secret_title, history=guesses, was_won=True)
            except InferenceError as e:
                logger.error(f"Inference Error in Vision Quest: {e}")
                return JsonResponse({'error': "Le moteur d'IA est temporairement indisponible."}, status=503)
            except Exception as e:
                logger.error(f"Unexpected Error in Vision Quest: {e}")
    return redirect('vision_quest')


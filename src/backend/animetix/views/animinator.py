from django.shortcuts import render, redirect
from django_ratelimit.decorators import ratelimit
from .common import animetix_service, handle_win_achievements, logger
from ..session_manager import GameSessionManager
from ..models import GameplaySession
from ..forms import GameGuessForm, AniminatorForm
from core.domain.exceptions import InferenceError

def animinator_view(request):
    manager = GameSessionManager(request)
    media_type, data = manager.get_current_mode(), animetix_service.load_data(manager.get_current_mode())
    if not data: return redirect('index')
    if request.GET.get('new') == '1': manager.set('is_daily', False)
    is_daily = manager.get('is_daily', False)
    if 'animinator_secret' not in request.session or request.GET.get('new') == '1' or is_daily:
        if is_daily: secret = manager.get('secret_title')
        else: secret = animetix_service.animinator_service.select_secret(data)
        if not secret: return redirect('index')
        manager.update({'animinator_secret': secret, 'animinator_chat': [], 'animinator_questions_left': 20, 'animinator_game_over': False})
        if is_daily: manager.set('is_daily', True)
    return render(request, 'animetix/animinator/animinator.html', {'media_type': media_type, 'chat': manager.get('animinator_chat', []), 'questions_left': manager.get('animinator_questions_left', 20), 'game_over': manager.get('animinator_game_over', False), 'is_daily': is_daily, 'secret_title': manager.get('animinator_secret') if manager.get('animinator_game_over') else None, 'remaining_items': [item for item in data['lookup'] if item['title'] in data['title_to_full_data']]})

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def animinator_ask(request):
    manager = GameSessionManager(request)
    if request.method == 'POST' and not manager.get('animinator_game_over'):
        form = AniminatorForm(request.POST)
        if form.is_valid():
            try:
                question = form.cleaned_data['question']
                media_type, data = manager.get_current_mode(), animetix_service.load_data(manager.get_current_mode())
                secret = manager.get('animinator_secret')
                if not data or secret not in data['title_to_full_data']: return redirect('index')
                answer = animetix_service.animinator_service.ask_oracle(media_type, secret, data['title_to_full_data'][secret], question)
                chat = manager.get('animinator_chat', [])
                chat.append({'q': question, 'a': answer})
                manager.set('animinator_chat', chat)
                q_left = manager.get('animinator_questions_left', 20) - 1
                manager.set('animinator_questions_left', q_left)
                if q_left <= 0:
                    manager.set('animinator_game_over', True)
                    GameplaySession.objects.create(game_mode='animinator', media_type=media_type, target_item=secret, history=chat, was_won=False)
            except InferenceError as e:
                logger.error(f"Inference Error in Animinator: {e}")
            except Exception as e:
                logger.error(f"Unexpected Error in Animinator: {e}")
    return redirect('animinator')

def animinator_guess(request):
    manager = GameSessionManager(request)
    if request.method == 'POST' and not manager.get('animinator_game_over'):
        form = GameGuessForm(request.POST)
        if form.is_valid():
            try:
                guess, secret, media_type = form.cleaned_data['guess'], manager.get('animinator_secret'), manager.get_current_mode()
                data = animetix_service.load_data(media_type)
                secret_item = data['title_to_full_data'].get(secret)
                is_correct = animetix_service.game_service.check_title_match(guess, secret_item)
                if is_correct:
                    manager.set('animinator_game_over', True)
                    if request.user.is_authenticated: 
                        newly_unlocked = request.user.profile.add_win(is_daily=manager.get('is_daily', False), game_mode='animinator', media_type=media_type, attempts=len(manager.get('animinator_chat', [])))
                        handle_win_achievements(request, newly_unlocked)
                    GameplaySession.objects.create(game_mode='animinator', media_type=media_type, target_item=secret, history=manager.get('animinator_chat', []), was_won=True)
            except Exception as e:
                logger.error(f"Error in Animinator Guess: {e}")
    return redirect('animinator')

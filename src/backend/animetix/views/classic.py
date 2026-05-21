import json
import random
from django.shortcuts import render, redirect
from .common import animetix_service, handle_win_achievements
from ..presenters import ArchetypistPresenter, GamePresenter
from ..session_manager import GameSessionManager
from ..models import GameplaySession
from ..forms import GameGuessForm
from ..services import DIFFICULTY_SETTINGS

def start_game(request, override_secret=None):
    session = GameSessionManager(request)
    media_type, difficulty = session.get_current_mode(), session.get('difficulty', 'Normal')
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    
    if override_secret: 
        secret_title = override_secret
    else:
        session.update({'is_daily': False, 'is_ranked': False})
        if difficulty == 'Custom':
            config = {
                'mode': session.get('custom_mode', 'all'),
                'whitelist': session.get('custom_whitelist', []),
                'blacklist': session.get('custom_blacklist', []),
                'genres_white': session.get('custom_genres_white', []),
                'genres_black': session.get('custom_genres_black', []),
                'tags_white': session.get('custom_tags_white', []),
                'tags_black': session.get('custom_tags_black', []),
            }
            secret_title = animetix_service.game_service.select_secret_custom(media_type, config, data)
        else:
            secret_title = animetix_service.game_service.select_secret(media_type, difficulty, DIFFICULTY_SETTINGS)

    if not secret_title: return redirect('index')

    session.start_classic_game(secret_title, difficulty, media_type)
    return redirect('game')

def game_view(request):
    session = GameSessionManager(request)
    state = session.get_classic_state()
    media_type, secret_title = state['media_type'], state['secret_title']
    data = animetix_service.load_data(media_type)
    if not data or not secret_title: return redirect('index')
    
    secret_data = data['title_to_full_data'].get(secret_title)
    if not secret_data: return redirect('index')
    
    theme_color = ArchetypistPresenter.get_theme_color(secret_title)
    hints = GamePresenter.format_classic_hints(secret_data, len(state['guesses']), state['revealed_hints'])

    return render(request, 'animetix/classic/game.html', {
        'media_type': media_type, 'guesses': state['guesses'], 'game_over': state['game_over'],
        'guess_count': len(state['guesses']), 'hints': hints, 'radar_data': json.dumps([]), 
        'is_daily': state['is_daily'], 'is_ranked': state['is_ranked'],
        'ranked_points': request.user.profile.ranked_points if request.user.is_authenticated else 0,
        'secret_title': secret_title if state['game_over'] else None, 'secret_data': secret_data if state['game_over'] else None,
        'remaining_items': [item for item in data['lookup'] if item['title'] in data['title_to_full_data']],
        'theme_color': theme_color
    })


def make_guess(request):
    session = GameSessionManager(request)
    state = session.get_classic_state()
    if request.method == 'POST' and not state['game_over']:
        form = GameGuessForm(request.POST)
        if form.is_valid():
            guess_title, media_type = form.cleaned_data['guess'], state['media_type']
            secret_title, max_sim = state['secret_title'], session.get('max_raw_sim', 1.0)
            data = animetix_service.load_data(media_type)
            if not data or guess_title not in data['title_to_index']: return redirect('game')
            
            raw_sim = animetix_service.game_service.calculate_raw_similarity(media_type, secret_title, guess_title, data)
            secret_item = data['title_to_full_data'].get(secret_title)
            is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
            
            score = 100.0 if is_correct else round(min(0.99, (raw_sim / max_sim) * 0.99) * 100, 2)
            color = GamePresenter.get_score_color(score)
            
            g_data = data['title_to_full_data'].get(guess_title, {})
            session.add_guess({"title": guess_title, "title_english": g_data.get('title_english'), "title_native": g_data.get('title_native'), "image": g_data.get('image'), "score": score, "color": color})
            
            if is_correct:
                session.set_game_over(True)
                if request.user.is_authenticated:
                    item_rank = 100
                    for i, item in enumerate(data['lookup']):
                        if (item.get('title') or item.get('name')) == secret_title:
                            item_rank = i + 1; break
                    newly_unlocked = request.user.profile.add_win(is_daily=state['is_daily'], is_ranked=state['is_ranked'], item_rank=item_rank, game_mode='classic', media_type=media_type, attempts=len(state['guesses']) + 1)
                    handle_win_achievements(request, newly_unlocked)
                GameplaySession.objects.create(user=request.user if request.user.is_authenticated else None, game_mode='classic', media_type=media_type, target_item=secret_title, history=session.get('guesses'), was_won=True)
    return redirect('game')

def start_ranked_mode(request):
    session = GameSessionManager(request)
    session.update({'is_ranked': True, 'is_daily': False})
    return ranked_next_level(request)

def ranked_next_level(request):
    session = GameSessionManager(request)
    if not session.get('is_ranked'): return redirect('index')
    media_type = session.get_current_mode()
    data = animetix_service.load_data(media_type)
    points = request.user.profile.ranked_points if request.user.is_authenticated else 0
    rank_limit = min(2500, 100 + int(points / 2))
    valid_lookup = data.get('lookup', [])[:rank_limit]
    valid_titles = [item.get('title') or item.get('name') for item in valid_lookup if (item.get('title') or item.get('name')) in data.get('title_to_full_data', {})]
    if not valid_titles: valid_titles = data.get('titles', [])[:100]
    if not valid_titles: return redirect('index')
    secret_title = random.choice(valid_titles)
    session.start_classic_game(secret_title, "Normal", media_type)
    return redirect('game')

def reveal_hint(request, hint_type):
    session = GameSessionManager(request)
    session.reveal_hint(hint_type)
    return redirect('game')

def abandon_game(request):
    session = GameSessionManager(request)
    session.set_game_over(True)
    return redirect('game')


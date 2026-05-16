from django.shortcuts import render, redirect
from .common import animetix_service, handle_win_achievements
from ..utils import get_current_mode
from ..session_manager import GameSessionManager
from ..models import GameplaySession
from ..forms import GameGuessForm

def emoji_decode_view(request):
    session = GameSessionManager(request)
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': 
        session.update({'is_daily': False, 'is_ranked': False})
    
    state = session.get_emoji_state()
    is_daily, is_ranked = state['is_daily'], state['is_ranked']
    
    if not state['secret'] or request.GET.get('new') == '1' or is_daily or is_ranked:
        if is_daily or is_ranked: 
            secret = session.get('secret_title')
        else: 
            secret = animetix_service.emoji_service.select_secret(data)
            
        if not secret: return redirect('index')
        emoji_list = animetix_service.emoji_service.generate_emojis(media_type, secret, data['title_to_full_data'][secret].get('description', ''))
        session.start_emoji_game(secret, emoji_list)
        if is_daily: session.set('is_daily', True)
        if is_ranked: session.set('is_ranked', True)
        state = session.get_emoji_state()

    remaining_items = [{'t': item.get('title'), 'en': item.get('title_english'), 'jp': item.get('title_native'), 'i': item.get('image')} for item in data['db']]
    return render(request, 'animetix/emoji/game.html', {
        'media_type': media_type, 
        'emojis': state['emojis'], 
        'guesses': state['guesses'], 
        'game_over': state['game_over'], 
        'is_daily': is_daily, 
        'is_ranked': is_ranked, 
        'ranked_points': request.user.profile.ranked_points if request.user.is_authenticated else 0, 
        'remaining_items': remaining_items, 
        'secret_title': state['secret'] if state['game_over'] else None
    })

def emoji_decode_guess(request):
    session = GameSessionManager(request)
    state = session.get_emoji_state()
    if request.method == 'POST' and not state['game_over']:
        form = GameGuessForm(request.POST)
        if form.is_valid():
            guess_title = form.cleaned_data['guess']
            secret, media_type = state['secret'], get_current_mode(request)
            data = animetix_service.load_data(media_type)
            guesses = state['guesses']
            guess_full, secret_item = data['title_to_full_data'].get(guess_title), data['title_to_full_data'].get(secret)
            if guess_full:
                is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
                guesses.append({'title': guess_title, 'title_en': guess_full.get('title_english'), 'title_jp': guess_full.get('title_native'), 'image': guess_full.get('image'), 'is_correct': is_correct})
                session.set('emoji_guesses', guesses)
                if is_correct: 
                    session.set('emoji_game_over', True)
                    if request.user.is_authenticated:
                        item_rank = 100
                        for i, item in enumerate(data['lookup']):
                            if (item.get('title') or item.get('name')) == secret: item_rank = i + 1; break
                        newly_unlocked = request.user.profile.add_win(is_daily=state['is_daily'], is_ranked=state['is_ranked'], item_rank=item_rank, game_mode='emoji', media_type=media_type, attempts=len(guesses))
                        handle_win_achievements(request, newly_unlocked)
                    GameplaySession.objects.create(user=request.user if request.user.is_authenticated else None, game_mode='emoji', media_type=media_type, target_item=secret, history=guesses, was_won=True)
    return redirect('emoji_decode')


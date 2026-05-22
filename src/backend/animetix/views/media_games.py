import datetime
import logging
from django.shortcuts import render, redirect

logger = logging.getLogger('animetix')
from ..containers import get_container
from ..session_manager import GameSessionManager

def blindtest_view(request):
    container = get_container()
    session = GameSessionManager(request)
    media_type = "Anime"
    data = container.catalog_service.load_data(media_type)
    if not data: return redirect('index')
    
    is_daily = session.get('is_daily', False)
    theme_pref = request.GET.get('type')
    state = session.get_blindtest_state()
    
    if request.GET.get('new') == '1' or not state['secret'] or is_daily:
        if is_daily:
            theme = container.blind_test_service.get_daily_theme(datetime.date.today())
        else:
            theme = container.blind_test_service.get_random_theme(theme_type=theme_pref)
            
        if not theme: return redirect('index')
        session.start_blindtest_game(theme)
        if is_daily: session.set('is_daily', True)
        state = session.get_blindtest_state()
        
    return render(request, 'animetix/blindtest/game.html', {
        'video_url': state['video'], 
        'theme_type': state['type'], 
        'theme_pref': theme_pref, 
        'blindtest_song': state['song'], 
        'blindtest_artists': state['artists'], 
        'guesses': state['guesses'], 
        'game_over': state['game_over'], 
        'is_daily': is_daily, 
        'secret_title': state['secret'] if state['game_over'] else None, 
        'remaining_items_json': data.get('autocomplete_json', '[]')
    })

def blindtest_guess(request):
    container = get_container()
    session = GameSessionManager(request)
    state = session.get_blindtest_state()
    
    if request.method == 'POST' and not state['game_over']:
        guess_title = request.POST.get('guess')
        secret = state['secret']
        media_type = "Anime"
        data = container.catalog_service.load_data(media_type)
        is_daily = state['is_daily']
        
        if guess_title:
            secret_item = data['title_to_full_data'].get(secret)
            is_correct = container.game_service.check_title_match(guess_title, secret_item)
            
            guesses = state['guesses']
            guess_full = data['title_to_full_data'].get(guess_title)
            
            if guess_full:
                guesses.append({
                    'title': str(guess_title), 
                    'image': str(guess_full.get('image')) if guess_full.get('image') else None, 
                    'is_correct': bool(is_correct)
                })
                session.set('blindtest_guesses', guesses)
                
                if is_correct:
                    session.set('blindtest_game_over', True)
                    if request.user.is_authenticated:
                        try:
                            newly_unlocked = request.user.profile.add_win(
                                is_daily=is_daily, 
                                game_mode='blindtest', 
                                media_type=media_type, 
                                attempts=len(guesses)
                            )
                            session.handle_win_achievements(newly_unlocked)
                        except Exception: pass
                        
    return redirect('blindtest')

def covertest_view(request):
    container = get_container()
    session = GameSessionManager(request)
    media_type = "Manga"
    data = container.catalog_service.load_data(media_type)
    if not data: return redirect('index')
    
    is_daily = session.get('is_daily', False)
    state = session.get_covertest_state()
    
    if request.GET.get('new') == '1' or not state['secret'] or is_daily:
        if is_daily:
            cover = container.cover_test_service.get_daily_cover(datetime.date.today())
        else:
            cover = container.cover_test_service.get_random_cover()
            
        if not cover: return redirect('index')
        session.start_covertest_game(cover)
        if is_daily: session.set('is_daily', True)
        state = session.get_covertest_state()
        
    return render(request, 'animetix/manga/cover_test.html', {
        'cover_url': state['url'], 
        'locale': state['locale'], 
        'volume': state['volume'], 
        'guesses': state['guesses'], 
        'game_over': state['game_over'], 
        'is_daily': is_daily, 
        'secret_title': state['secret'] if state['game_over'] else None, 
        'remaining_items_json': data.get('autocomplete_json', '[]')
    })

def covertest_guess(request):
    container = get_container()
    session = GameSessionManager(request)
    state = session.get_covertest_state()
    
    if request.method == 'POST' and not state['game_over']:
        guess_title = request.POST.get('guess')
        secret = state['secret']
        media_type = "Manga"
        data = container.catalog_service.load_data(media_type)
        is_daily = state['is_daily']
        
        if guess_title:
            secret_item = data['title_to_full_data'].get(secret)
            is_correct = container.game_service.check_title_match(guess_title, secret_item)
            
            guesses = state['guesses']
            guess_full = data['title_to_full_data'].get(guess_title)
            
            if guess_full:
                guesses.append({
                    'title': str(guess_title), 
                    'image': str(guess_full.get('image')) if guess_full.get('image') else None, 
                    'is_correct': bool(is_correct)
                })
                session.set('covertest_guesses', guesses)
                
                if is_correct:
                    session.set('covertest_game_over', True)
                    if request.user.is_authenticated:
                        try:
                            newly_unlocked = request.user.profile.add_win(
                                is_daily=is_daily, 
                                game_mode='covertest', 
                                media_type=media_type, 
                                attempts=len(guesses)
                            )
                            session.handle_win_achievements(newly_unlocked)
                        except Exception: pass
                        
    return redirect('covertest')


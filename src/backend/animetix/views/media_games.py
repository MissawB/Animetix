import datetime
from django.shortcuts import render, redirect
from .common import animetix_service, blindtest_service, covertest_service, handle_win_achievements
from ..session_manager import GameSessionManager

def blindtest_view(request):
    session = GameSessionManager(request)
    media_type, data = "Anime", animetix_service.load_data("Anime")
    if not data: return redirect('index')
    
    is_daily, theme_pref = session.get('is_daily', False), request.GET.get('type')
    state = session.get_blindtest_state()
    
    if request.GET.get('new') == '1' or not state['secret'] or is_daily:
        if is_daily: theme = blindtest_service.get_daily_theme(datetime.date.today())
        else: theme = blindtest_service.get_random_theme(theme_type=theme_pref)
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
    session = GameSessionManager(request)
    state = session.get_blindtest_state()
    if request.method == 'POST' and not state['game_over']:
        guess_title, secret, media_type = request.POST.get('guess'), state['secret'], "Anime"
        data, is_daily = animetix_service.load_data("Anime"), state['is_daily']
        if guess_title:
            secret_item = data['title_to_full_data'].get(secret)
            is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
            guesses, guess_full = state['guesses'], data['title_to_full_data'].get(guess_title)
            if guess_full:
                guesses.append({'title': str(guess_title), 'image': str(guess_full.get('image')) if guess_full.get('image') else None, 'is_correct': bool(is_correct)})
                session.set('blindtest_guesses', guesses)
                if is_correct:
                    session.set('blindtest_game_over', True)
                    if request.user.is_authenticated:
                        newly_unlocked = request.user.profile.add_win(is_daily=is_daily, game_mode='blindtest', media_type=media_type, attempts=len(guesses))
                        handle_win_achievements(request, newly_unlocked)
    return redirect('blindtest')

def covertest_view(request):
    session = GameSessionManager(request)
    media_type, data = "Manga", animetix_service.load_data("Manga")
    if not data: return redirect('index')
    
    is_daily = session.get('is_daily', False)
    state = session.get_covertest_state()
    
    if request.GET.get('new') == '1' or not state['secret'] or is_daily:
        if is_daily: cover = covertest_service.get_daily_cover(datetime.date.today())
        else: cover = covertest_service.get_random_cover()
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
    session = GameSessionManager(request)
    state = session.get_covertest_state()
    if request.method == 'POST' and not state['game_over']:
        guess_title, secret, media_type = request.POST.get('guess'), state['secret'], "Manga"
        data, is_daily = animetix_service.load_data("Manga"), state['is_daily']
        if guess_title:
            secret_item = data['title_to_full_data'].get(secret)
            is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
            guesses, guess_full = state['guesses'], data['title_to_full_data'].get(guess_title)
            if guess_full:
                guesses.append({'title': str(guess_title), 'image': str(guess_full.get('image')) if guess_full.get('image') else None, 'is_correct': bool(is_correct)})
                session.set('covertest_guesses', guesses)
                if is_correct:
                    session.set('covertest_game_over', True)
                    if request.user.is_authenticated:
                        newly_unlocked = request.user.profile.add_win(is_daily=is_daily, game_mode='covertest', media_type=media_type, attempts=len(guesses))
                        handle_win_achievements(request, newly_unlocked)
    return redirect('covertest')


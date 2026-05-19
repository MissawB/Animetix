import random
from django.shortcuts import render, redirect
from .common import animetix_service, handle_win_achievements
from ..session_manager import GameSessionManager
from ..forms import GameGuessForm

def paradox_view(request):
    session = GameSessionManager(request)
    media_type, data = session.get_current_mode(), animetix_service.load_data(session.get_current_mode())
    if not data: return redirect('index')
    
    is_daily = session.get('is_daily', False)
    state = session.get_paradox_state()
    
    if not (is_daily and state['answer'] == session.get('secret_title')):
        res_prepare = animetix_service.paradox_service.prepare_challenge(data, is_daily, session.get('secret_title'))
        if not res_prepare or len(res_prepare) < 3: return redirect('index')
        t1, t2, intruder = res_prepare
        res = animetix_service.paradox_service.generate_logic(media_type, data['title_to_full_data'][t1], data['title_to_full_data'][t2], data['title_to_full_data'][intruder], session.get('language', 'Français'))
        session.start_paradox_game(intruder, [t1, t2, intruder], res.get('reasoning'), res.get('scenario'), media_type)
        if is_daily: session.set('is_daily', True)
        state = session.get_paradox_state()

    options = [{'title': t, 'image': data['title_to_full_data'][t].get('image')} for t in state['options']]
    random.shuffle(options)
    return render(request, 'animetix/paradox/intruder.html', {
        'scenario': state['scenario'], 
        'options': options, 
        'media_type': media_type, 
        'is_daily': is_daily
    })

def paradox_guess(request):
    session = GameSessionManager(request)
    state = session.get_paradox_state()
    if request.method == 'POST':
        form = GameGuessForm(request.POST)
        if form.is_valid():
            choice, answer, titles, media, is_daily = form.cleaned_data['guess'], state['answer'], state['options'], state['media'], state['is_daily']
            is_correct, data = (choice == answer), animetix_service.load_data(media)
            if is_correct and request.user.is_authenticated:
                newly_unlocked = request.user.profile.add_win(is_daily=is_daily, game_mode='paradox', media_type=media, attempts=1)
                handle_win_achievements(request, newly_unlocked)
            final_opts = [{'title': t, 'is_intruder': (t == answer), 'is_user_choice': (t == choice), 'image': data['title_to_full_data'].get(t, {}).get('image') if data else None} for t in titles]
            return render(request, 'animetix/paradox/intruder_result.html', {
                'is_correct': is_correct, 
                'answer': answer, 
                'reasoning': state['reasoning'], 
                'final_options': final_opts, 
                'media_type': media, 
                'is_daily': is_daily
            })
    return redirect('index')

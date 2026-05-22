import random
from django.shortcuts import render, redirect
from .common import animetix_service, handle_win_achievements
from ..forms import GameGuessForm
from src.adapters.persistence.session_state_adapter import DjangoSessionStateAdapter

def paradox_view(request):
    state_port = DjangoSessionStateAdapter(request.session)
    media_type = state_port.get('current_mode', 'Anime')
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    
    is_daily = state_port.get('is_daily', False)
    state = animetix_service.paradox_service.get_state(state_port)
    
    if not (is_daily and state.get('answer') == state_port.get('secret_title')):
        res_prepare = animetix_service.paradox_service.prepare_challenge(data, is_daily, state_port.get('secret_title'))
        if not res_prepare or len(res_prepare) < 3: return redirect('index')
        t1, t2, intruder = res_prepare
        res = animetix_service.paradox_service.generate_logic(media_type, data['title_to_full_data'][t1], data['title_to_full_data'][t2], data['title_to_full_data'][intruder], state_port.get('language', 'Français'))
        
        new_state = {
            'answer': intruder,
            'options': [t1, t2, intruder],
            'reasoning': res.reasoning,
            'scenario': res.scenario,
            'media': media_type,
            'is_daily': is_daily
        }
        animetix_service.paradox_service.save_state(state_port, new_state)
        state = new_state

    options = [{'title': t, 'image': data['title_to_full_data'][t].get('image')} for t in state['options']]
    random.shuffle(options)
    return render(request, 'animetix/paradox/intruder.html', {
        'scenario': state['scenario'], 
        'options': options, 
        'media_type': media_type, 
        'is_daily': is_daily
    })

def paradox_guess(request):
    state_port = DjangoSessionStateAdapter(request.session)
    state = animetix_service.paradox_service.get_state(state_port)
    if request.method == 'POST':
        form = GameGuessForm(request.POST)
        if form.is_valid():
            choice = form.cleaned_data['guess']
            answer = state['answer']
            titles = state['options']
            media = state['media']
            is_daily = state['is_daily']
            
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

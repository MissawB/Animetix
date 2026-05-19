from django.shortcuts import render, redirect
from .common import animetix_service, handle_win_achievements
from ..session_manager import GameSessionManager
from ..models import GameplaySession
from ..forms import AkinetixAnswerForm
from ..containers import get_container

def akinetix_view(request):
    session = GameSessionManager(request)
    media_type = session.get_current_mode()
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': 
        session.update({'akinetix_probs': None, 'akinetix_asked_attrs': None, 'is_daily': False})
    
    is_daily = session.get('is_daily', False)
    state = session.get_akinetix_state()
    
    if not state['current_q'] or request.GET.get('new') == '1' or is_daily:
        game_state = get_container().akinetix_service.start_new_game(data['db'])
        session.start_akinetix_game(game_state)
        if is_daily: session.set('is_daily', True)
        state = session.get_akinetix_state()
        
    return render(request, 'animetix/akinetix/akinetix.html', {
        'media_type': media_type, 
        'current_question': state['current_q'], 
        'history': state['history'], 
        'game_over': state['game_over'], 
        'ai_guess': state['ai_guess'], 
        'is_daily': is_daily
    })

def akinetix_answer(request):
    session = GameSessionManager(request)
    state = session.get_akinetix_state()
    if request.method == 'POST' and not state['game_over']:
        form, raw_answer, media_type = AkinetixAnswerForm(request.POST), "NE SAIT PAS", session.get_current_mode()
        if form.is_valid(): raw_answer = form.cleaned_data['answer']
        data = animetix_service.load_data(media_type)
        if not data: return redirect('index')
        
        new_state = get_container().akinetix_service.process_answer(data['db'], state, raw_answer)
        session.update_akinetix_state(new_state)
    return redirect('akinetix')

def akinetix_confirm(request):
    session = GameSessionManager(request)
    state = session.get_akinetix_state()
    if request.method == 'POST':
        is_correct, media_type = request.POST.get('correct') == 'true', session.get_current_mode()
        if not is_correct and request.user.is_authenticated:
            newly_unlocked = request.user.profile.add_win(is_daily=state['is_daily'], game_mode='akinetix')
            handle_win_achievements(request, newly_unlocked)
        GameplaySession.objects.create(game_mode='akinetix', media_type=media_type, target_item=state['ai_guess'] or "Unknown", history=state['history'], was_won=is_correct)
    return redirect('akinetix', new='1')


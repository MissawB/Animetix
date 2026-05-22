from django.shortcuts import render, redirect
from adapters.persistence.session_state_adapter import DjangoSessionStateAdapter
from ..models import GameplaySession
from ..forms import AkinetixAnswerForm
from ..containers import get_container

def akinetix_view(request):
    container = get_container()
    state_port = DjangoSessionStateAdapter(request.session)
    akinetix_service = container.akinetix_service
    
    media_type = state_port.get('media_type', 'Anime')
    data = container.catalog_service.load_data(media_type)
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': 
        akinetix_service.reset_state(state_port)
    
    state = akinetix_service.get_state(state_port)
    
    if not state.current_q or request.GET.get('new') == '1' or state.is_daily:
        game_state = akinetix_service.start_new_game(data['db'])
        # If it was a new daily request, ensure the new state reflects it
        if state.is_daily or request.GET.get('is_daily') == 'true':
            game_state.is_daily = True
        akinetix_service.save_state(state_port, game_state)
        state = game_state
        
    return render(request, 'animetix/akinetix/akinetix.html', {
        'media_type': media_type, 
        'current_question': state.current_q, 
        'history': state.history, 
        'game_over': state.game_over, 
        'ai_guess': state.ai_guess, 
        'is_daily': state.is_daily
    })

def akinetix_answer(request):
    container = get_container()
    state_port = DjangoSessionStateAdapter(request.session)
    akinetix_service = container.akinetix_service
    state = akinetix_service.get_state(state_port)
    
    if request.method == 'POST' and not state.game_over:
        form = AkinetixAnswerForm(request.POST)
        raw_answer = "NE SAIT PAS"
        media_type = state_port.get('media_type', 'Anime')
        
        if form.is_valid(): 
            raw_answer = form.cleaned_data['answer']
            
        data = container.catalog_service.load_data(media_type)
        if not data: return redirect('index')
        
        new_state = akinetix_service.process_answer(data['db'], state, raw_answer)
        akinetix_service.save_state(state_port, new_state)
        
    return redirect('akinetix')

def akinetix_confirm(request):
    container = get_container()
    state_port = DjangoSessionStateAdapter(request.session)
    akinetix_service = container.akinetix_service
    state = akinetix_service.get_state(state_port)
    
    if request.method == 'POST':
        is_correct = request.POST.get('correct') == 'true'
        media_type = state_port.get('media_type', 'Anime')
        
        if is_correct and request.user.is_authenticated:
            try:
                newly_unlocked = request.user.profile.add_win(
                    is_daily=state.is_daily, 
                    game_mode='akinetix',
                    media_type=media_type
                )
                if newly_unlocked:
                    ach_data = state_port.get('new_achievements', [])
                    for ach in newly_unlocked:
                        ach_data.append({
                            'code': ach.code,
                            'name': ach.name,
                            'icon': ach.icon,
                            'xp': ach.xp_reward
                        })
                    state_port.set('new_achievements', ach_data)
            except Exception: pass
            
        GameplaySession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            game_mode='akinetix', 
            media_type=media_type, 
            target_item=state.ai_guess or "Unknown", 
            history=[h.model_dump() for h in state.history], 
            was_won=is_correct
        )
    return redirect('akinetix', new='1')


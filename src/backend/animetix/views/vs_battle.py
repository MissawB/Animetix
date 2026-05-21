from django.shortcuts import render
from .common import vs_battle_service

def vs_battle_view(request):
    """
    View to handle VS Battle game logic.
    """
    if request.method == 'POST':
        char_a = request.POST.get('char_a')
        char_b = request.POST.get('char_b')
        
        if not char_a or not char_b:
            return render(request, 'animetix/games/vs_battle_select.html', {
                'error': 'Please provide both character names.'
            })
            
        try:
            # We use the language from the session or default to French
            language = request.session.get('django_language', 'Français')
            result = vs_battle_service.run_battle(char_a, char_b, language=language)
            
            return render(request, 'animetix/games/vs_battle_result.html', {
                'result': result,
                'char_a_name': char_a,
                'char_b_name': char_b
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return render(request, 'animetix/games/vs_battle_select.html', {
                'error': f"Error running battle: {str(e)}",
                'char_a': char_a,
                'char_b': char_b
            })
            
    return render(request, 'animetix/games/vs_battle_select.html')

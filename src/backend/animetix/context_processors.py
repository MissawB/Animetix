from .services import TRANSLATIONS

def translation_processor(request):
    """Injecte les textes traduits dans tous les templates."""
    lang = request.session.get('language', 'Français')
    return {
        'txt': TRANSLATIONS.get(lang, TRANSLATIONS['Français']),
        'current_lang': lang
    }

def achievements_processor(request):
    """Injecte les nouveaux succès débloqués pour affichage Toast."""
    new_achievements = request.session.get('new_achievements', [])
    if new_achievements:
        # On vide la session après récupération pour ne pas les afficher deux fois
        request.session['new_achievements'] = []
    return {
        'newly_unlocked_achievements': new_achievements
    }

def features_processor(request):
    """Rend les Feature Flags disponibles dans tous les templates."""
    from django.conf import settings
    return {'features': getattr(settings, 'FEATURE_FLAGS', {})}

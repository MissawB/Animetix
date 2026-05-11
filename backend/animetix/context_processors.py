from .services import TRANSLATIONS

def translation_processor(request):
    """Injecte les textes traduits dans tous les templates."""
    lang = request.session.get('language', 'Français')
    return {
        'txt': TRANSLATIONS.get(lang, TRANSLATIONS['Français']),
        'current_lang': lang
    }

import numpy as np
import datetime
import logging
from django.shortcuts import redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("animetix.utils")

# Note: Most session-related utilities have been moved to GameSessionManager 
# to comply with the architectural decoupling mandate.

def get_current_mode(request):
    """Fallback for non-GameSessionManager contexts."""
    return request.session.get('media_type', 'Anime')

def switch_mode(request, mode):
    """Switches the media type mode in the session and redirects back."""
    from .session_manager import GameSessionManager
    GameSessionManager(request).switch_mode(mode)
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def switch_language(request, lang):
    """Switches the UI language in the session and redirects back."""
    from .session_manager import GameSessionManager
    GameSessionManager(request).switch_language(lang)
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def switch_difficulty(request, diff):
    """Switches the game difficulty in the session."""
    from .session_manager import GameSessionManager
    GameSessionManager(request).switch_difficulty(diff)
    return JsonResponse({'status': 'ok'})

def handle_win_achievements(request, unlocked_achievements):
    """Wrapper for GameSessionManager.handle_win_achievements."""
    from .session_manager import GameSessionManager
    GameSessionManager(request).handle_win_achievements(unlocked_achievements)


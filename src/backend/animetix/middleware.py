import contextvars
from typing import Optional, Any

user_id_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar("user_id", default=None)
user_tier_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_tier", default="free")

def get_current_user_id():
    return user_id_var.get()

def get_current_user_tier():
    return user_tier_var.get()

class UserTrackingMiddleware:
    """
    Middleware that stores the current user ID in context-local storage 
    for domain-level observability (e.g. token tracking).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        token = user_id_var.set(user_id)
        try:
            return self.get_response(request)
        finally:
            user_id_var.reset(token)

class UserTierMiddleware:
    """
    Middleware that extracts the user's tier from their profile and 
    attaches it to the request object as 'user_tier', and stores it in context locals.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tier = 'free'
        if request.user.is_authenticated:
            # Profile is automatically created on user creation via signals
            profile = getattr(request.user, 'profile', None)
            tier = getattr(profile, 'tier', 'free') if profile else 'free'
            request.user_tier = tier
        else:
            request.user_tier = 'free'
        
        token = user_tier_var.set(tier)
        try:
            return self.get_response(request)
        finally:
            user_tier_var.reset(token)

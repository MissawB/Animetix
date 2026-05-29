import contextvars
import sys
from typing import Optional, Any
from asgiref.sync import iscoroutinefunction

# Synchronize contextvars across double-import namespaces (e.g. animetix.middleware vs backend.api.animetix.middleware)
if "animetix.middleware" in sys.modules and __name__ != "animetix.middleware":
    _other = sys.modules["animetix.middleware"]
    user_id_var = getattr(_other, "user_id_var")
    user_tier_var = getattr(_other, "user_tier_var")
elif "backend.api.animetix.middleware" in sys.modules and __name__ != "backend.api.animetix.middleware":
    _other = sys.modules["backend.api.animetix.middleware"]
    user_id_var = getattr(_other, "user_id_var")
    user_tier_var = getattr(_other, "user_tier_var")
else:
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
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)

        user_id = request.user.id if request.user.is_authenticated else None
        token = user_id_var.set(user_id)
        try:
            return self.get_response(request)
        finally:
            user_id_var.reset(token)

    async def __acall__(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        token = user_id_var.set(user_id)
        try:
            return await self.get_response(request)
        finally:
            user_id_var.reset(token)

class UserTierMiddleware:
    """
    Middleware that extracts the user's tier from their profile and 
    attaches it to the request object as 'user_tier', and stores it in context locals.
    """
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)

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

    async def __acall__(self, request):
        tier = 'free'
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            tier = getattr(profile, 'tier', 'free') if profile else 'free'
            request.user_tier = tier
        else:
            request.user_tier = 'free'

        token = user_tier_var.set(tier)
        try:
            return await self.get_response(request)
        finally:
            user_tier_var.reset(token)

import threading

_thread_locals = threading.local()

def get_current_user_id():
    return getattr(_thread_locals, 'user_id', None)

def get_current_user_tier():
    return getattr(_thread_locals, 'user_tier', 'free')

class UserTrackingMiddleware:
    """
    Middleware that stores the current user ID in thread-local storage 
    for domain-level observability (e.g. token tracking).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            _thread_locals.user_id = request.user.id
        else:
            _thread_locals.user_id = None
            
        response = self.get_response(request)
        
        # Cleanup
        if hasattr(_thread_locals, 'user_id'):
            del _thread_locals.user_id
            
        return response

class UserTierMiddleware:
    """
    Middleware that extracts the user's tier from their profile and 
    attaches it to the request object as 'user_tier', and stores it in thread locals.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tier = 'free'
        if request.user.is_authenticated:
            # Profile is automatically created on user creation via signals
            tier = request.user.profile.tier
            request.user_tier = tier
        else:
            request.user_tier = 'free'
        
        _thread_locals.user_tier = tier
        response = self.get_response(request)

        # Cleanup
        if hasattr(_thread_locals, 'user_tier'):
            del _thread_locals.user_tier

        return response

import threading

_thread_locals = threading.local()

def get_current_user_id():
    return getattr(_thread_locals, 'user_id', None)

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

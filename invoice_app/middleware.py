"""
Middleware to capture current user and request for audit logging
"""
import threading

# Thread-local storage for current request/user
_thread_locals = threading.local()


def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    """Get the current user from thread-local storage"""
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user
    return None


class CurrentRequestMiddleware:
    """Middleware to store current request in thread-local storage"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.request = None
        return response

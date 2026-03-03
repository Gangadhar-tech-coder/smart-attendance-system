from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles=[]):
    """
    Decorator for views that checks whether the user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and (request.user.user_type in allowed_roles or request.user.is_superuser):
                return view_func(request, *args, **kwargs)
            
            # If user has a different role, send them to their specific redirector
            return redirect('dashboard') 
        return _wrapped_view
    return decorator
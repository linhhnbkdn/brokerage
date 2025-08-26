"""
JWT authentication decorators.
"""
from functools import wraps
from django.http import JsonResponse
from .services import JWTTokenService


def jwt_required(view_func):
    """
    Decorator to require JWT authentication for views.
    
    Usage:
        @jwt_required
        def my_view(request):
            user_id = request.user_id
            # ... view logic
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return JsonResponse(
                {'error': 'Authorization header required'},
                status=401
            )
        
        # Check bearer token format
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Invalid authorization header format'},
                status=401
            )
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token
        user_id = JWTTokenService.validate_access_token(token)
        if user_id is None:
            return JsonResponse(
                {'error': 'Invalid or expired token'},
                status=401
            )
        
        # Add user_id to request
        request.user_id = user_id
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
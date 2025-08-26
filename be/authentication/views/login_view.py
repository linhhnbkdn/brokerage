"""
User login view.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse

from .base_view import BaseAuthView
from ..services import JWTTokenService


class LoginView(BaseAuthView):
    """User login API view."""
    
    def post(self, request) -> JsonResponse:
        """
        Authenticate user and return JWT tokens.
        
        Expected JSON payload:
        {
            "email": "user@example.com",
            "password": "secure_password"
        }
        """
        data, error = self.parse_json_body(request)
        if error:
            return error
        
        # Validate required fields
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return JsonResponse(
                {'error': 'Email and password are required'},
                status=400
            )
        
        # Check if user exists first
        try:
            user_obj = User.objects.get(username=email)
            if not user_obj.is_active:
                return JsonResponse(
                    {'error': 'Account is disabled'},
                    status=401
                )
        except User.DoesNotExist:
            pass

        # Authenticate user
        user = authenticate(
            request,
            username=email,
            password=password
        )
        
        if user is None:
            return JsonResponse(
                {'error': 'Invalid credentials'},
                status=401
            )
        
        # Generate JWT tokens
        tokens = JWTTokenService.generate_token_pair(user.id)
        
        return JsonResponse(tokens, status=200)
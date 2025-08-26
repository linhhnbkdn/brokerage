"""
Token refresh view.
"""
from django.contrib.auth.models import User
from django.http import JsonResponse

from .base_view import BaseAuthView
from ..services import JWTTokenService


class RefreshView(BaseAuthView):
    """Token refresh API view."""
    
    def post(self, request) -> JsonResponse:
        """
        Refresh JWT tokens using refresh token.
        
        Expected JSON payload:
        {
            "refresh_token": "jwt_refresh_token"
        }
        """
        data, error = self.parse_json_body(request)
        if error:
            return error
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return JsonResponse(
                {'error': 'Refresh token is required'},
                status=400
            )
        
        # Validate refresh token
        user_id = JWTTokenService.validate_refresh_token(refresh_token)
        if user_id is None:
            return JsonResponse(
                {'error': 'Invalid refresh token'},
                status=401
            )
        
        try:
            # Check if user still exists
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return JsonResponse(
                    {'error': 'Account is disabled'},
                    status=401
                )
        except User.DoesNotExist:
            return JsonResponse(
                {'error': 'User not found'},
                status=401
            )
        
        # Revoke old refresh token
        JWTTokenService.revoke_refresh_token(refresh_token)
        
        # Generate new token pair
        tokens = JWTTokenService.generate_token_pair(user_id)
        
        return JsonResponse(tokens, status=200)
"""
User logout view.
"""
from django.http import JsonResponse

from .base_view import BaseAuthView
from ..services import JWTTokenService


class LogoutView(BaseAuthView):
    """User logout API view."""
    
    def post(self, request) -> JsonResponse:
        """
        Logout user by revoking refresh token.
        
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
        
        # Revoke refresh token
        success = JWTTokenService.revoke_refresh_token(refresh_token)
        
        if success:
            return JsonResponse(
                {'message': 'Logged out successfully'},
                status=200
            )
        else:
            return JsonResponse(
                {'error': 'Invalid refresh token'},
                status=400
            )
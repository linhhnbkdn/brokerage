"""
Base view with common functionality for authentication views.
"""
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View


@method_decorator(csrf_exempt, name='dispatch')
class BaseAuthView(View):
    """Base view for authentication endpoints."""
    
    def parse_json_body(self, request) -> tuple[dict, JsonResponse]:
        """
        Parse JSON body from request.
        
        Returns:
            Tuple of (parsed_data, error_response)
            If successful, error_response is None
        """
        try:
            data = json.loads(request.body)
            return data, None
        except json.JSONDecodeError:
            return None, JsonResponse(
                {'error': 'Invalid JSON payload'},
                status=400
            )
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> str:
        """
        Validate password strength.
        
        Returns:
            Error message if invalid, empty string if valid
        """
        if len(password) < 8:
            return 'Password must be at least 8 characters long'
        
        if not re.search(r'[A-Z]', password):
            return 'Password must contain at least one uppercase letter'
        
        if not re.search(r'[a-z]', password):
            return 'Password must contain at least one lowercase letter'
        
        if not re.search(r'[0-9]', password):
            return 'Password must contain at least one digit'
        
        return ''
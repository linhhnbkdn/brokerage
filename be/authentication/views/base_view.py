"""
Base view with common functionality for authentication views.
"""
import json
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class BaseAuthView(APIView):
    """Base view for authentication endpoints."""
    permission_classes = [AllowAny]
    
    def parse_json_body(self, request) -> tuple[dict, Response]:
        """
        Parse JSON body from request.
        
        Returns:
            Tuple of (parsed_data, error_response)
            If successful, error_response is None
        """
        # DRF automatically parses JSON, so we just return the data
        # Invalid JSON will be caught by DRF's parser and return 400 automatically
        return request.data, None
    
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
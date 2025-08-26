"""
User registration view.
"""
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import IntegrityError

from .base_view import BaseAuthView
from ..services import JWTTokenService


class RegisterView(BaseAuthView):
    """User registration API view."""
    
    def post(self, request) -> JsonResponse:
        """
        Register a new user and return JWT tokens.
        
        Expected JSON payload:
        {
            "email": "user@example.com",
            "password": "secure_password",
            "firstName": "John",
            "lastName": "Doe"
        }
        """
        data, error = self.parse_json_body(request)
        if error:
            return error
        
        # Validate required fields
        required_fields = ['email', 'password', 'firstName', 'lastName']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse(
                    {'error': f'{field} is required'},
                    status=400
                )
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = data['firstName'].strip()
        last_name = data['lastName'].strip()
        
        # Validate email format
        if not self.validate_email(email):
            return JsonResponse(
                {'error': 'Invalid email format'},
                status=400
            )
        
        # Validate password strength
        password_error = self.validate_password(password)
        if password_error:
            return JsonResponse(
                {'error': password_error},
                status=400
            )
        
        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return JsonResponse(
                {'error': 'User already exists'},
                status=409
            )
        
        try:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Generate JWT tokens
            tokens = JWTTokenService.generate_token_pair(user.id)
            
            return JsonResponse(tokens, status=201)
            
        except IntegrityError:
            return JsonResponse(
                {'error': 'User already exists'},
                status=409
            )
        except Exception as e:
            return JsonResponse(
                {'error': 'Internal server error'},
                status=500
            )
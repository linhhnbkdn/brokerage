"""
User registration view.
"""

from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample

from .base_view import BaseAuthView
from ..services import JWTTokenService


class RegisterView(BaseAuthView):
    """User registration API view."""

    @extend_schema(
        summary="Register new user",
        description="Register a new user account and return JWT tokens",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string", "minLength": 8},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                },
                "required": ["email", "password", "firstName", "lastName"],
            }
        },
        responses={
            201: {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                    },
                }
            }
        },
        examples=[
            OpenApiExample(
                "Registration Example",
                request_only=True,
                value={
                    "email": "user@example.com",
                    "password": "SecurePass123",
                    "firstName": "John",
                    "lastName": "Doe",
                },
            )
        ],
    )
    def post(self, request) -> Response:
        """Register a new user and return JWT tokens."""
        data, error = self.parse_json_body(request)
        if error:
            return error

        # Validate required fields
        required_fields = ["email", "password", "firstName", "lastName"]
        for field in required_fields:
            if field not in data or not data[field]:
                return Response(
                    {"error": f"{field} is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        email = data["email"].lower().strip()
        password = data["password"]
        first_name = data["firstName"].strip()
        last_name = data["lastName"].strip()

        # Validate email format
        if not self.validate_email(email):
            return Response(
                {"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password strength
        password_error = self.validate_password(password)
        if password_error:
            return Response(
                {"error": password_error}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return Response(
                {"error": "User already exists"}, status=status.HTTP_409_CONFLICT
            )

        try:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # Generate JWT tokens
            tokens = JWTTokenService.generate_token_pair(user.id)

            return Response(tokens, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"error": "User already exists"}, status=status.HTTP_409_CONFLICT
            )
        except Exception:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

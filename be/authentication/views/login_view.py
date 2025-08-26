"""
User login view.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample

from .base_view import BaseAuthView
from ..services import JWTTokenService


class LoginView(BaseAuthView):
    """User login API view."""

    @extend_schema(
        summary="User login",
        description="Authenticate user and return JWT tokens",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string"},
                },
                "required": ["email", "password"],
            }
        },
        responses={
            200: {
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
                "Login Example",
                request_only=True,
                value={"email": "user@example.com", "password": "SecurePass123"},
            )
        ],
    )
    def post(self, request) -> Response:
        """Authenticate user and return JWT tokens."""
        data, error = self.parse_json_body(request)
        if error:
            return error

        # Validate required fields
        email = data.get("email", "").lower().strip()
        password = data.get("password", "")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user exists first
        try:
            user_obj = User.objects.get(username=email)
            if not user_obj.is_active:
                return Response(
                    {"error": "Account is disabled"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except User.DoesNotExist:
            pass

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT tokens
        tokens = JWTTokenService.generate_token_pair(user.id)

        return Response(tokens, status=status.HTTP_200_OK)

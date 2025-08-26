"""
Token refresh view.
"""

from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .base_view import BaseAuthView
from ..services import JWTTokenService


class RefreshView(BaseAuthView):
    """Token refresh API view."""

    @extend_schema(
        summary="Refresh tokens",
        description="Refresh JWT tokens using refresh token",
        request={
            "application/json": {
                "type": "object",
                "properties": {"refresh_token": {"type": "string"}},
                "required": ["refresh_token"],
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
    )
    def post(self, request) -> Response:
        """Refresh JWT tokens using refresh token."""
        data, error = self.parse_json_body(request)
        if error:
            return error

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate refresh token
        user_id = JWTTokenService.validate_refresh_token(refresh_token)
        if user_id is None:
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Check if user still exists
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return Response(
                    {"error": "Account is disabled"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Revoke old refresh token
        JWTTokenService.revoke_refresh_token(refresh_token)

        # Generate new token pair
        tokens = JWTTokenService.generate_token_pair(user_id)

        return Response(tokens, status=status.HTTP_200_OK)

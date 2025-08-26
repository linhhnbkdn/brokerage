"""
User logout view.
"""

from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .base_view import BaseAuthView
from ..services import JWTTokenService


class LogoutView(BaseAuthView):
    """User logout API view."""

    @extend_schema(
        summary="User logout",
        description="Logout user by revoking refresh token",
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
                    "properties": {"message": {"type": "string"}},
                }
            }
        },
    )
    def post(self, request) -> Response:
        """Logout user by revoking refresh token."""
        data, error = self.parse_json_body(request)
        if error:
            return error

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Revoke refresh token
        success = JWTTokenService.revoke_refresh_token(refresh_token)

        if success:
            return Response(
                {"message": "Logged out successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )

"""
Base views for banking API endpoints
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class BankingBaseView(APIView):
    """
    Base view for all banking endpoints
    Provides authentication and common functionality
    JWT authentication is handled by method decorators
    """

    permission_classes = [AllowAny]  # JWT handled by decorators

    def handle_service_error(self, error):
        """Handle service layer errors consistently"""
        if isinstance(error, ValueError):
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

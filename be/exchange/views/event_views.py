"""
Event API views (placeholder)
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class MarketEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Placeholder ViewSet for market events"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({'message': 'Market events API coming soon'})
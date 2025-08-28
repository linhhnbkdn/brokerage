"""
Order API views (placeholder)
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class OrderViewSet(viewsets.ModelViewSet):
    """Placeholder ViewSet for orders"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({'message': 'Order API coming soon'})
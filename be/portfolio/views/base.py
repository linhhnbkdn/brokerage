"""
Base view classes for portfolio app
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from authentication.decorators import jwt_required
from django.utils.decorators import method_decorator


@method_decorator(jwt_required, name='dispatch')
class BasePortfolioViewSet(viewsets.ViewSet):
    """Base viewset for portfolio-related views with authentication"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_user_queryset(self, model_class):
        """Get queryset filtered by current user"""
        return model_class.objects.filter(user=self.request.user)
    
    def handle_error_response(self, error_message, status_code=status.HTTP_400_BAD_REQUEST):
        """Standard error response format"""
        return Response(
            {
                "error": True,
                "message": error_message,
                "details": None
            },
            status=status_code
        )
    
    def handle_success_response(self, data, message=None, status_code=status.HTTP_200_OK):
        """Standard success response format"""
        response_data = {
            "error": False,
            "data": data
        }
        if message:
            response_data["message"] = message
            
        return Response(response_data, status=status_code)


@method_decorator(jwt_required, name='dispatch')
class BasePortfolioModelViewSet(viewsets.ModelViewSet):
    """Base model viewset for portfolio models with authentication"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset by current user"""
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user on create"""
        serializer.save(user=self.request.user)
    
    def handle_error_response(self, error_message, status_code=status.HTTP_400_BAD_REQUEST):
        """Standard error response format"""
        return Response(
            {
                "error": True,
                "message": error_message,
                "details": None
            },
            status=status_code
        )
    
    def handle_success_response(self, data, message=None, status_code=status.HTTP_200_OK):
        """Standard success response format"""
        response_data = {
            "error": False,
            "data": data
        }
        if message:
            response_data["message"] = message
            
        return Response(response_data, status=status_code)
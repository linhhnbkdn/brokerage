"""
Unit tests for authentication decorators.
"""
import json

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.renderers import JSONRenderer

from ..services import JWTTokenService
from ..decorators import jwt_required


class JWTRequiredDecoratorTest(TestCase):
    """Test JWT required decorator."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123'
        )
        self.access_token = JWTTokenService.create_access_token(self.user.id)
        self.factory = APIRequestFactory()
    
    def test_decorator_with_valid_token(self):
        """Test decorator with valid token."""
        @jwt_required
        def test_view(request):
            from rest_framework.response import Response
            return Response({'user_id': request.user_id})
        
        # Mock request with valid authorization
        request = self.factory.get('/', HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = test_view(request)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        response.render()
        data = json.loads(response.content)
        
        self.assertEqual(data['user_id'], self.user.id)
    
    def test_decorator_without_auth_header(self):
        """Test decorator without authorization header."""
        @jwt_required
        def test_view(request):
            from rest_framework.response import Response
            return Response({'success': True})
        
        request = self.factory.get('/')
        
        response = test_view(request)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        response.render()
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['error'], 'Authorization header required')
    
    def test_decorator_with_invalid_format(self):
        """Test decorator with invalid authorization format."""
        @jwt_required
        def test_view(request):
            from rest_framework.response import Response
            return Response({'success': True})
        
        request = self.factory.get('/', HTTP_AUTHORIZATION='Invalid format')
        
        response = test_view(request)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        response.render()
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['error'], 'Invalid authorization header format')
    
    def test_decorator_with_invalid_token(self):
        """Test decorator with invalid token."""
        @jwt_required
        def test_view(request):
            from rest_framework.response import Response
            return Response({'success': True})
        
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer invalid_token')
        
        response = test_view(request)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        response.render()
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['error'], 'Invalid or expired token')
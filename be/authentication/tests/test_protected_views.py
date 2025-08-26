"""
Unit tests for protected views.
"""
import json

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from ..services import JWTTokenService


class ProtectedEndpointTest(TestCase):
    """Test protected endpoint with JWT authentication."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('authentication:protected')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123'
        )
        self.access_token = JWTTokenService.create_access_token(self.user.id)
    
    def test_protected_endpoint_success(self):
        """Test protected endpoint with valid token."""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Access granted')
        self.assertEqual(data['user_id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
    
    def test_protected_endpoint_no_auth(self):
        """Test protected endpoint without authorization."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Authorization header required')
    
    def test_protected_endpoint_invalid_header(self):
        """Test protected endpoint with invalid authorization header."""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Invalid header'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid authorization header format')
    
    def test_protected_endpoint_invalid_token(self):
        """Test protected endpoint with invalid token."""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Bearer invalid_token'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid or expired token')
    
    def test_protected_endpoint_user_not_found(self):
        """Test protected endpoint when user is deleted."""
        self.user.delete()
        
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'User not found')
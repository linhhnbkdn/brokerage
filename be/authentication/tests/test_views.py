"""
Unit tests for authentication views.
"""
import json
import jwt
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

from ..services import JWTTokenService


class RegisterViewTest(TestCase):
    """Test user registration API view."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('authentication:register')
        self.valid_data = {
            'email': 'test@example.com',
            'password': 'TestPass123',
            'firstName': 'Test',
            'lastName': 'User'
        }
    
    def test_register_success(self):
        """Test successful user registration."""
        response = self.client.post(
            self.url,
            json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        
        # Verify user created
        self.assertTrue(
            User.objects.filter(username='test@example.com').exists()
        )
    
    def test_register_invalid_json(self):
        """Test registration with invalid JSON."""
        response = self.client.post(
            self.url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON payload')
    
    def test_register_missing_fields(self):
        """Test registration with missing required fields."""
        for field in ['email', 'password', 'firstName', 'lastName']:
            invalid_data = self.valid_data.copy()
            del invalid_data[field]
            
            response = self.client.post(
                self.url,
                json.dumps(invalid_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data['error'], f'{field} is required')
    
    def test_register_empty_fields(self):
        """Test registration with empty fields."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = ''
        
        response = self.client.post(
            self.url,
            json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'email is required')
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid_email'
        
        response = self.client.post(
            self.url,
            json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid email format')
    
    def test_register_weak_password(self):
        """Test registration with weak password."""
        test_cases = [
            ('short', 'Password must be at least 8 characters long'),
            ('lowercase', 'Password must contain at least one uppercase letter'),
            ('UPPERCASE', 'Password must contain at least one lowercase letter'),
            ('NoNumber', 'Password must contain at least one digit'),
        ]
        
        for password, expected_error in test_cases:
            invalid_data = self.valid_data.copy()
            invalid_data['password'] = password
            
            response = self.client.post(
                self.url,
                json.dumps(invalid_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data['error'], expected_error)
    
    def test_register_user_exists(self):
        """Test registration when user already exists."""
        # Create user first
        User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='existing'
        )
        
        response = self.client.post(
            self.url,
            json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'User already exists')
    
    @patch('django.contrib.auth.models.User.objects.create_user')
    def test_register_database_error(self, mock_create_user):
        """Test registration with database error."""
        mock_create_user.side_effect = Exception('Database error')
        
        response = self.client.post(
            self.url,
            json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Internal server error')


class LoginViewTest(TestCase):
    """Test user login API view."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('authentication:login')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='User'
        )
        self.valid_data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
    
    def test_login_success(self):
        """Test successful user login."""
        response = self.client.post(
            self.url,
            json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
    
    def test_login_invalid_json(self):
        """Test login with invalid JSON."""
        response = self.client.post(
            self.url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON payload')
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials."""
        response = self.client.post(
            self.url,
            json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Email and password are required')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = 'wrongpassword'
        
        response = self.client.post(
            self.url,
            json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid credentials')
    
    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(
            self.url,
            json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Account is disabled')
    
    def test_login_case_insensitive_email(self):
        """Test login with case insensitive email."""
        data = self.valid_data.copy()
        data['email'] = 'TEST@EXAMPLE.COM'
        
        response = self.client.post(
            self.url,
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)


class RefreshViewTest(TestCase):
    """Test token refresh API view."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('authentication:refresh')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123'
        )
        self.refresh_token = JWTTokenService.create_refresh_token(self.user.id)
        cache.clear()
        # Re-store the token after cache clear
        payload = jwt.decode(
            self.refresh_token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        JWTTokenService.store_refresh_token(payload['jti'], self.user.id)
    
    def tearDown(self):
        cache.clear()
    
    def test_refresh_success(self):
        """Test successful token refresh."""
        response = self.client.post(
            self.url,
            json.dumps({'refresh_token': self.refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
    
    def test_refresh_invalid_json(self):
        """Test refresh with invalid JSON."""
        response = self.client.post(
            self.url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON payload')
    
    def test_refresh_missing_token(self):
        """Test refresh without refresh token."""
        response = self.client.post(
            self.url,
            json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Refresh token is required')
    
    def test_refresh_invalid_token(self):
        """Test refresh with invalid token."""
        response = self.client.post(
            self.url,
            json.dumps({'refresh_token': 'invalid_token'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid refresh token')
    
    def test_refresh_user_not_found(self):
        """Test refresh when user is deleted."""
        self.user.delete()
        
        response = self.client.post(
            self.url,
            json.dumps({'refresh_token': self.refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'User not found')
    
    def test_refresh_inactive_user(self):
        """Test refresh with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(
            self.url,
            json.dumps({'refresh_token': self.refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Account is disabled')


class LogoutViewTest(TestCase):
    """Test user logout API view."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('authentication:logout')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123'
        )
        self.refresh_token = JWTTokenService.create_refresh_token(self.user.id)
        cache.clear()
        # Re-store the token after cache clear
        payload = jwt.decode(
            self.refresh_token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        JWTTokenService.store_refresh_token(payload['jti'], self.user.id)
    
    def tearDown(self):
        cache.clear()
    
    def test_logout_success(self):
        """Test successful logout."""
        response = self.client.post(
            self.url,
            json.dumps({'refresh_token': self.refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Logged out successfully')
    
    def test_logout_invalid_json(self):
        """Test logout with invalid JSON."""
        response = self.client.post(
            self.url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON payload')
    
    def test_logout_missing_token(self):
        """Test logout without refresh token."""
        response = self.client.post(
            self.url,
            json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Refresh token is required')
    
    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        response = self.client.post(
            self.url,
            json.dumps({'refresh_token': 'invalid_token'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid refresh token')
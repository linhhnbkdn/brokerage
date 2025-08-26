"""
Unit tests for JWT Token Service.
"""

import jwt
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from ..services import JWTTokenService


class JWTTokenServiceTest(TestCase):
    """Test JWT Token Service functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="TestPass123",
            first_name="Test",
            last_name="User",
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_generate_token_pair(self):
        """Test token pair generation."""
        tokens = JWTTokenService.generate_token_pair(self.user.id)

        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)
        self.assertIsInstance(tokens["access_token"], str)
        self.assertIsInstance(tokens["refresh_token"], str)

    def test_create_access_token(self):
        """Test access token creation."""
        token = JWTTokenService.create_access_token(self.user.id)

        # Decode token to verify contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        self.assertEqual(payload["user_id"], self.user.id)
        self.assertEqual(payload["type"], "access")
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = JWTTokenService.create_refresh_token(self.user.id)

        # Decode token to verify contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        self.assertEqual(payload["user_id"], self.user.id)
        self.assertEqual(payload["type"], "refresh")
        self.assertIn("jti", payload)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

        # Check token is stored in cache
        jti = payload["jti"]
        cache_key = f"refresh_token:{jti}"
        self.assertEqual(cache.get(cache_key), self.user.id)

    def test_validate_access_token_valid(self):
        """Test access token validation with valid token."""
        token = JWTTokenService.create_access_token(self.user.id)
        user_id = JWTTokenService.validate_access_token(token)

        self.assertEqual(user_id, self.user.id)

    def test_validate_access_token_invalid(self):
        """Test access token validation with invalid token."""
        user_id = JWTTokenService.validate_access_token("invalid_token")
        self.assertIsNone(user_id)

    def test_validate_access_token_wrong_type(self):
        """Test access token validation with refresh token."""
        refresh_token = JWTTokenService.create_refresh_token(self.user.id)
        user_id = JWTTokenService.validate_access_token(refresh_token)

        self.assertIsNone(user_id)

    def test_validate_access_token_expired(self):
        """Test access token validation with expired token."""
        # Create token with short expiry for testing
        import jwt

        past_time = timezone.now() - timedelta(hours=1)
        payload = {
            "user_id": self.user.id,
            "exp": past_time,
            "iat": past_time,
            "type": "access",
        }

        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        user_id = JWTTokenService.validate_access_token(expired_token)
        self.assertIsNone(user_id)

    def test_validate_refresh_token_valid(self):
        """Test refresh token validation with valid token."""
        token = JWTTokenService.create_refresh_token(self.user.id)
        user_id = JWTTokenService.validate_refresh_token(token)

        self.assertEqual(user_id, self.user.id)

    def test_validate_refresh_token_invalid(self):
        """Test refresh token validation with invalid token."""
        user_id = JWTTokenService.validate_refresh_token("invalid_token")
        self.assertIsNone(user_id)

    def test_validate_refresh_token_wrong_type(self):
        """Test refresh token validation with access token."""
        access_token = JWTTokenService.create_access_token(self.user.id)
        user_id = JWTTokenService.validate_refresh_token(access_token)

        self.assertIsNone(user_id)

    def test_validate_refresh_token_not_in_cache(self):
        """Test refresh token validation when token not in cache."""
        token = JWTTokenService.create_refresh_token(self.user.id)

        # Clear cache to simulate revoked token
        cache.clear()

        user_id = JWTTokenService.validate_refresh_token(token)
        self.assertIsNone(user_id)

    def test_store_refresh_token(self):
        """Test refresh token storage in cache."""
        jti = "test_jti"
        JWTTokenService.store_refresh_token(jti, self.user.id)

        cache_key = f"refresh_token:{jti}"
        self.assertEqual(cache.get(cache_key), self.user.id)

    def test_check_refresh_token_exists(self):
        """Test checking if refresh token exists in cache."""
        jti = "test_jti"
        JWTTokenService.store_refresh_token(jti, self.user.id)

        self.assertTrue(JWTTokenService.check_refresh_token(jti))

    def test_check_refresh_token_not_exists(self):
        """Test checking if refresh token exists when it doesn't."""
        self.assertFalse(JWTTokenService.check_refresh_token("nonexistent"))

    def test_revoke_refresh_token_valid(self):
        """Test revoking valid refresh token."""
        token = JWTTokenService.create_refresh_token(self.user.id)

        # Verify token is in cache
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        jti = payload["jti"]
        self.assertTrue(JWTTokenService.check_refresh_token(jti))

        # Revoke token
        success = JWTTokenService.revoke_refresh_token(token)

        self.assertTrue(success)
        self.assertFalse(JWTTokenService.check_refresh_token(jti))

    def test_revoke_refresh_token_invalid(self):
        """Test revoking invalid refresh token."""
        success = JWTTokenService.revoke_refresh_token("invalid_token")
        self.assertFalse(success)

    def test_get_token_payload_valid(self):
        """Test getting token payload from valid token."""
        token = JWTTokenService.create_access_token(self.user.id)
        payload = JWTTokenService.get_token_payload(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], self.user.id)
        self.assertEqual(payload["type"], "access")

    def test_get_token_payload_invalid(self):
        """Test getting token payload from invalid token."""
        payload = JWTTokenService.get_token_payload("invalid_token")
        self.assertIsNone(payload)

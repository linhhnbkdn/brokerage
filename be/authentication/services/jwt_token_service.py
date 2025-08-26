"""
JWT Token Service for authentication operations.
"""

import uuid
from datetime import timedelta
from typing import Dict, Optional

import jwt
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


class JWTTokenService:
    """Service class for JWT token operations."""

    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=7)
    ALGORITHM = "HS256"

    @classmethod
    def generate_token_pair(cls, user_id: int) -> Dict[str, str]:
        """
        Generate access and refresh token pair for a user.

        Args:
            user_id: User ID to generate tokens for

        Returns:
            Dictionary with access_token and refresh_token
        """
        access_token = cls.create_access_token(user_id)
        refresh_token = cls.create_refresh_token(user_id)

        return {"access_token": access_token, "refresh_token": refresh_token}

    @classmethod
    def create_access_token(cls, user_id: int) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID to encode in token

        Returns:
            JWT access token string
        """
        now = timezone.now()
        payload = {
            "user_id": user_id,
            "exp": now + cls.ACCESS_TOKEN_LIFETIME,
            "iat": now,
            "type": "access",
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        """
        Create JWT refresh token and store in cache.

        Args:
            user_id: User ID to encode in token

        Returns:
            JWT refresh token string
        """
        jti = str(uuid.uuid4())
        now = timezone.now()

        payload = {
            "user_id": user_id,
            "jti": jti,
            "exp": now + cls.REFRESH_TOKEN_LIFETIME,
            "iat": now,
            "type": "refresh",
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=cls.ALGORITHM)

        # Store refresh token in cache
        cls.store_refresh_token(jti, user_id)

        return token

    @classmethod
    def validate_access_token(cls, token: str) -> Optional[int]:
        """
        Validate access token and return user ID.

        Args:
            token: JWT access token

        Returns:
            User ID if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[cls.ALGORITHM])

            if payload.get("type") != "access":
                return None

            return payload.get("user_id")

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def validate_refresh_token(cls, token: str) -> Optional[int]:
        """
        Validate refresh token and return user ID.

        Args:
            token: JWT refresh token

        Returns:
            User ID if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[cls.ALGORITHM])

            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            user_id = payload.get("user_id")

            if not jti or not user_id:
                return None

            # Check if token exists in cache
            if not cls.check_refresh_token(jti):
                return None

            return user_id

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def store_refresh_token(cls, jti: str, user_id: int) -> None:
        """
        Store refresh token in cache.

        Args:
            jti: JWT ID
            user_id: User ID
        """
        cache_key = f"refresh_token:{jti}"
        cache.set(
            cache_key, user_id, timeout=int(cls.REFRESH_TOKEN_LIFETIME.total_seconds())
        )

    @classmethod
    def check_refresh_token(cls, jti: str) -> bool:
        """
        Check if refresh token exists in cache.

        Args:
            jti: JWT ID

        Returns:
            True if token exists, False otherwise
        """
        cache_key = f"refresh_token:{jti}"
        return cache.get(cache_key) is not None

    @classmethod
    def revoke_refresh_token(cls, token: str) -> bool:
        """
        Revoke refresh token by removing from cache.

        Args:
            token: JWT refresh token

        Returns:
            True if successfully revoked, False otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[cls.ALGORITHM])

            jti = payload.get("jti")
            if jti:
                cache_key = f"refresh_token:{jti}"
                cache.delete(cache_key)
                return True

        except jwt.InvalidTokenError:
            pass

        return False

    @classmethod
    def get_token_payload(cls, token: str) -> Optional[Dict]:
        """
        Get token payload without validation.

        Args:
            token: JWT token

        Returns:
            Token payload if decodable, None otherwise
        """
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[cls.ALGORITHM])
        except jwt.InvalidTokenError:
            return None

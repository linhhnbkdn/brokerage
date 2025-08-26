"""
Base classes and common functionality for banking models
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


class TimestampedModel(models.Model):
    """
    Abstract base class for models requiring created_at and updated_at fields
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EncryptionMixin:
    """
    Mixin providing encryption functionality for sensitive data
    """

    @abstractmethod
    def get_encryption_key(self):
        """Get encryption key for this model"""
        pass

    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        from cryptography.fernet import Fernet

        fernet = Fernet(self.get_encryption_key())
        return fernet.encrypt(data.encode())

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        from cryptography.fernet import Fernet

        fernet = Fernet(self.get_encryption_key())
        return fernet.decrypt(encrypted_data).decode()


class ValidatorInterface(ABC):
    """
    Interface for validation services
    """

    @abstractmethod
    def validate(self, data) -> bool:
        """Validate data according to business rules"""
        pass

    @abstractmethod
    def get_validation_errors(self) -> list:
        """Get list of validation errors"""
        pass


class FinancialModel(TimestampedModel):
    """
    Abstract base class for financial models with common validations
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="%(class)s_records"
    )

    class Meta:
        abstract = True

    def validate_user_ownership(self, user: User) -> bool:
        """Validate that the user owns this record"""
        return self.user == user

    def get_formatted_amount(self, amount: Decimal) -> str:
        """Format amount for display"""
        return f"${amount:,.2f}"

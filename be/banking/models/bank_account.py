"""
BankAccount model for storing linked bank account information
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.conf import settings
from cryptography.fernet import Fernet

from .base import TimestampedModel, EncryptionMixin


class BankAccount(TimestampedModel, EncryptionMixin):
    """
    Bank account linked to user for ACH transfers
    Stores encrypted sensitive information following security best practices
    """

    ACCOUNT_TYPE_CHOICES = [
        ("checking", "Checking"),
        ("savings", "Savings"),
    ]

    STATUS_CHOICES = [
        ("pending_verification", "Pending Verification"),
        ("verified", "Verified"),
        ("suspended", "Suspended"),
        ("closed", "Closed"),
    ]

    # Primary identification
    account_link_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique identifier for external API calls",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bank_accounts"
    )

    # Bank details
    bank_name = models.CharField(max_length=100)
    bank_routing_number = models.CharField(max_length=9)
    account_number_encrypted = models.BinaryField()  # Encrypted account number
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)
    account_holder_name = models.CharField(max_length=100)

    # Account status and verification
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending_verification"
    )
    verification_attempts = models.IntegerField(default=0)
    max_verification_attempts = models.IntegerField(default=3)

    # Micro-deposit verification
    micro_deposit_amount_1 = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    micro_deposit_amount_2 = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    micro_deposits_sent_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Daily limits
    daily_deposit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("50000.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    daily_withdrawal_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("50000.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "banking_bank_accounts"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["account_link_id"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"

    def __str__(self):
        last_four = self.get_last_four_digits()
        return f"{self.user.email} - {self.bank_name} ****{last_four}"

    def get_encryption_key(self):
        """Get encryption key from settings"""
        key = getattr(settings, "BANKING_ENCRYPTION_KEY", None)
        if not key:
            # Generate key for development - in production, use environment variable
            key = Fernet.generate_key()
        return key

    def set_account_number(self, account_number: str):
        """Encrypt and store account number"""
        self.account_number_encrypted = self.encrypt_data(account_number)

    def get_account_number(self) -> str:
        """Decrypt and return account number"""
        if not self.account_number_encrypted:
            return ""
        return self.decrypt_data(self.account_number_encrypted)

    def get_last_four_digits(self) -> str:
        """Get last 4 digits of account number for display"""
        account_number = self.get_account_number()
        if account_number and len(account_number) >= 4:
            return account_number[-4:]
        return "****"

    def is_verified(self) -> bool:
        """Check if account is verified and ready for transactions"""
        return self.status == "verified"

    def can_attempt_verification(self) -> bool:
        """Check if user can attempt verification"""
        return self.verification_attempts < self.max_verification_attempts

    def is_active(self) -> bool:
        """Check if account is active for transactions"""
        return self.status in ["verified"]

    def generate_micro_deposits(self):
        """Generate random micro-deposit amounts for verification"""
        import random
        from django.utils import timezone

        amount1 = Decimal(f"0.{random.randint(1, 99):02d}")
        amount2 = Decimal(f"0.{random.randint(1, 99):02d}")

        # Ensure amounts are different
        while amount1 == amount2:
            amount2 = Decimal(f"0.{random.randint(1, 99):02d}")

        self.micro_deposit_amount_1 = amount1
        self.micro_deposit_amount_2 = amount2
        self.micro_deposits_sent_at = timezone.now()

    def verify_micro_deposits(self, amount1: Decimal, amount2: Decimal) -> bool:
        """Verify micro-deposit amounts"""
        if not self.micro_deposit_amount_1 or not self.micro_deposit_amount_2:
            return False

        amounts_match = (
            self.micro_deposit_amount_1 == amount1
            and self.micro_deposit_amount_2 == amount2
        ) or (
            self.micro_deposit_amount_1 == amount2
            and self.micro_deposit_amount_2 == amount1
        )

        if amounts_match:
            self.status = "verified"
            return True
        else:
            self.verification_attempts += 1
            return False

    def get_masked_account_info(self) -> dict:
        """Get account info with masked sensitive data for API responses"""
        return {
            "account_link_id": str(self.account_link_id),
            "bank_name": self.bank_name,
            "account_type": self.account_type,
            "last_four_digits": self.get_last_four_digits(),
            "status": self.status,
            "account_holder_name": self.account_holder_name,
        }

    def update_last_used(self):
        """Update last used timestamp"""
        from django.utils import timezone

        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])

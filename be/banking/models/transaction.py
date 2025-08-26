"""
Transaction model for banking operations
"""

import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

from .base import TimestampedModel
from .bank_account import BankAccount


class Transaction(TimestampedModel):
    """
    Banking transactions (deposits, withdrawals, transfers)
    Tracks all financial movements with proper audit trail
    """

    TYPE_CHOICES = [
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("micro_deposit", "Micro Deposit"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    # Primary identification
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique identifier for transaction tracking",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="banking_transactions"
    )
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="transactions"
    )

    # Transaction details
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, default="USD")

    # Status tracking
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")

    # ACH processing details
    ach_transaction_id = models.CharField(max_length=100, null=True, blank=True)
    processor_reference = models.CharField(max_length=100, null=True, blank=True)

    # Timing information
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion_date = models.DateField(null=True, blank=True)

    # Error handling
    failure_reason = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    # Metadata
    description = models.CharField(max_length=255, null=True, blank=True)
    internal_notes = models.TextField(null=True, blank=True)

    # Balance tracking for audit
    balance_before = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    balance_after = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = "banking_transactions"
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["bank_account", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Banking Transaction"
        verbose_name_plural = "Banking Transactions"

    def __str__(self):
        return (
            f"{self.get_type_display()} ${self.amount} - "
            f"{self.get_status_display()} ({self.user.email})"
        )

    def is_processable(self) -> bool:
        """Check if transaction can be processed"""
        return (
            self.status in ["pending", "processing"]
            and self.retry_count < self.max_retries
        )

    def can_retry(self) -> bool:
        """Check if failed transaction can be retried"""
        return self.status == "failed" and self.retry_count < self.max_retries

    def is_completed(self) -> bool:
        """Check if transaction is completed"""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if transaction failed"""
        return self.status == "failed"

    def calculate_estimated_completion(self):
        """Calculate estimated completion date based on transaction type"""
        if self.type == "micro_deposit":
            # Micro deposits take 2-3 business days
            self.estimated_completion_date = date.today() + timedelta(days=3)
        else:
            # Regular deposits/withdrawals take 1-3 business days
            self.estimated_completion_date = date.today() + timedelta(days=2)

    def mark_as_processing(self):
        """Mark transaction as processing"""
        from django.utils import timezone

        self.status = "processing"
        self.processed_at = timezone.now()

    def mark_as_completed(
        self, balance_before: Decimal = None, balance_after: Decimal = None
    ):
        """Mark transaction as completed with optional balance tracking"""
        from django.utils import timezone

        self.status = "completed"
        self.completed_at = timezone.now()
        if balance_before is not None:
            self.balance_before = balance_before
        if balance_after is not None:
            self.balance_after = balance_after

    def mark_as_failed(self, reason: str = None):
        """Mark transaction as failed with optional reason"""
        self.status = "failed"
        if reason:
            self.failure_reason = reason
        self.retry_count += 1

    def get_transaction_summary(self) -> dict:
        """Get transaction summary for API responses"""
        return {
            "transaction_id": str(self.transaction_id),
            "type": self.type,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "estimated_completion": (
                self.estimated_completion_date.isoformat()
                if self.estimated_completion_date
                else None
            ),
            "description": self.description,
        }

    def save(self, *args, **kwargs):
        """Override save to set estimated completion date if needed"""
        if not self.estimated_completion_date and self.status == "pending":
            self.calculate_estimated_completion()
        super().save(*args, **kwargs)

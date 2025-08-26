"""
UserBalance model for tracking user account balances
"""

from decimal import Decimal
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

from .base import TimestampedModel


class UserBalance(TimestampedModel):
    """
    User account balance tracking with daily limits management
    Maintains available, pending, and total balance calculations
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="account_balance"
    )

    # Balance amounts
    available_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Balance available for withdrawals",
    )
    pending_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Balance pending from deposits",
    )
    total_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total balance (available + pending)",
    )

    # Daily usage tracking
    daily_deposit_used = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    daily_withdrawal_used = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    last_daily_reset = models.DateField(auto_now_add=True)

    # Account limits
    max_daily_deposit = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("50000.00")
    )
    max_daily_withdrawal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("50000.00")
    )

    class Meta:
        db_table = "banking_user_balances"
        verbose_name = "User Balance"
        verbose_name_plural = "User Balances"

    def __str__(self):
        return f"{self.user.email} - ${self.available_balance}"

    def update_total_balance(self):
        """Recalculate total balance from available and pending"""
        self.total_balance = self.available_balance + self.pending_balance

    def reset_daily_limits_if_needed(self):
        """Reset daily usage counters if new day"""
        today = date.today()

        if self.last_daily_reset < today:
            self.daily_deposit_used = Decimal("0.00")
            self.daily_withdrawal_used = Decimal("0.00")
            self.last_daily_reset = today
            self.save(
                update_fields=[
                    "daily_deposit_used",
                    "daily_withdrawal_used",
                    "last_daily_reset",
                ]
            )

    def can_withdraw(self, amount: Decimal) -> bool:
        """Check if user can withdraw specified amount"""
        return amount <= self.available_balance

    def can_deposit_today(self, amount: Decimal) -> bool:
        """Check if user can deposit amount within daily limits"""
        self.reset_daily_limits_if_needed()
        remaining_limit = self.max_daily_deposit - self.daily_deposit_used
        return amount <= remaining_limit

    def can_withdraw_today(self, amount: Decimal) -> bool:
        """Check if user can withdraw amount within daily limits"""
        self.reset_daily_limits_if_needed()
        remaining_limit = self.max_daily_withdrawal - self.daily_withdrawal_used
        return amount <= remaining_limit and self.can_withdraw(amount)

    def get_remaining_daily_deposit_limit(self) -> Decimal:
        """Get remaining daily deposit limit"""
        self.reset_daily_limits_if_needed()
        return self.max_daily_deposit - self.daily_deposit_used

    def get_remaining_daily_withdrawal_limit(self) -> Decimal:
        """Get remaining daily withdrawal limit"""
        self.reset_daily_limits_if_needed()
        return min(
            self.max_daily_withdrawal - self.daily_withdrawal_used,
            self.available_balance,
        )

    def add_pending_deposit(self, amount: Decimal):
        """Add amount to pending balance"""
        self.pending_balance += amount
        self.daily_deposit_used += amount
        self.update_total_balance()

    def complete_deposit(self, amount: Decimal):
        """Move amount from pending to available balance"""
        if self.pending_balance >= amount:
            self.pending_balance -= amount
            self.available_balance += amount
            self.update_total_balance()

    def process_withdrawal(self, amount: Decimal) -> bool:
        """Process withdrawal from available balance"""
        if self.can_withdraw_today(amount):
            self.available_balance -= amount
            self.daily_withdrawal_used += amount
            self.update_total_balance()
            return True
        return False

    def get_balance_summary(self) -> dict:
        """Get balance summary for API responses"""
        self.reset_daily_limits_if_needed()
        return {
            "available_balance": str(self.available_balance),
            "pending_balance": str(self.pending_balance),
            "total_balance": str(self.total_balance),
            "daily_deposit_used": str(self.daily_deposit_used),
            "daily_withdrawal_used": str(self.daily_withdrawal_used),
            "remaining_daily_deposit_limit": str(
                self.get_remaining_daily_deposit_limit()
            ),
            "remaining_daily_withdrawal_limit": str(
                self.get_remaining_daily_withdrawal_limit()
            ),
        }

    def save(self, *args, **kwargs):
        """Override save to ensure total balance is updated"""
        self.update_total_balance()
        super().save(*args, **kwargs)


# Signal to create UserBalance when User is created


@receiver(post_save, sender=User)
def create_user_balance(sender, instance, created, **kwargs):
    """Create UserBalance when User is created"""
    if created:
        UserBalance.objects.create(user=instance)

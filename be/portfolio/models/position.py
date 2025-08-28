"""
Position model for portfolio holdings
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from banking.models.base import TimestampedModel


class Position(TimestampedModel):
    """
    User portfolio positions (stocks, bonds, crypto, etc.)
    Tracks current holdings and calculates performance
    """

    INSTRUMENT_TYPES = [
        ("stock", "Stock"),
        ("bond", "Bond"),
        ("crypto", "Cryptocurrency"),
        ("etf", "Exchange Traded Fund"),
        ("mutual_fund", "Mutual Fund"),
        ("option", "Option"),
        ("future", "Future"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("closed", "Closed"),
        ("suspended", "Suspended"),
    ]

    # Primary identification
    position_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique identifier for position tracking",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="portfolio_positions"
    )

    # Instrument details
    symbol = models.CharField(max_length=20, db_index=True)
    instrument_type = models.CharField(max_length=20, choices=INSTRUMENT_TYPES)
    name = models.CharField(max_length=255, help_text="Full name of the instrument")

    # Position details
    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        validators=[MinValueValidator(Decimal("0.00000001"))],
        help_text="Current quantity held",
    )
    average_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Average cost basis per share/unit",
    )
    current_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal("0.0000"),
        help_text="Latest market price",
    )

    # Status and metadata
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Performance tracking
    last_price_update = models.DateTimeField(null=True, blank=True)
    total_dividends = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        db_table = "portfolio_positions"
        unique_together = ["user", "symbol", "status"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["symbol", "instrument_type"]),
            models.Index(fields=["position_id"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Portfolio Position"
        verbose_name_plural = "Portfolio Positions"

    def __str__(self):
        return f"{self.user.email} - {self.symbol} ({self.quantity})"

    def get_cost_basis(self) -> Decimal:
        """Calculate total cost basis"""
        return self.quantity * self.average_cost

    def get_current_value(self) -> Decimal:
        """Calculate current market value"""
        return self.quantity * self.current_price

    def get_unrealized_gain_loss(self) -> Decimal:
        """Calculate unrealized gain/loss"""
        return self.get_current_value() - self.get_cost_basis()

    def get_unrealized_gain_loss_percent(self) -> Decimal:
        """Calculate unrealized gain/loss percentage"""
        cost_basis = self.get_cost_basis()
        if cost_basis == 0:
            return Decimal("0.00")
        return (self.get_unrealized_gain_loss() / cost_basis) * 100

    def update_current_price(self, price: Decimal):
        """Update current price and timestamp"""
        from django.utils import timezone
        
        self.current_price = price
        self.last_price_update = timezone.now()

    def is_profitable(self) -> bool:
        """Check if position is currently profitable"""
        return self.get_unrealized_gain_loss() > 0

    def get_position_summary(self) -> dict:
        """Get position summary for API responses"""
        return {
            "position_id": str(self.position_id),
            "symbol": self.symbol,
            "instrument_type": self.instrument_type,
            "name": self.name,
            "quantity": str(self.quantity),
            "average_cost": str(self.average_cost),
            "current_price": str(self.current_price),
            "cost_basis": str(self.get_cost_basis()),
            "current_value": str(self.get_current_value()),
            "unrealized_gain_loss": str(self.get_unrealized_gain_loss()),
            "unrealized_gain_loss_percent": str(self.get_unrealized_gain_loss_percent()),
            "status": self.status,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_price_update": (
                self.last_price_update.isoformat() 
                if self.last_price_update else None
            ),
        }
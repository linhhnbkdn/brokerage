"""
PortfolioSnapshot model for daily portfolio value tracking
"""

import uuid
from decimal import Decimal
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from banking.models.base import TimestampedModel


class PortfolioSnapshot(TimestampedModel):
    """
    Daily portfolio value snapshots for performance tracking
    Captures portfolio state at specific points in time
    """

    # Primary identification
    snapshot_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique identifier for snapshot",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="portfolio_snapshots"
    )

    # Snapshot metadata
    snapshot_date = models.DateField(db_index=True)
    snapshot_time = models.DateTimeField(auto_now_add=True)

    # Portfolio values
    total_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        help_text="Total portfolio market value",
    )
    cash_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Cash available in account",
    )
    total_cost_basis = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        help_text="Total cost basis of all positions",
    )

    # Daily performance
    day_gain_loss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Gain/loss for the day",
    )
    day_gain_loss_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.0000"),
        help_text="Daily gain/loss percentage",
    )

    # Total performance
    total_gain_loss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total unrealized gain/loss",
    )
    total_gain_loss_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.0000"),
        help_text="Total gain/loss percentage",
    )

    # Holdings data (JSON field for detailed position data)
    holdings_data = models.JSONField(
        default=dict,
        help_text="Detailed holdings data for this snapshot",
    )

    # Market context
    market_indexes = models.JSONField(
        default=dict,
        help_text="Market index values for comparison",
    )

    class Meta:
        db_table = "portfolio_snapshots"
        unique_together = ["user", "snapshot_date"]
        indexes = [
            models.Index(fields=["user", "snapshot_date"]),
            models.Index(fields=["snapshot_date"]),
            models.Index(fields=["user", "-snapshot_date"]),
        ]
        ordering = ["-snapshot_date", "-snapshot_time"]
        verbose_name = "Portfolio Snapshot"
        verbose_name_plural = "Portfolio Snapshots"

    def __str__(self):
        return f"{self.user.email} - {self.snapshot_date} (${self.total_value})"

    def calculate_total_value_with_cash(self) -> Decimal:
        """Calculate total portfolio value including cash"""
        return self.total_value + self.cash_balance

    def calculate_allocation_percent(self, position_value: Decimal) -> Decimal:
        """Calculate position allocation as percentage of total portfolio"""
        total_portfolio = self.calculate_total_value_with_cash()
        if total_portfolio == 0:
            return Decimal("0.00")
        return (position_value / total_portfolio) * 100

    def get_cash_allocation_percent(self) -> Decimal:
        """Get cash allocation percentage"""
        return self.calculate_allocation_percent(self.cash_balance)

    def is_profitable(self) -> bool:
        """Check if portfolio is currently profitable"""
        return self.total_gain_loss > 0

    @classmethod
    def create_daily_snapshot(cls, user: User, positions_data: list, cash_balance: Decimal):
        """
        Create a daily snapshot from current portfolio positions
        
        Args:
            user: User instance
            positions_data: List of position dictionaries
            cash_balance: Current cash balance
        """
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # Calculate totals
        total_value = sum(Decimal(pos['current_value']) for pos in positions_data)
        total_cost_basis = sum(Decimal(pos['cost_basis']) for pos in positions_data)
        total_gain_loss = total_value - total_cost_basis
        
        # Calculate percentages
        total_gain_loss_percent = Decimal("0.0000")
        if total_cost_basis > 0:
            total_gain_loss_percent = (total_gain_loss / total_cost_basis) * 100

        # Get previous snapshot for daily comparison
        previous_snapshot = cls.objects.filter(
            user=user,
            snapshot_date__lt=today
        ).order_by('-snapshot_date').first()

        day_gain_loss = Decimal("0.00")
        day_gain_loss_percent = Decimal("0.0000")
        
        if previous_snapshot:
            day_gain_loss = total_value - previous_snapshot.total_value
            if previous_snapshot.total_value > 0:
                day_gain_loss_percent = (day_gain_loss / previous_snapshot.total_value) * 100

        # Prepare holdings data
        holdings_data = {
            "positions": positions_data,
            "position_count": len(positions_data),
            "asset_allocation": cls._calculate_asset_allocation(positions_data, total_value),
        }

        # Create or update snapshot
        snapshot, created = cls.objects.update_or_create(
            user=user,
            snapshot_date=today,
            defaults={
                "total_value": total_value,
                "cash_balance": cash_balance,
                "total_cost_basis": total_cost_basis,
                "day_gain_loss": day_gain_loss,
                "day_gain_loss_percent": day_gain_loss_percent,
                "total_gain_loss": total_gain_loss,
                "total_gain_loss_percent": total_gain_loss_percent,
                "holdings_data": holdings_data,
            }
        )

        return snapshot

    @staticmethod
    def _calculate_asset_allocation(positions_data: list, total_value: Decimal) -> dict:
        """Calculate asset allocation by instrument type"""
        allocation = {}
        
        for position in positions_data:
            instrument_type = position.get('instrument_type', 'unknown')
            current_value = Decimal(position.get('current_value', '0'))
            
            if instrument_type not in allocation:
                allocation[instrument_type] = {
                    'value': Decimal('0'),
                    'count': 0,
                    'percentage': Decimal('0.00')
                }
            
            allocation[instrument_type]['value'] += current_value
            allocation[instrument_type]['count'] += 1
        
        # Calculate percentages
        for instrument_type in allocation:
            if total_value > 0:
                allocation[instrument_type]['percentage'] = (
                    allocation[instrument_type]['value'] / total_value
                ) * 100
            allocation[instrument_type]['value'] = str(allocation[instrument_type]['value'])
            allocation[instrument_type]['percentage'] = str(allocation[instrument_type]['percentage'])
        
        return allocation

    def get_snapshot_summary(self) -> dict:
        """Get snapshot summary for API responses"""
        return {
            "snapshot_id": str(self.snapshot_id),
            "snapshot_date": self.snapshot_date.isoformat(),
            "total_value": str(self.total_value),
            "cash_balance": str(self.cash_balance),
            "total_portfolio_value": str(self.calculate_total_value_with_cash()),
            "total_cost_basis": str(self.total_cost_basis),
            "day_gain_loss": str(self.day_gain_loss),
            "day_gain_loss_percent": str(self.day_gain_loss_percent),
            "total_gain_loss": str(self.total_gain_loss),
            "total_gain_loss_percent": str(self.total_gain_loss_percent),
            "cash_allocation_percent": str(self.get_cash_allocation_percent()),
            "holdings_count": len(self.holdings_data.get('positions', [])),
            "asset_allocation": self.holdings_data.get('asset_allocation', {}),
        }
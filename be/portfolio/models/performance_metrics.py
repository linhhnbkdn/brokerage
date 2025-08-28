"""
PerformanceMetrics model for portfolio performance calculations
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from banking.models.base import TimestampedModel


class PerformanceMetrics(TimestampedModel):
    """
    Portfolio performance metrics and calculations
    Stores calculated performance indicators for different time periods
    """

    PERIOD_CHOICES = [
        ("1D", "1 Day"),
        ("1W", "1 Week"),
        ("1M", "1 Month"),
        ("3M", "3 Months"),
        ("6M", "6 Months"),
        ("1Y", "1 Year"),
        ("3Y", "3 Years"),
        ("5Y", "5 Years"),
        ("ALL", "All Time"),
    ]

    # Primary identification
    metrics_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique identifier for metrics record",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="portfolio_metrics"
    )

    # Time period and calculation details
    period = models.CharField(max_length=5, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    calculated_at = models.DateTimeField(auto_now=True)

    # Return metrics
    total_return = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        help_text="Total return percentage for period",
    )
    annualized_return = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Annualized return percentage",
    )
    time_weighted_return = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Time-weighted return percentage",
    )

    # Risk metrics
    volatility = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Portfolio volatility (standard deviation)",
    )
    sharpe_ratio = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Risk-adjusted return ratio",
    )
    max_drawdown = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Maximum drawdown percentage",
    )

    # Benchmark comparison
    benchmark_return = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Benchmark return for same period",
    )
    alpha = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Alpha vs benchmark",
    )
    beta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Beta vs benchmark",
    )

    # Portfolio value data
    starting_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        help_text="Portfolio value at start of period",
    )
    ending_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        help_text="Portfolio value at end of period",
    )
    peak_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Peak portfolio value during period",
    )

    # Additional metrics
    trading_days = models.IntegerField(
        default=0,
        help_text="Number of trading days in period",
    )
    number_of_trades = models.IntegerField(
        default=0,
        help_text="Number of trades executed in period",
    )

    # Metadata
    calculation_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notes about calculation methodology",
    )

    class Meta:
        db_table = "portfolio_performance_metrics"
        unique_together = ["user", "period", "start_date", "end_date"]
        indexes = [
            models.Index(fields=["user", "period"]),
            models.Index(fields=["period", "calculated_at"]),
            models.Index(fields=["user", "-calculated_at"]),
        ]
        ordering = ["-calculated_at", "period"]
        verbose_name = "Performance Metrics"
        verbose_name_plural = "Performance Metrics"

    def __str__(self):
        return f"{self.user.email} - {self.period} ({self.total_return}%)"

    def outperformed_benchmark(self) -> bool:
        """Check if portfolio outperformed benchmark"""
        if self.benchmark_return is None:
            return False
        return self.total_return > self.benchmark_return

    def is_profitable(self) -> bool:
        """Check if portfolio was profitable for this period"""
        return self.total_return > 0

    def get_risk_adjusted_return(self) -> Decimal:
        """Get risk-adjusted return (Sharpe ratio)"""
        return self.sharpe_ratio or Decimal("0.0000")

    @classmethod
    def calculate_metrics(cls, user: User, period: str, snapshots: list, benchmark_data: dict = None):
        """
        Calculate performance metrics from portfolio snapshots
        
        Args:
            user: User instance
            period: Period string (e.g., '1M', '3M', '1Y')
            snapshots: List of PortfolioSnapshot objects
            benchmark_data: Optional benchmark performance data
        """
        if not snapshots or len(snapshots) < 2:
            return None

        # Sort snapshots by date
        snapshots = sorted(snapshots, key=lambda x: x.snapshot_date)
        
        start_snapshot = snapshots[0]
        end_snapshot = snapshots[-1]
        
        # Calculate basic returns
        starting_value = start_snapshot.total_value + start_snapshot.cash_balance
        ending_value = end_snapshot.total_value + end_snapshot.cash_balance
        
        total_return = Decimal("0.0000")
        if starting_value > 0:
            total_return = ((ending_value - starting_value) / starting_value) * 100

        # Calculate additional metrics
        values = [s.total_value + s.cash_balance for s in snapshots]
        peak_value = max(values) if values else ending_value
        
        # Calculate volatility (simplified)
        volatility = cls._calculate_volatility(values) if len(values) > 1 else None
        
        # Calculate max drawdown
        max_drawdown = cls._calculate_max_drawdown(values) if len(values) > 1 else None
        
        # Calculate annualized return
        days_diff = (end_snapshot.snapshot_date - start_snapshot.snapshot_date).days
        annualized_return = None
        if days_diff > 0 and starting_value > 0:
            years = Decimal(days_diff) / Decimal("365.25")
            if years > 0:
                growth_factor = ending_value / starting_value
                annualized_return = ((growth_factor ** (1 / float(years))) - 1) * 100

        # Calculate Sharpe ratio (simplified - assuming 2% risk-free rate)
        sharpe_ratio = None
        if volatility and volatility > 0 and annualized_return:
            risk_free_rate = Decimal("2.0")  # 2% risk-free rate
            excess_return = annualized_return - risk_free_rate
            sharpe_ratio = excess_return / volatility

        # Benchmark comparison
        benchmark_return = None
        alpha = None
        beta = None
        
        if benchmark_data:
            benchmark_return = benchmark_data.get('return')
            if benchmark_return and total_return:
                alpha = total_return - benchmark_return

        # Create or update metrics
        metrics, created = cls.objects.update_or_create(
            user=user,
            period=period,
            start_date=start_snapshot.snapshot_date,
            end_date=end_snapshot.snapshot_date,
            defaults={
                "total_return": total_return,
                "annualized_return": annualized_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "benchmark_return": benchmark_return,
                "alpha": alpha,
                "beta": beta,
                "starting_value": starting_value,
                "ending_value": ending_value,
                "peak_value": peak_value,
                "trading_days": len(snapshots),
            }
        )

        return metrics

    @staticmethod
    def _calculate_volatility(values: list) -> Decimal:
        """Calculate portfolio volatility (standard deviation of returns)"""
        if len(values) < 2:
            return Decimal("0.0000")
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                daily_return = (values[i] - values[i-1]) / values[i-1]
                returns.append(daily_return)
        
        if not returns:
            return Decimal("0.0000")
        
        # Calculate mean and standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        # Annualize volatility (multiply by sqrt(252) for daily data)
        annualized_volatility = std_dev * (252 ** 0.5) * 100
        
        return Decimal(str(round(annualized_volatility, 4)))

    @staticmethod
    def _calculate_max_drawdown(values: list) -> Decimal:
        """Calculate maximum drawdown percentage"""
        if len(values) < 2:
            return Decimal("0.0000")
        
        peak = values[0]
        max_drawdown = Decimal("0.0000")
        
        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = ((peak - value) / peak) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown

    def get_metrics_summary(self) -> dict:
        """Get metrics summary for API responses"""
        return {
            "metrics_id": str(self.metrics_id),
            "period": self.period,
            "period_display": self.get_period_display(),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_return": str(self.total_return),
            "annualized_return": str(self.annualized_return) if self.annualized_return else None,
            "volatility": str(self.volatility) if self.volatility else None,
            "sharpe_ratio": str(self.sharpe_ratio) if self.sharpe_ratio else None,
            "max_drawdown": str(self.max_drawdown) if self.max_drawdown else None,
            "benchmark_return": str(self.benchmark_return) if self.benchmark_return else None,
            "alpha": str(self.alpha) if self.alpha else None,
            "beta": str(self.beta) if self.beta else None,
            "starting_value": str(self.starting_value),
            "ending_value": str(self.ending_value),
            "peak_value": str(self.peak_value) if self.peak_value else None,
            "outperformed_benchmark": self.outperformed_benchmark(),
            "is_profitable": self.is_profitable(),
            "calculated_at": self.calculated_at.isoformat(),
        }
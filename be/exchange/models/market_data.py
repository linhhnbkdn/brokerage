"""
Market data models for exchange integration
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .base import ExchangeBaseModel


class MarketDataSnapshot(ExchangeBaseModel):
    """Stores real-time market data snapshots"""
    
    symbol = models.CharField(
        max_length=10,
        help_text="Trading symbol (e.g., AAPL, BTC-USD)"
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Current price"
    )
    change = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Price change from previous close"
    )
    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        help_text="Percentage change from previous close"
    )
    volume = models.BigIntegerField(
        help_text="Trading volume"
    )
    bid = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Best bid price"
    )
    ask = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Best ask price"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Market data timestamp"
    )
    exchange = models.CharField(
        max_length=20,
        default="SIMULATOR",
        help_text="Exchange name"
    )
    
    class Meta:
        db_table = "exchange_market_data"
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self) -> str:
        return f"{self.symbol}: ${self.price} ({self.change_percent:+.2f}%)"
    
    def get_spread(self) -> Decimal:
        """Calculate bid-ask spread"""
        return self.ask - self.bid
    
    def get_spread_percent(self) -> Decimal:
        """Calculate bid-ask spread percentage"""
        if self.ask == 0:
            return Decimal('0.00')
        return (self.get_spread() / self.ask) * 100
    
    def to_websocket_message(self) -> dict:
        """Convert to WebSocket message format"""
        return {
            "type": "price_update",
            "symbol": self.symbol,
            "price": float(self.price),
            "change": float(self.change),
            "change_percent": float(self.change_percent),
            "volume": self.volume,
            "bid": float(self.bid),
            "ask": float(self.ask),
            "timestamp": self.timestamp.isoformat(),
        }


class SymbolSubscription(ExchangeBaseModel):
    """Tracks user subscriptions to market data symbols"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='symbol_subscriptions'
    )
    symbol = models.CharField(
        max_length=10,
        help_text="Trading symbol"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether subscription is active"
    )
    subscribed_at = models.DateTimeField(
        default=timezone.now,
        help_text="When user subscribed"
    )
    last_price_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time price update was sent to user"
    )
    
    class Meta:
        db_table = "exchange_symbol_subscriptions"
        unique_together = ['user', 'symbol']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['symbol', 'is_active']),
        ]
    
    def __str__(self) -> str:
        status = "Active" if self.is_active else "Inactive"
        return f"{self.user.username} -> {self.symbol} ({status})"
    
    def activate(self) -> None:
        """Activate subscription"""
        self.is_active = True
        self.subscribed_at = timezone.now()
        self.save()
    
    def deactivate(self) -> None:
        """Deactivate subscription"""
        self.is_active = False
        self.save()
    
    def update_last_price_update(self) -> None:
        """Update last price update timestamp"""
        self.last_price_update = timezone.now()
        self.save(update_fields=['last_price_update'])


class MarketEvent(ExchangeBaseModel):
    """Market events and news that can affect trading"""
    
    EVENT_TYPES = [
        ('earnings_beat', 'Earnings Beat'),
        ('earnings_miss', 'Earnings Miss'),
        ('dividend_announcement', 'Dividend Announcement'),
        ('stock_split', 'Stock Split'),
        ('merger_acquisition', 'Merger/Acquisition'),
        ('regulatory_news', 'Regulatory News'),
        ('market_news', 'Market News'),
        ('technical_alert', 'Technical Alert'),
    ]
    
    IMPACT_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    symbol = models.CharField(
        max_length=10,
        help_text="Affected symbol"
    )
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
        help_text="Type of market event"
    )
    impact = models.CharField(
        max_length=10,
        choices=IMPACT_LEVELS,
        default='medium',
        help_text="Expected market impact"
    )
    title = models.CharField(
        max_length=200,
        help_text="Event title"
    )
    description = models.TextField(
        help_text="Event description"
    )
    event_timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the event occurred"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether event is still relevant"
    )
    
    class Meta:
        db_table = "exchange_market_events"
        indexes = [
            models.Index(fields=['symbol', '-event_timestamp']),
            models.Index(fields=['event_type', '-event_timestamp']),
            models.Index(fields=['impact', '-event_timestamp']),
        ]
        ordering = ['-event_timestamp']
    
    def __str__(self) -> str:
        return f"{self.symbol}: {self.title} ({self.impact})"
    
    def to_websocket_message(self) -> dict:
        """Convert to WebSocket message format"""
        return {
            "type": "market_alert",
            "symbol": self.symbol,
            "severity": self.impact,
            "title": self.title,
            "message": self.description,
            "timestamp": self.event_timestamp.isoformat(),
        }
    
    def deactivate(self) -> None:
        """Mark event as no longer active"""
        self.is_active = False
        self.save()
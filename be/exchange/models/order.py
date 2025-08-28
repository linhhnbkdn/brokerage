"""
Order models for exchange integration
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .base import ExchangeBaseModel


class Order(ExchangeBaseModel):
    """Order placement and execution tracking"""
    
    ORDER_SIDES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    ORDER_TYPES = [
        ('market', 'Market Order'),
        ('limit', 'Limit Order'),
        ('stop', 'Stop Order'),
        ('stop_limit', 'Stop Limit Order'),
    ]
    
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('partial', 'Partially Filled'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    TIME_IN_FORCE = [
        ('day', 'Day Order'),
        ('gtc', 'Good Till Cancelled'),
        ('ioc', 'Immediate or Cancel'),
        ('fok', 'Fill or Kill'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='exchange_orders'
    )
    order_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="External order ID"
    )
    symbol = models.CharField(
        max_length=10,
        help_text="Trading symbol"
    )
    side = models.CharField(
        max_length=4,
        choices=ORDER_SIDES,
        help_text="Buy or sell"
    )
    order_type = models.CharField(
        max_length=10,
        choices=ORDER_TYPES,
        help_text="Order type"
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Order quantity"
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Order price (for limit/stop orders)"
    )
    stop_price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Stop price (for stop orders)"
    )
    filled_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal('0.00'),
        help_text="Quantity filled"
    )
    average_fill_price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Average price of fills"
    )
    status = models.CharField(
        max_length=10,
        choices=ORDER_STATUS,
        default='pending',
        help_text="Order status"
    )
    time_in_force = models.CharField(
        max_length=3,
        choices=TIME_IN_FORCE,
        default='day',
        help_text="Time in force"
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was submitted to exchange"
    )
    filled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was fully filled"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was cancelled"
    )
    exchange = models.CharField(
        max_length=20,
        default="SIMULATOR",
        help_text="Exchange name"
    )
    
    class Meta:
        db_table = "exchange_orders"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['symbol', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['order_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.order_id}: {self.side.upper()} {self.quantity} {self.symbol} @ {self.price or 'MARKET'}"
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to fill"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_fully_filled(self) -> bool:
        """Check if order is fully filled"""
        return self.filled_quantity >= self.quantity
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active (can be filled)"""
        return self.status in ['pending', 'submitted', 'partial']
    
    def submit(self) -> None:
        """Mark order as submitted"""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
    
    def fill(self, fill_quantity: Decimal, fill_price: Decimal) -> None:
        """Process a fill for this order"""
        if not self.is_active:
            raise ValueError("Cannot fill inactive order")
        
        if fill_quantity > self.remaining_quantity:
            raise ValueError("Fill quantity exceeds remaining quantity")
        
        # Update filled quantity and average price
        total_filled_value = (self.filled_quantity * (self.average_fill_price or Decimal('0.00'))) + (fill_quantity * fill_price)
        self.filled_quantity += fill_quantity
        self.average_fill_price = total_filled_value / self.filled_quantity
        
        # Update status
        if self.is_fully_filled:
            self.status = 'filled'
            self.filled_at = timezone.now()
        else:
            self.status = 'partial'
        
        self.save()
    
    def cancel(self) -> None:
        """Cancel the order"""
        if not self.is_active:
            raise ValueError("Cannot cancel inactive order")
        
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
    
    def reject(self, reason: str = None) -> None:
        """Reject the order"""
        self.status = 'rejected'
        self.save()
    
    def to_websocket_message(self) -> dict:
        """Convert to WebSocket message format"""
        return {
            "type": "order_executed",
            "order_id": self.order_id,
            "symbol": self.symbol,
            "status": self.status,
            "quantity": float(self.quantity),
            "filled_quantity": float(self.filled_quantity),
            "price": float(self.average_fill_price) if self.average_fill_price else None,
            "timestamp": (self.filled_at or self.updated_at).isoformat(),
        }


class OrderExecution(ExchangeBaseModel):
    """Individual order executions/fills"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    execution_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Execution ID from exchange"
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Executed quantity"
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Execution price"
    )
    executed_at = models.DateTimeField(
        default=timezone.now,
        help_text="Execution timestamp"
    )
    commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Commission charged"
    )
    
    class Meta:
        db_table = "exchange_order_executions"
        indexes = [
            models.Index(fields=['order', '-executed_at']),
            models.Index(fields=['execution_id']),
        ]
        ordering = ['-executed_at']
    
    def __str__(self) -> str:
        return f"{self.execution_id}: {self.quantity} @ {self.price}"
    
    @property
    def total_value(self) -> Decimal:
        """Calculate total execution value"""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> Decimal:
        """Calculate net execution value after commission"""
        return self.total_value - self.commission
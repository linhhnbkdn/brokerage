"""
WebSocket connection tracking models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .base import ExchangeBaseModel


class WebSocketConnection(ExchangeBaseModel):
    """Track active WebSocket connections"""
    
    CONNECTION_STATUS = [
        ('connecting', 'Connecting'),
        ('connected', 'Connected'),
        ('authenticated', 'Authenticated'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='websocket_connections',
        help_text="Associated user (after authentication)"
    )
    channel_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Channels channel name"
    )
    status = models.CharField(
        max_length=15,
        choices=CONNECTION_STATUS,
        default='connecting',
        help_text="Connection status"
    )
    connected_at = models.DateTimeField(
        default=timezone.now,
        help_text="When connection was established"
    )
    authenticated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user was authenticated"
    )
    last_activity = models.DateTimeField(
        default=timezone.now,
        help_text="Last activity timestamp"
    )
    disconnected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When connection was closed"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="Client user agent"
    )
    subscription_count = models.IntegerField(
        default=0,
        help_text="Number of active subscriptions"
    )
    
    class Meta:
        db_table = "exchange_websocket_connections"
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-last_activity']),
            models.Index(fields=['channel_name']),
        ]
        ordering = ['-last_activity']
    
    def __str__(self) -> str:
        user_info = f"{self.user.username}" if self.user else "Anonymous"
        return f"{user_info} ({self.channel_name}) - {self.status}"
    
    def authenticate(self, user: User) -> None:
        """Mark connection as authenticated"""
        self.user = user
        self.status = 'authenticated'
        self.authenticated_at = timezone.now()
        self.update_activity()
    
    def disconnect(self) -> None:
        """Mark connection as disconnected"""
        self.status = 'disconnected'
        self.disconnected_at = timezone.now()
        self.save()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def increment_subscriptions(self) -> None:
        """Increment subscription count"""
        self.subscription_count += 1
        self.save(update_fields=['subscription_count'])
    
    def decrement_subscriptions(self) -> None:
        """Decrement subscription count"""
        self.subscription_count = max(0, self.subscription_count - 1)
        self.save(update_fields=['subscription_count'])
    
    @property
    def is_active(self) -> bool:
        """Check if connection is active"""
        return self.status in ['connected', 'authenticated']
    
    @property
    def session_duration(self) -> timezone.timedelta:
        """Calculate session duration"""
        end_time = self.disconnected_at or timezone.now()
        return end_time - self.connected_at


class ConnectionEvent(ExchangeBaseModel):
    """Log connection events for monitoring"""
    
    EVENT_TYPES = [
        ('connect', 'Connection Established'),
        ('authenticate', 'User Authenticated'),
        ('subscribe', 'Symbol Subscription'),
        ('unsubscribe', 'Symbol Unsubscription'),
        ('message_sent', 'Message Sent'),
        ('message_received', 'Message Received'),
        ('error', 'Error Occurred'),
        ('disconnect', 'Connection Closed'),
    ]
    
    connection = models.ForeignKey(
        WebSocketConnection,
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        help_text="Type of event"
    )
    event_data = models.JSONField(
        default=dict,
        help_text="Additional event data"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When event occurred"
    )
    
    class Meta:
        db_table = "exchange_connection_events"
        indexes = [
            models.Index(fields=['connection', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self) -> str:
        return f"{self.connection.channel_name}: {self.event_type}"
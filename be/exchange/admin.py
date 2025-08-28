"""
Django admin configuration for exchange models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from exchange.models import (
    MarketDataSnapshot, SymbolSubscription, MarketEvent,
    Order, OrderExecution, WebSocketConnection, ConnectionEvent
)


@admin.register(MarketDataSnapshot)
class MarketDataSnapshotAdmin(admin.ModelAdmin):
    """Admin for MarketDataSnapshot"""
    
    list_display = (
        'symbol', 'price', 'change_colored', 'change_percent_colored',
        'volume', 'exchange', 'timestamp'
    )
    list_filter = ('exchange', 'symbol', 'timestamp')
    search_fields = ('symbol',)
    ordering = ('-timestamp',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'spread_display')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('symbol', 'exchange', 'timestamp')
        }),
        ('Price Data', {
            'fields': ('price', 'change', 'change_percent', 'bid', 'ask', 'spread_display')
        }),
        ('Volume', {
            'fields': ('volume',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def change_colored(self, obj):
        """Display change with color coding"""
        if obj.change > 0:
            return format_html(
                '<span style="color: green;">+{}</span>',
                obj.change
            )
        elif obj.change < 0:
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.change
            )
        return obj.change
    change_colored.short_description = 'Change'
    
    def change_percent_colored(self, obj):
        """Display change percent with color coding"""
        if obj.change_percent > 0:
            return format_html(
                '<span style="color: green;">+{:.2f}%</span>',
                obj.change_percent
            )
        elif obj.change_percent < 0:
            return format_html(
                '<span style="color: red;">{:.2f}%</span>',
                obj.change_percent
            )
        return f"{obj.change_percent:.2f}%"
    change_percent_colored.short_description = 'Change %'
    
    def spread_display(self, obj):
        """Display bid-ask spread"""
        spread = obj.get_spread()
        spread_percent = obj.get_spread_percent()
        return f"{spread} ({spread_percent:.4f}%)"
    spread_display.short_description = 'Bid-Ask Spread'


@admin.register(SymbolSubscription)
class SymbolSubscriptionAdmin(admin.ModelAdmin):
    """Admin for SymbolSubscription"""
    
    list_display = (
        'user', 'symbol', 'is_active', 'subscribed_at', 'last_price_update'
    )
    list_filter = ('is_active', 'symbol', 'subscribed_at')
    search_fields = ('user__username', 'user__email', 'symbol')
    ordering = ('-subscribed_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        """Activate selected subscriptions"""
        count = 0
        for subscription in queryset:
            subscription.activate()
            count += 1
        self.message_user(request, f'Activated {count} subscriptions.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        """Deactivate selected subscriptions"""
        count = 0
        for subscription in queryset:
            subscription.deactivate()
            count += 1
        self.message_user(request, f'Deactivated {count} subscriptions.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'


@admin.register(MarketEvent)
class MarketEventAdmin(admin.ModelAdmin):
    """Admin for MarketEvent"""
    
    list_display = (
        'symbol', 'event_type', 'impact_colored', 'title',
        'is_active', 'event_timestamp'
    )
    list_filter = ('event_type', 'impact', 'is_active', 'event_timestamp')
    search_fields = ('symbol', 'title', 'description')
    ordering = ('-event_timestamp',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def impact_colored(self, obj):
        """Display impact with color coding"""
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.impact, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.impact.upper()
        )
    impact_colored.short_description = 'Impact'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order"""
    
    list_display = (
        'order_id', 'user', 'symbol', 'side_colored', 'order_type',
        'quantity', 'price', 'status_colored', 'created_at'
    )
    list_filter = ('status', 'side', 'order_type', 'exchange', 'created_at')
    search_fields = ('order_id', 'user__username', 'symbol')
    ordering = ('-created_at',)
    readonly_fields = (
        'id', 'order_id', 'created_at', 'updated_at', 'remaining_quantity',
        'is_fully_filled', 'is_active'
    )
    
    def side_colored(self, obj):
        """Display order side with color coding"""
        color = 'green' if obj.side == 'buy' else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.side.upper()
        )
    side_colored.short_description = 'Side'
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'orange',
            'submitted': 'blue',
            'partial': 'purple',
            'filled': 'green',
            'cancelled': 'gray',
            'rejected': 'red',
            'expired': 'darkgray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_colored.short_description = 'Status'


@admin.register(WebSocketConnection)
class WebSocketConnectionAdmin(admin.ModelAdmin):
    """Admin for WebSocketConnection"""
    
    list_display = (
        'channel_name_short', 'user', 'status_colored', 'subscription_count',
        'connected_at', 'session_duration_display'
    )
    list_filter = ('status', 'connected_at', 'disconnected_at')
    search_fields = ('user__username', 'channel_name', 'ip_address')
    ordering = ('-last_activity',)
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'is_active', 'session_duration_display'
    )
    
    def channel_name_short(self, obj):
        """Display shortened channel name"""
        return obj.channel_name[-16:] if len(obj.channel_name) > 16 else obj.channel_name
    channel_name_short.short_description = 'Channel'
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'connecting': 'orange',
            'connected': 'blue',
            'authenticated': 'green',
            'disconnected': 'gray',
            'error': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_colored.short_description = 'Status'
    
    def session_duration_display(self, obj):
        """Display session duration"""
        duration = obj.session_duration
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        seconds = duration.total_seconds() % 60
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    session_duration_display.short_description = 'Session Duration'

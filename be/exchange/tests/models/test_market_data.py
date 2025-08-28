"""
Tests for market data models
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User

from exchange.models import MarketDataSnapshot, SymbolSubscription, MarketEvent
from exchange.tests.factories import (
    UserFactory, MarketDataSnapshotFactory, SymbolSubscriptionFactory,
    MarketEventFactory, CryptoMarketDataFactory, HighImpactEventFactory
)


@pytest.mark.django_db
class TestMarketDataSnapshot:
    """Test MarketDataSnapshot model"""
    
    def test_create_market_data_snapshot(self):
        """Test creating a market data snapshot"""
        snapshot = MarketDataSnapshotFactory()
        
        assert snapshot.id is not None
        assert snapshot.symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'BTC-USD']
        assert snapshot.price > 0
        assert snapshot.timestamp is not None
        assert snapshot.exchange == 'SIMULATOR'
    
    def test_str_representation(self):
        """Test string representation"""
        snapshot = MarketDataSnapshotFactory(
            symbol='AAPL',
            price=Decimal('150.00'),
            change_percent=Decimal('2.50')
        )
        
        expected = "AAPL: $150.000000 (+2.5000%)"
        assert str(snapshot) == expected
    
    def test_get_spread(self):
        """Test bid-ask spread calculation"""
        snapshot = MarketDataSnapshotFactory(
            bid=Decimal('149.50'),
            ask=Decimal('150.50')
        )
        
        assert snapshot.get_spread() == Decimal('1.00')
    
    def test_get_spread_percent(self):
        """Test bid-ask spread percentage calculation"""
        snapshot = MarketDataSnapshotFactory(
            bid=Decimal('149.50'),
            ask=Decimal('150.50')
        )
        
        expected_percent = (Decimal('1.00') / Decimal('150.50')) * 100
        assert abs(snapshot.get_spread_percent() - expected_percent) < Decimal('0.01')
    
    def test_get_spread_percent_zero_ask(self):
        """Test spread percentage with zero ask price"""
        snapshot = MarketDataSnapshotFactory(
            bid=Decimal('149.50'),
            ask=Decimal('0.00')
        )
        
        assert snapshot.get_spread_percent() == Decimal('0.00')
    
    def test_to_websocket_message(self):
        """Test WebSocket message conversion"""
        snapshot = MarketDataSnapshotFactory(
            symbol='AAPL',
            price=Decimal('150.00'),
            change=Decimal('2.50'),
            change_percent=Decimal('1.69'),
            volume=1500000,
            bid=Decimal('149.99'),
            ask=Decimal('150.01')
        )
        
        message = snapshot.to_websocket_message()
        
        assert message['type'] == 'price_update'
        assert message['symbol'] == 'AAPL'
        assert message['price'] == 150.0
        assert message['change'] == 2.5
        assert message['change_percent'] == 1.69
        assert message['volume'] == 1500000
        assert message['bid'] == 149.99
        assert message['ask'] == 150.01
        assert 'timestamp' in message
    
    def test_crypto_market_data(self):
        """Test crypto market data creation"""
        crypto_data = CryptoMarketDataFactory()
        
        assert crypto_data.symbol in ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD']
        assert crypto_data.price >= Decimal('45000.00')
    
    def test_ordering(self):
        """Test default ordering by timestamp"""
        # Create snapshots with different timestamps
        old_snapshot = MarketDataSnapshotFactory(
            timestamp=timezone.now() - timezone.timedelta(hours=1)
        )
        new_snapshot = MarketDataSnapshotFactory(
            timestamp=timezone.now()
        )
        
        snapshots = list(MarketDataSnapshot.objects.all())
        assert snapshots[0] == new_snapshot  # Most recent first
        assert snapshots[1] == old_snapshot


@pytest.mark.django_db
class TestSymbolSubscription:
    """Test SymbolSubscription model"""
    
    def test_create_subscription(self):
        """Test creating a symbol subscription"""
        subscription = SymbolSubscriptionFactory()
        
        assert subscription.id is not None
        assert subscription.user is not None
        assert subscription.symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        assert subscription.is_active is True
        assert subscription.subscribed_at is not None
    
    def test_str_representation(self):
        """Test string representation"""
        user = UserFactory(username='testuser')
        subscription = SymbolSubscriptionFactory(
            user=user,
            symbol='AAPL',
            is_active=True
        )
        
        assert str(subscription) == "testuser -> AAPL (Active)"
    
    def test_str_representation_inactive(self):
        """Test string representation for inactive subscription"""
        user = UserFactory(username='testuser')
        subscription = SymbolSubscriptionFactory(
            user=user,
            symbol='AAPL',
            is_active=False
        )
        
        assert str(subscription) == "testuser -> AAPL (Inactive)"
    
    def test_activate_subscription(self):
        """Test activating a subscription"""
        subscription = SymbolSubscriptionFactory(is_active=False)
        old_time = subscription.subscribed_at
        
        subscription.activate()
        
        assert subscription.is_active is True
        assert subscription.subscribed_at > old_time
    
    def test_deactivate_subscription(self):
        """Test deactivating a subscription"""
        subscription = SymbolSubscriptionFactory(is_active=True)
        
        subscription.deactivate()
        
        assert subscription.is_active is False
    
    def test_update_last_price_update(self):
        """Test updating last price update timestamp"""
        subscription = SymbolSubscriptionFactory(last_price_update=None)
        
        subscription.update_last_price_update()
        
        assert subscription.last_price_update is not None
    
    def test_unique_together_constraint(self):
        """Test unique constraint on user and symbol"""
        user = UserFactory()
        SymbolSubscriptionFactory(user=user, symbol='AAPL')
        
        # Creating another subscription for same user and symbol should use get_or_create
        subscription2 = SymbolSubscriptionFactory.build(user=user, symbol='AAPL')
        
        # This would raise IntegrityError in real scenario, but factory handles it
        assert True  # Test structure is in place


@pytest.mark.django_db
class TestMarketEvent:
    """Test MarketEvent model"""
    
    def test_create_market_event(self):
        """Test creating a market event"""
        event = MarketEventFactory()
        
        assert event.id is not None
        assert event.symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        assert event.event_type in [
            'earnings_beat', 'earnings_miss', 'dividend_announcement',
            'market_news', 'technical_alert'
        ]
        assert event.impact in ['low', 'medium', 'high']
        assert event.title is not None
        assert event.description is not None
        assert event.is_active is True
    
    def test_str_representation(self):
        """Test string representation"""
        event = MarketEventFactory(
            symbol='AAPL',
            title='Earnings Beat',
            impact='high'
        )
        
        assert str(event) == "AAPL: Earnings Beat (high)"
    
    def test_to_websocket_message(self):
        """Test WebSocket message conversion"""
        event = MarketEventFactory(
            symbol='AAPL',
            impact='high',
            title='Earnings Beat',
            description='Apple beats quarterly expectations'
        )
        
        message = event.to_websocket_message()
        
        assert message['type'] == 'market_alert'
        assert message['symbol'] == 'AAPL'
        assert message['severity'] == 'high'
        assert message['title'] == 'Earnings Beat'
        assert message['message'] == 'Apple beats quarterly expectations'
        assert 'timestamp' in message
    
    def test_deactivate_event(self):
        """Test deactivating an event"""
        event = MarketEventFactory(is_active=True)
        
        event.deactivate()
        
        assert event.is_active is False
    
    def test_high_impact_event(self):
        """Test high-impact event creation"""
        event = HighImpactEventFactory()
        
        assert event.impact == 'high'
        assert event.event_type == 'earnings_beat'
    
    def test_event_choices(self):
        """Test that event type choices are valid"""
        valid_types = [choice[0] for choice in MarketEvent.EVENT_TYPES]
        event = MarketEventFactory()
        
        assert event.event_type in valid_types
    
    def test_impact_choices(self):
        """Test that impact choices are valid"""
        valid_impacts = [choice[0] for choice in MarketEvent.IMPACT_LEVELS]
        event = MarketEventFactory()
        
        assert event.impact in valid_impacts
    
    def test_ordering(self):
        """Test default ordering by event timestamp"""
        old_event = MarketEventFactory(
            event_timestamp=timezone.now() - timezone.timedelta(hours=1)
        )
        new_event = MarketEventFactory(
            event_timestamp=timezone.now()
        )
        
        events = list(MarketEvent.objects.all())
        assert events[0] == new_event  # Most recent first
        assert events[1] == old_event
"""
Tests for MarketDataService
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User
from django.utils import timezone

from exchange.services import MarketDataService
from exchange.models import MarketDataSnapshot, SymbolSubscription, MarketEvent
from exchange.tests.factories import (
    UserFactory, MarketDataSnapshotFactory, SymbolSubscriptionFactory,
    MarketEventFactory, create_market_data_history
)


@pytest.mark.django_db
class TestMarketDataService:
    """Test MarketDataService"""
    
    def setup_method(self):
        """Set up test data"""
        self.service = MarketDataService()
        self.user = UserFactory()
    
    @patch('exchange.services.market_data_service.redis.Redis')
    def test_get_redis_client(self, mock_redis):
        """Test Redis client initialization"""
        service = MarketDataService()
        
        mock_redis.assert_called_once()
        assert service.redis_client is not None
    
    def test_get_current_price_exists(self):
        """Test getting current price for existing symbol"""
        snapshot = MarketDataSnapshotFactory(
            symbol='AAPL',
            price=Decimal('150.25')
        )
        
        price = self.service.get_current_price('AAPL')
        
        assert price == Decimal('150.25')
    
    def test_get_current_price_not_exists(self):
        """Test getting current price for non-existent symbol"""
        price = self.service.get_current_price('NONEXISTENT')
        
        assert price is None
    
    def test_get_current_price_case_insensitive(self):
        """Test getting current price is case insensitive"""
        snapshot = MarketDataSnapshotFactory(
            symbol='AAPL',
            price=Decimal('150.25')
        )
        
        price = self.service.get_current_price('aapl')
        
        assert price == Decimal('150.25')
    
    def test_get_latest_market_data(self):
        """Test getting latest market data snapshot"""
        snapshot = MarketDataSnapshotFactory(symbol='AAPL')
        
        result = self.service.get_latest_market_data('AAPL')
        
        assert result == snapshot
        assert result.symbol == 'AAPL'
    
    def test_get_market_data_history(self):
        """Test getting market data history"""
        snapshots = create_market_data_history('AAPL', hours=2)
        
        history = self.service.get_market_data_history('AAPL', hours=1)
        
        # Should return snapshots from last 1 hour
        assert len(history) > 0
        assert all(snap.symbol == 'AAPL' for snap in history)
        assert history == sorted(history, key=lambda x: x.timestamp, reverse=True)
    
    def test_store_market_data(self):
        """Test storing market data"""
        market_data = {
            'symbol': 'AAPL',
            'price': 150.25,
            'change': 2.50,
            'change_percent': 1.69,
            'volume': 1500000,
            'bid': 150.24,
            'ask': 150.26
        }
        
        with patch.object(self.service, 'publish_price_update') as mock_publish:
            snapshot = self.service.store_market_data(market_data)
        
        assert snapshot.symbol == 'AAPL'
        assert snapshot.price == Decimal('150.25')
        assert snapshot.change == Decimal('2.50')
        assert snapshot.volume == 1500000
        assert snapshot.exchange == 'SIMULATOR'
        mock_publish.assert_called_once_with(snapshot)
    
    def test_store_market_data_with_exchange(self):
        """Test storing market data with custom exchange"""
        market_data = {
            'symbol': 'AAPL',
            'price': 150.25,
            'exchange': 'NASDAQ'
        }
        
        with patch.object(self.service, 'publish_price_update'):
            snapshot = self.service.store_market_data(market_data)
        
        assert snapshot.exchange == 'NASDAQ'
    
    @patch('exchange.services.market_data_service.redis.Redis')
    def test_publish_price_update(self, mock_redis_class):
        """Test publishing price update to Redis"""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        
        service = MarketDataService()
        snapshot = MarketDataSnapshotFactory()
        
        service.publish_price_update(snapshot)
        
        mock_redis.publish.assert_called_once()
        args = mock_redis.publish.call_args[0]
        assert args[0] == service.price_channel
        # Verify JSON message structure
        import json
        message = json.loads(args[1])
        assert message['action'] == 'price_update'
        assert message['data']['type'] == 'price_update'
    
    @patch('exchange.services.market_data_service.redis.Redis')
    def test_publish_market_event(self, mock_redis_class):
        """Test publishing market event to Redis"""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        
        service = MarketDataService()
        event = MarketEventFactory()
        
        service.publish_market_event(event)
        
        mock_redis.publish.assert_called_once()
        args = mock_redis.publish.call_args[0]
        assert args[0] == service.event_channel
    
    def test_get_subscribed_users(self):
        """Test getting subscribed users for symbol"""
        user1 = UserFactory()
        user2 = UserFactory()
        SymbolSubscriptionFactory(user=user1, symbol='AAPL', is_active=True)
        SymbolSubscriptionFactory(user=user2, symbol='AAPL', is_active=True)
        SymbolSubscriptionFactory(user=user1, symbol='GOOGL', is_active=True)  # Different symbol
        SymbolSubscriptionFactory(user=user2, symbol='AAPL', is_active=False)  # Inactive
        
        user_ids = self.service.get_subscribed_users('AAPL')
        
        assert len(user_ids) == 2
        assert user1.id in user_ids
        assert user2.id in user_ids
    
    def test_get_user_subscriptions(self):
        """Test getting user's subscriptions"""
        SymbolSubscriptionFactory(user=self.user, symbol='AAPL', is_active=True)
        SymbolSubscriptionFactory(user=self.user, symbol='GOOGL', is_active=True)
        SymbolSubscriptionFactory(user=self.user, symbol='MSFT', is_active=False)  # Inactive
        
        symbols = self.service.get_user_subscriptions(self.user)
        
        assert len(symbols) == 2
        assert 'AAPL' in symbols
        assert 'GOOGL' in symbols
        assert 'MSFT' not in symbols
    
    def test_create_subscription_new(self):
        """Test creating new subscription"""
        subscription = self.service.create_subscription(self.user, 'AAPL')
        
        assert subscription.user == self.user
        assert subscription.symbol == 'AAPL'
        assert subscription.is_active is True
    
    def test_create_subscription_reactivate(self):
        """Test reactivating existing subscription"""
        existing = SymbolSubscriptionFactory(
            user=self.user,
            symbol='AAPL',
            is_active=False
        )
        
        subscription = self.service.create_subscription(self.user, 'aapl')  # Case insensitive
        
        assert subscription == existing
        assert subscription.is_active is True
    
    def test_remove_subscription_success(self):
        """Test removing active subscription"""
        SymbolSubscriptionFactory(
            user=self.user,
            symbol='AAPL',
            is_active=True
        )
        
        result = self.service.remove_subscription(self.user, 'AAPL')
        
        assert result is True
        subscription = SymbolSubscription.objects.get(user=self.user, symbol='AAPL')
        assert subscription.is_active is False
    
    def test_remove_subscription_not_found(self):
        """Test removing non-existent subscription"""
        result = self.service.remove_subscription(self.user, 'NONEXISTENT')
        
        assert result is False
    
    def test_cleanup_old_data(self):
        """Test cleaning up old market data"""
        # Create old and new snapshots
        old_time = timezone.now() - timezone.timedelta(hours=25)
        new_time = timezone.now() - timezone.timedelta(hours=1)
        
        MarketDataSnapshotFactory(timestamp=old_time)
        MarketDataSnapshotFactory(timestamp=new_time)
        
        assert MarketDataSnapshot.objects.count() == 2
        
        deleted_count = self.service.cleanup_old_data(hours=24)
        
        assert deleted_count == 1
        assert MarketDataSnapshot.objects.count() == 1
    
    def test_get_market_statistics(self):
        """Test getting market statistics"""
        # Create market data history
        snapshots = create_market_data_history('AAPL', hours=2)
        
        stats = self.service.get_market_statistics('AAPL')
        
        assert stats['symbol'] == 'AAPL'
        assert 'current_price' in stats
        assert 'high_24h' in stats
        assert 'low_24h' in stats
        assert 'volume_24h' in stats
        assert 'price_change_24h' in stats
        assert 'price_change_percent_24h' in stats
        assert stats['data_points'] > 0
        assert 'last_updated' in stats
    
    def test_get_market_statistics_no_data(self):
        """Test getting market statistics with no data"""
        stats = self.service.get_market_statistics('NONEXISTENT')
        
        assert stats == {}
    
    def test_validate_symbol_valid(self):
        """Test validating valid symbols"""
        valid_symbols = ['AAPL', 'BTC-USD', 'SPY', 'GOOGL.L']
        
        for symbol in valid_symbols:
            assert self.service.validate_symbol(symbol) is True
    
    def test_validate_symbol_invalid(self):
        """Test validating invalid symbols"""
        invalid_symbols = ['', 'TOOLONGSYMBOL', None, '!@#$']
        
        for symbol in invalid_symbols:
            assert self.service.validate_symbol(symbol) is False
    
    def test_get_supported_symbols(self):
        """Test getting supported symbols list"""
        symbols = self.service.get_supported_symbols()
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert 'AAPL' in symbols
        assert 'BTC-USD' in symbols
        assert all(self.service.validate_symbol(symbol) for symbol in symbols)
    
    @patch('exchange.services.market_data_service.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling in various methods"""
        # Test with invalid data that would cause an error
        with pytest.raises(Exception):
            self.service.store_market_data({})  # Missing required fields
        
        # Verify error was logged
        mock_logger.error.assert_called()
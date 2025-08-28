"""
Test factories for exchange models
"""

import factory
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone

from exchange.models import (
    MarketDataSnapshot, SymbolSubscription, MarketEvent,
    Order, OrderExecution, WebSocketConnection, ConnectionEvent
)


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model"""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class MarketDataSnapshotFactory(factory.django.DjangoModelFactory):
    """Factory for MarketDataSnapshot model"""
    
    class Meta:
        model = MarketDataSnapshot
    
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'BTC-USD'])
    price = factory.LazyFunction(lambda: Decimal('150.00'))
    change = factory.LazyFunction(lambda: Decimal('2.50'))
    change_percent = factory.LazyFunction(lambda: Decimal('1.69'))
    volume = factory.LazyFunction(lambda: 1500000)
    bid = factory.LazyAttribute(lambda obj: obj.price - Decimal('0.01'))
    ask = factory.LazyAttribute(lambda obj: obj.price + Decimal('0.01'))
    timestamp = factory.LazyFunction(timezone.now)
    exchange = 'SIMULATOR'


class CryptoMarketDataFactory(MarketDataSnapshotFactory):
    """Factory for crypto market data"""
    symbol = factory.Iterator(['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD'])
    price = factory.LazyFunction(lambda: Decimal('45000.00'))
    bid = factory.LazyAttribute(lambda obj: obj.price - Decimal('10.00'))
    ask = factory.LazyAttribute(lambda obj: obj.price + Decimal('10.00'))


class VolatileMarketDataFactory(MarketDataSnapshotFactory):
    """Factory for volatile market data"""
    change = factory.LazyFunction(lambda: Decimal('-15.50'))
    change_percent = factory.LazyFunction(lambda: Decimal('-8.25'))


class SymbolSubscriptionFactory(factory.django.DjangoModelFactory):
    """Factory for SymbolSubscription model"""
    
    class Meta:
        model = SymbolSubscription
        django_get_or_create = ('user', 'symbol')
    
    user = factory.SubFactory(UserFactory)
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    is_active = True
    subscribed_at = factory.LazyFunction(timezone.now)
    last_price_update = None


class InactiveSubscriptionFactory(SymbolSubscriptionFactory):
    """Factory for inactive subscriptions"""
    is_active = False


class MarketEventFactory(factory.django.DjangoModelFactory):
    """Factory for MarketEvent model"""
    
    class Meta:
        model = MarketEvent
    
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    event_type = factory.Iterator([
        'earnings_beat', 'earnings_miss', 'dividend_announcement',
        'market_news', 'technical_alert'
    ])
    impact = factory.Iterator(['low', 'medium', 'high'])
    title = factory.LazyAttribute(
        lambda obj: f"{obj.symbol} {obj.event_type.replace('_', ' ').title()}"
    )
    description = factory.LazyAttribute(
        lambda obj: f"Market event for {obj.symbol}: {obj.title}"
    )
    event_timestamp = factory.LazyFunction(timezone.now)
    is_active = True


class HighImpactEventFactory(MarketEventFactory):
    """Factory for high-impact events"""
    impact = 'high'
    event_type = 'earnings_beat'


class OrderFactory(factory.django.DjangoModelFactory):
    """Factory for Order model"""
    
    class Meta:
        model = Order
    
    user = factory.SubFactory(UserFactory)
    order_id = factory.LazyFunction(lambda: f"ord_{uuid.uuid4().hex[:12]}")
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    side = factory.Iterator(['buy', 'sell'])
    order_type = factory.Iterator(['market', 'limit'])
    quantity = factory.LazyFunction(lambda: Decimal('100.00'))
    price = factory.Maybe(
        'order_type__in=["limit", "stop_limit"]',
        yes_declaration=factory.LazyFunction(lambda: Decimal('150.00')),
        no_declaration=None
    )
    status = 'pending'
    time_in_force = 'day'
    exchange = 'SIMULATOR'


class MarketOrderFactory(OrderFactory):
    """Factory for market orders"""
    order_type = 'market'
    price = None


class LimitOrderFactory(OrderFactory):
    """Factory for limit orders"""
    order_type = 'limit'
    price = factory.LazyFunction(lambda: Decimal('150.00'))


class BuyOrderFactory(OrderFactory):
    """Factory for buy orders"""
    side = 'buy'


class SellOrderFactory(OrderFactory):
    """Factory for sell orders"""
    side = 'sell'


class SubmittedOrderFactory(OrderFactory):
    """Factory for submitted orders"""
    status = 'submitted'
    submitted_at = factory.LazyFunction(timezone.now)


class FilledOrderFactory(OrderFactory):
    """Factory for filled orders"""
    status = 'filled'
    filled_quantity = factory.LazyAttribute(lambda obj: obj.quantity)
    average_fill_price = factory.LazyFunction(lambda: Decimal('150.25'))
    submitted_at = factory.LazyFunction(timezone.now)
    filled_at = factory.LazyFunction(timezone.now)


class CancelledOrderFactory(OrderFactory):
    """Factory for cancelled orders"""
    status = 'cancelled'
    submitted_at = factory.LazyFunction(timezone.now)
    cancelled_at = factory.LazyFunction(timezone.now)


class OrderExecutionFactory(factory.django.DjangoModelFactory):
    """Factory for OrderExecution model"""
    
    class Meta:
        model = OrderExecution
    
    order = factory.SubFactory(SubmittedOrderFactory)
    execution_id = factory.LazyFunction(lambda: f"exec_{uuid.uuid4().hex[:12]}")
    quantity = factory.LazyFunction(lambda: Decimal('50.00'))
    price = factory.LazyFunction(lambda: Decimal('150.25'))
    executed_at = factory.LazyFunction(timezone.now)
    commission = factory.LazyFunction(lambda: Decimal('1.00'))


class PartialExecutionFactory(OrderExecutionFactory):
    """Factory for partial executions"""
    quantity = factory.LazyAttribute(lambda obj: obj.order.quantity / 2)


class WebSocketConnectionFactory(factory.django.DjangoModelFactory):
    """Factory for WebSocketConnection model"""
    
    class Meta:
        model = WebSocketConnection
    
    user = factory.SubFactory(UserFactory)
    channel_name = factory.LazyFunction(
        lambda: f"websocket.{uuid.uuid4().hex[:16]}"
    )
    status = 'connected'
    connected_at = factory.LazyFunction(timezone.now)
    last_activity = factory.LazyFunction(timezone.now)
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    subscription_count = 0


class AuthenticatedConnectionFactory(WebSocketConnectionFactory):
    """Factory for authenticated connections"""
    status = 'authenticated'
    authenticated_at = factory.LazyFunction(timezone.now)


class DisconnectedConnectionFactory(WebSocketConnectionFactory):
    """Factory for disconnected connections"""
    status = 'disconnected'
    disconnected_at = factory.LazyFunction(timezone.now)


class ConnectionEventFactory(factory.django.DjangoModelFactory):
    """Factory for ConnectionEvent model"""
    
    class Meta:
        model = ConnectionEvent
    
    connection = factory.SubFactory(WebSocketConnectionFactory)
    event_type = factory.Iterator([
        'connect', 'authenticate', 'subscribe', 'unsubscribe',
        'message_sent', 'message_received', 'error', 'disconnect'
    ])
    event_data = factory.LazyFunction(lambda: {})
    timestamp = factory.LazyFunction(timezone.now)


class AuthEventFactory(ConnectionEventFactory):
    """Factory for authentication events"""
    event_type = 'authenticate'
    event_data = factory.LazyFunction(lambda: {'user_id': 1})


class SubscribeEventFactory(ConnectionEventFactory):
    """Factory for subscription events"""
    event_type = 'subscribe'
    event_data = factory.LazyFunction(lambda: {'symbols': ['AAPL', 'GOOGL']})


# Batch factories for creating related objects
def create_user_with_orders(user_kwargs=None, order_count=5):
    """Create a user with multiple orders"""
    user_kwargs = user_kwargs or {}
    user = UserFactory(**user_kwargs)
    
    orders = []
    for i in range(order_count):
        if i % 3 == 0:
            order = FilledOrderFactory(user=user)
        elif i % 3 == 1:
            order = SubmittedOrderFactory(user=user)
        else:
            order = CancelledOrderFactory(user=user)
        orders.append(order)
    
    return {'user': user, 'orders': orders}


def create_user_with_subscriptions(user_kwargs=None, subscription_count=5):
    """Create a user with symbol subscriptions"""
    user_kwargs = user_kwargs or {}
    user = UserFactory(**user_kwargs)
    
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    subscriptions = []
    
    for i in range(min(subscription_count, len(symbols))):
        subscription = SymbolSubscriptionFactory(
            user=user,
            symbol=symbols[i]
        )
        subscriptions.append(subscription)
    
    return {'user': user, 'subscriptions': subscriptions}


def create_market_data_history(symbol='AAPL', hours=24):
    """Create historical market data for a symbol"""
    snapshots = []
    base_price = Decimal('150.00')
    
    for i in range(hours * 60 // 5):  # Every 5 minutes
        timestamp = timezone.now() - timedelta(minutes=i * 5)
        price_change = Decimal(str((i % 10 - 5) * 0.5))  # Random walk
        current_price = base_price + price_change
        
        snapshot = MarketDataSnapshotFactory(
            symbol=symbol,
            price=current_price,
            timestamp=timestamp,
            change=price_change,
            change_percent=(price_change / base_price) * 100
        )
        snapshots.append(snapshot)
    
    return snapshots


def create_complete_trading_session(user_kwargs=None):
    """Create a complete trading session with user, orders, executions"""
    user_kwargs = user_kwargs or {}
    user = UserFactory(**user_kwargs)
    
    # Create WebSocket connection
    connection = AuthenticatedConnectionFactory(user=user)
    
    # Create subscriptions
    subscriptions = []
    for symbol in ['AAPL', 'GOOGL', 'MSFT']:
        subscription = SymbolSubscriptionFactory(user=user, symbol=symbol)
        subscriptions.append(subscription)
    
    # Create market data
    market_data = []
    for symbol in ['AAPL', 'GOOGL', 'MSFT']:
        data = MarketDataSnapshotFactory(symbol=symbol)
        market_data.append(data)
    
    # Create orders with executions
    orders = []
    executions = []
    
    # Filled order
    filled_order = FilledOrderFactory(user=user, symbol='AAPL')
    execution = OrderExecutionFactory(order=filled_order)
    orders.append(filled_order)
    executions.append(execution)
    
    # Pending order
    pending_order = SubmittedOrderFactory(user=user, symbol='GOOGL')
    orders.append(pending_order)
    
    # Market events
    events = [
        MarketEventFactory(symbol='AAPL'),
        HighImpactEventFactory(symbol='MSFT')
    ]
    
    return {
        'user': user,
        'connection': connection,
        'subscriptions': subscriptions,
        'market_data': market_data,
        'orders': orders,
        'executions': executions,
        'events': events
    }


# Trait mixins for common scenarios
class VolatileStockTrait:
    """Trait for volatile stock behavior"""
    change_percent = factory.LazyFunction(lambda: Decimal(str(10 * (0.5 - random.random()))))


class CryptoTrait:
    """Trait for cryptocurrency data"""
    symbol = factory.Iterator(['BTC-USD', 'ETH-USD', 'ADA-USD'])
    price = factory.LazyFunction(lambda: Decimal('45000.00'))


class LowVolumeTraitE:
    """Trait for low volume trading"""
    volume = factory.LazyFunction(lambda: 50000)


# Import random for traits
import random
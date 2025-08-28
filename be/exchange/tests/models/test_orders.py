"""
Tests for order models
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User

from exchange.models import Order, OrderExecution
from exchange.tests.factories import (
    UserFactory, OrderFactory, MarketOrderFactory, LimitOrderFactory,
    BuyOrderFactory, SellOrderFactory, SubmittedOrderFactory,
    FilledOrderFactory, CancelledOrderFactory, OrderExecutionFactory,
    PartialExecutionFactory
)


@pytest.mark.django_db
class TestOrder:
    """Test Order model"""
    
    def test_create_order(self):
        """Test creating an order"""
        order = OrderFactory()
        
        assert order.id is not None
        assert order.user is not None
        assert order.order_id.startswith('ord_')
        assert order.symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        assert order.side in ['buy', 'sell']
        assert order.order_type in ['market', 'limit']
        assert order.quantity > 0
        assert order.status == 'pending'
        assert order.exchange == 'SIMULATOR'
    
    def test_str_representation(self):
        """Test string representation"""
        order = OrderFactory(
            order_id='ord_123456789',
            side='buy',
            quantity=Decimal('100'),
            symbol='AAPL',
            price=Decimal('150.00')
        )
        
        assert str(order) == "ord_123456789: BUY 100 AAPL @ 150.00"
    
    def test_str_representation_market_order(self):
        """Test string representation for market order"""
        order = MarketOrderFactory(
            order_id='ord_123456789',
            side='buy',
            quantity=Decimal('100'),
            symbol='AAPL'
        )
        
        assert str(order) == "ord_123456789: BUY 100 AAPL @ MARKET"
    
    def test_remaining_quantity(self):
        """Test remaining quantity calculation"""
        order = OrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('30')
        )
        
        assert order.remaining_quantity == Decimal('70')
    
    def test_is_fully_filled_true(self):
        """Test is_fully_filled property when order is filled"""
        order = OrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('100')
        )
        
        assert order.is_fully_filled is True
    
    def test_is_fully_filled_false(self):
        """Test is_fully_filled property when order is not filled"""
        order = OrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('50')
        )
        
        assert order.is_fully_filled is False
    
    def test_is_active_pending(self):
        """Test is_active property for pending order"""
        order = OrderFactory(status='pending')
        
        assert order.is_active is True
    
    def test_is_active_submitted(self):
        """Test is_active property for submitted order"""
        order = OrderFactory(status='submitted')
        
        assert order.is_active is True
    
    def test_is_active_partial(self):
        """Test is_active property for partially filled order"""
        order = OrderFactory(status='partial')
        
        assert order.is_active is True
    
    def test_is_active_filled(self):
        """Test is_active property for filled order"""
        order = OrderFactory(status='filled')
        
        assert order.is_active is False
    
    def test_is_active_cancelled(self):
        """Test is_active property for cancelled order"""
        order = OrderFactory(status='cancelled')
        
        assert order.is_active is False
    
    def test_submit_order(self):
        """Test submitting an order"""
        order = OrderFactory(status='pending')
        
        order.submit()
        
        assert order.status == 'submitted'
        assert order.submitted_at is not None
    
    def test_fill_order_partial(self):
        """Test partial fill of an order"""
        order = SubmittedOrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('0'),
            average_fill_price=None
        )
        
        order.fill(Decimal('50'), Decimal('150.25'))
        
        assert order.filled_quantity == Decimal('50')
        assert order.average_fill_price == Decimal('150.25')
        assert order.status == 'partial'
        assert order.filled_at is None  # Not fully filled yet
    
    def test_fill_order_complete(self):
        """Test complete fill of an order"""
        order = SubmittedOrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('0'),
            average_fill_price=None
        )
        
        order.fill(Decimal('100'), Decimal('150.25'))
        
        assert order.filled_quantity == Decimal('100')
        assert order.average_fill_price == Decimal('150.25')
        assert order.status == 'filled'
        assert order.filled_at is not None
    
    def test_fill_order_multiple_fills(self):
        """Test multiple fills with average price calculation"""
        order = SubmittedOrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('0'),
            average_fill_price=None
        )
        
        # First fill: 50 shares at $150.00
        order.fill(Decimal('50'), Decimal('150.00'))
        assert order.average_fill_price == Decimal('150.00')
        assert order.status == 'partial'
        
        # Second fill: 50 shares at $151.00
        order.fill(Decimal('50'), Decimal('151.00'))
        assert order.average_fill_price == Decimal('150.50')  # Average
        assert order.status == 'filled'
    
    def test_fill_order_exceeds_quantity(self):
        """Test fill exceeding remaining quantity raises error"""
        order = SubmittedOrderFactory(
            quantity=Decimal('100'),
            filled_quantity=Decimal('80')
        )
        
        with pytest.raises(ValueError, match="Fill quantity exceeds remaining quantity"):
            order.fill(Decimal('30'), Decimal('150.00'))
    
    def test_fill_inactive_order(self):
        """Test filling inactive order raises error"""
        order = FilledOrderFactory()
        
        with pytest.raises(ValueError, match="Cannot fill inactive order"):
            order.fill(Decimal('10'), Decimal('150.00'))
    
    def test_cancel_order(self):
        """Test cancelling an order"""
        order = SubmittedOrderFactory()
        
        order.cancel()
        
        assert order.status == 'cancelled'
        assert order.cancelled_at is not None
    
    def test_cancel_inactive_order(self):
        """Test cancelling inactive order raises error"""
        order = FilledOrderFactory()
        
        with pytest.raises(ValueError, match="Cannot cancel inactive order"):
            order.cancel()
    
    def test_reject_order(self):
        """Test rejecting an order"""
        order = SubmittedOrderFactory()
        
        order.reject("Insufficient funds")
        
        assert order.status == 'rejected'
    
    def test_to_websocket_message(self):
        """Test WebSocket message conversion"""
        order = FilledOrderFactory(
            order_id='ord_123456789',
            symbol='AAPL',
            status='filled',
            quantity=Decimal('100'),
            filled_quantity=Decimal('100'),
            average_fill_price=Decimal('150.25')
        )
        
        message = order.to_websocket_message()
        
        assert message['type'] == 'order_executed'
        assert message['order_id'] == 'ord_123456789'
        assert message['symbol'] == 'AAPL'
        assert message['status'] == 'filled'
        assert message['quantity'] == 100.0
        assert message['filled_quantity'] == 100.0
        assert message['price'] == 150.25
        assert 'timestamp' in message
    
    def test_market_order_factory(self):
        """Test market order factory"""
        order = MarketOrderFactory()
        
        assert order.order_type == 'market'
        assert order.price is None
    
    def test_limit_order_factory(self):
        """Test limit order factory"""
        order = LimitOrderFactory()
        
        assert order.order_type == 'limit'
        assert order.price is not None
    
    def test_buy_order_factory(self):
        """Test buy order factory"""
        order = BuyOrderFactory()
        
        assert order.side == 'buy'
    
    def test_sell_order_factory(self):
        """Test sell order factory"""
        order = SellOrderFactory()
        
        assert order.side == 'sell'


@pytest.mark.django_db
class TestOrderExecution:
    """Test OrderExecution model"""
    
    def test_create_execution(self):
        """Test creating an order execution"""
        execution = OrderExecutionFactory()
        
        assert execution.id is not None
        assert execution.order is not None
        assert execution.execution_id.startswith('exec_')
        assert execution.quantity > 0
        assert execution.price > 0
        assert execution.executed_at is not None
        assert execution.commission >= 0
    
    def test_str_representation(self):
        """Test string representation"""
        execution = OrderExecutionFactory(
            execution_id='exec_123456789',
            quantity=Decimal('50'),
            price=Decimal('150.25')
        )
        
        assert str(execution) == "exec_123456789: 50 @ 150.25"
    
    def test_total_value(self):
        """Test total execution value calculation"""
        execution = OrderExecutionFactory(
            quantity=Decimal('100'),
            price=Decimal('150.25')
        )
        
        assert execution.total_value == Decimal('15025.00')
    
    def test_net_value(self):
        """Test net execution value calculation"""
        execution = OrderExecutionFactory(
            quantity=Decimal('100'),
            price=Decimal('150.25'),
            commission=Decimal('5.00')
        )
        
        assert execution.net_value == Decimal('15020.00')  # 15025 - 5
    
    def test_partial_execution_factory(self):
        """Test partial execution factory"""
        order = SubmittedOrderFactory(quantity=Decimal('100'))
        execution = PartialExecutionFactory(order=order)
        
        assert execution.quantity == Decimal('50')  # Half of order quantity
        assert execution.order == order
    
    def test_execution_ordering(self):
        """Test default ordering by execution time"""
        order = SubmittedOrderFactory()
        
        old_execution = OrderExecutionFactory(
            order=order,
            executed_at=timezone.now() - timezone.timedelta(minutes=30)
        )
        new_execution = OrderExecutionFactory(
            order=order,
            executed_at=timezone.now()
        )
        
        executions = list(OrderExecution.objects.all())
        assert executions[0] == new_execution  # Most recent first
        assert executions[1] == old_execution
    
    def test_order_relationship(self):
        """Test relationship between order and executions"""
        order = SubmittedOrderFactory()
        execution1 = OrderExecutionFactory(order=order)
        execution2 = OrderExecutionFactory(order=order)
        
        assert execution1 in order.executions.all()
        assert execution2 in order.executions.all()
        assert order.executions.count() == 2
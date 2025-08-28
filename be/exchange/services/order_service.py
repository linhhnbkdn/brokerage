"""
Order service for exchange integration
"""

import uuid
import redis
import json
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction

from exchange.models import Order, OrderExecution, MarketDataSnapshot

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing order operations"""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.order_channel = "market_data:orders"
        
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance"""
        config = settings.REDIS_CONFIG
        return redis.Redis(
            host=config['HOST'],
            port=config['PORT'],
            db=config['DB'],
            decode_responses=True
        )
    
    @transaction.atomic
    def place_order(self, user: User, order_data: Dict[str, Any]) -> Order:
        """Place a new order"""
        try:
            # Generate unique order ID
            order_id = f"ord_{uuid.uuid4().hex[:12]}"
            
            # Validate order data
            self._validate_order_data(order_data)
            
            # Create order
            order = Order.objects.create(
                user=user,
                order_id=order_id,
                symbol=order_data['symbol'].upper(),
                side=order_data['side'].lower(),
                order_type=order_data.get('order_type', 'market').lower(),
                quantity=Decimal(str(order_data['quantity'])),
                price=Decimal(str(order_data['price'])) if order_data.get('price') else None,
                stop_price=Decimal(str(order_data['stop_price'])) if order_data.get('stop_price') else None,
                time_in_force=order_data.get('time_in_force', 'day').lower()
            )
            
            # Submit to exchange simulator
            self._submit_to_exchange(order)
            
            logger.info(f"Order placed: {order_id} for user {user.username}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise
    
    def _validate_order_data(self, order_data: Dict[str, Any]) -> None:
        """Validate order data"""
        required_fields = ['symbol', 'side', 'quantity']
        for field in required_fields:
            if not order_data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Validate side
        if order_data['side'].lower() not in ['buy', 'sell']:
            raise ValueError("Invalid order side")
        
        # Validate quantity
        try:
            quantity = Decimal(str(order_data['quantity']))
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError):
            raise ValueError("Invalid quantity format")
        
        # Validate price for limit orders
        order_type = order_data.get('order_type', 'market').lower()
        if order_type in ['limit', 'stop_limit'] and not order_data.get('price'):
            raise ValueError("Price required for limit orders")
        
        if order_data.get('price'):
            try:
                price = Decimal(str(order_data['price']))
                if price <= 0:
                    raise ValueError("Price must be positive")
            except (ValueError, TypeError):
                raise ValueError("Invalid price format")
    
    def _submit_to_exchange(self, order: Order) -> None:
        """Submit order to exchange simulator"""
        try:
            order.submit()
            
            # Publish to Redis for processing
            message = {
                'action': 'new_order',
                'order_id': order.order_id,
                'user_id': order.user.id,
                'symbol': order.symbol,
                'side': order.side,
                'order_type': order.order_type,
                'quantity': float(order.quantity),
                'price': float(order.price) if order.price else None,
                'timestamp': order.submitted_at.isoformat()
            }
            
            self.redis_client.publish(
                self.order_channel,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error submitting order to exchange: {str(e)}")
            raise
    
    def execute_order(self, order: Order, execution_data: Dict[str, Any]) -> OrderExecution:
        """Execute an order (simulate fill)"""
        try:
            with transaction.atomic():
                # Create execution record
                execution = OrderExecution.objects.create(
                    order=order,
                    execution_id=f"exec_{uuid.uuid4().hex[:12]}",
                    quantity=Decimal(str(execution_data['quantity'])),
                    price=Decimal(str(execution_data['price'])),
                    commission=Decimal(str(execution_data.get('commission', '0.00')))
                )
                
                # Update order
                order.fill(execution.quantity, execution.price)
                
                # Publish execution update
                self._publish_order_update(order)
                
                logger.info(f"Order executed: {order.order_id}, {execution.quantity} @ {execution.price}")
                return execution
                
        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            raise
    
    def cancel_order(self, order: Order) -> bool:
        """Cancel an order"""
        try:
            if not order.is_active:
                raise ValueError("Cannot cancel inactive order")
            
            order.cancel()
            self._publish_order_update(order)
            
            logger.info(f"Order cancelled: {order.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def _publish_order_update(self, order: Order) -> None:
        """Publish order update to Redis"""
        try:
            message = {
                'action': 'order_update',
                'user_id': order.user.id,
                'data': order.to_websocket_message()
            }
            
            self.redis_client.publish(
                self.order_channel,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error publishing order update: {str(e)}")
    
    def get_user_orders(
        self, 
        user: User, 
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get user's orders"""
        try:
            queryset = Order.objects.filter(user=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return list(queryset.order_by('-created_at')[:limit])
            
        except Exception as e:
            logger.error(f"Error getting user orders: {str(e)}")
            return []
    
    def get_order_by_id(self, order_id: str, user: User = None) -> Optional[Order]:
        """Get order by ID"""
        try:
            queryset = Order.objects.filter(order_id=order_id)
            
            if user:
                queryset = queryset.filter(user=user)
            
            return queryset.first()
            
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            return None
    
    def get_order_executions(self, order: Order) -> List[OrderExecution]:
        """Get executions for an order"""
        try:
            return list(order.executions.order_by('-executed_at'))
            
        except Exception as e:
            logger.error(f"Error getting order executions: {str(e)}")
            return []
    
    def simulate_market_order_execution(self, order: Order) -> Optional[OrderExecution]:
        """Simulate immediate execution of market order"""
        try:
            # Get current market price
            market_data = MarketDataSnapshot.objects.filter(
                symbol=order.symbol
            ).first()
            
            if not market_data:
                logger.warning(f"No market data for symbol {order.symbol}")
                return None
            
            # Determine execution price based on order side
            if order.side == 'buy':
                execution_price = market_data.ask
            else:
                execution_price = market_data.bid
            
            # Calculate commission (simplified)
            commission = min(
                Decimal('9.99'),  # Max commission
                order.quantity * execution_price * Decimal('0.001')  # 0.1% commission
            )
            
            execution_data = {
                'quantity': order.quantity,
                'price': execution_price,
                'commission': commission
            }
            
            return self.execute_order(order, execution_data)
            
        except Exception as e:
            logger.error(f"Error simulating market order execution: {str(e)}")
            return None
    
    def check_limit_order_triggers(self, symbol: str, current_price: Decimal) -> List[Order]:
        """Check for limit orders that should be triggered"""
        try:
            triggered_orders = []
            
            # Check buy limit orders (trigger when price <= limit price)
            buy_orders = Order.objects.filter(
                symbol=symbol,
                side='buy',
                order_type='limit',
                status__in=['submitted', 'partial'],
                price__gte=current_price
            )
            
            # Check sell limit orders (trigger when price >= limit price)
            sell_orders = Order.objects.filter(
                symbol=symbol,
                side='sell',
                order_type='limit',
                status__in=['submitted', 'partial'],
                price__lte=current_price
            )
            
            triggered_orders.extend(buy_orders)
            triggered_orders.extend(sell_orders)
            
            return triggered_orders
            
        except Exception as e:
            logger.error(f"Error checking limit order triggers: {str(e)}")
            return []
    
    def get_order_book_summary(self, symbol: str) -> Dict[str, Any]:
        """Get order book summary for symbol"""
        try:
            # Get active orders
            buy_orders = Order.objects.filter(
                symbol=symbol,
                side='buy',
                status__in=['submitted', 'partial']
            ).order_by('-price')[:10]
            
            sell_orders = Order.objects.filter(
                symbol=symbol,
                side='sell',
                status__in=['submitted', 'partial']
            ).order_by('price')[:10]
            
            # Format order book
            bids = []
            for order in buy_orders:
                bids.append({
                    'price': float(order.price or 0),
                    'quantity': float(order.remaining_quantity),
                    'order_count': 1
                })
            
            asks = []
            for order in sell_orders:
                asks.append({
                    'price': float(order.price or 0),
                    'quantity': float(order.remaining_quantity),
                    'order_count': 1
                })
            
            return {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting order book summary: {str(e)}")
            return {'symbol': symbol, 'bids': [], 'asks': []}
    
    def get_trading_statistics(self, user: User = None) -> Dict[str, Any]:
        """Get trading statistics"""
        try:
            queryset = Order.objects.all()
            if user:
                queryset = queryset.filter(user=user)
            
            total_orders = queryset.count()
            filled_orders = queryset.filter(status='filled').count()
            cancelled_orders = queryset.filter(status='cancelled').count()
            
            # Calculate fill rate
            fill_rate = (filled_orders / total_orders * 100) if total_orders > 0 else 0
            
            stats = {
                'total_orders': total_orders,
                'filled_orders': filled_orders,
                'cancelled_orders': cancelled_orders,
                'fill_rate_percent': round(fill_rate, 2)
            }
            
            if user:
                stats['user_id'] = user.id
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting trading statistics: {str(e)}")
            return {}
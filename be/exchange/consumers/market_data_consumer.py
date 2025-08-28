"""
WebSocket consumer for real-time market data
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from authentication.services.jwt_token_service import JWTTokenService
from exchange.models import (
    WebSocketConnection, ConnectionEvent, SymbolSubscription,
    MarketDataSnapshot, Order
)
from exchange.services.market_data_service import MarketDataService
from exchange.services.order_service import OrderService

logger = logging.getLogger(__name__)


class MarketDataConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for market data streaming"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: Optional[User] = None
        self.connection: Optional[WebSocketConnection] = None
        self.subscribed_symbols: set = set()
        self.market_data_service = MarketDataService()
        self.order_service = OrderService()
        self.jwt_service = JWTTokenService()
        self.max_subscriptions = settings.EXCHANGE_SETTINGS.get('MAX_SUBSCRIPTIONS_PER_USER', 50)
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Accept the connection
            await self.accept()
            
            # Create connection record
            self.connection = await self.create_connection_record()
            await self.log_event('connect', {'channel': self.channel_name})
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected successfully. Please authenticate.',
                'max_subscriptions': self.max_subscriptions
            }))
            
            logger.info(f"WebSocket connected: {self.channel_name}")
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if self.connection:
                await self.cleanup_connection()
                await self.log_event('disconnect', {'close_code': close_code})
            
            logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
            
        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            await self.log_event('message_received', {'type': message_type, 'data': data})
            
            # Route message based on type
            handlers = {
                'auth': self.handle_auth,
                'subscribe': self.handle_subscribe,
                'unsubscribe': self.handle_unsubscribe,
                'place_order': self.handle_place_order,
                'ping': self.handle_ping,
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")
            await self.send_error("Internal server error")
    
    async def handle_auth(self, data: Dict[str, Any]):
        """Handle authentication message"""
        try:
            token = data.get('token')
            if not token:
                await self.send_error("Token required for authentication")
                return
            
            # Validate JWT token
            user = await self.authenticate_user(token)
            if not user:
                await self.send_error("Invalid token")
                return
            
            self.user = user
            await self.update_connection_auth(user)
            await self.log_event('authenticate', {'user_id': user.id})
            
            # Load existing subscriptions
            await self.load_existing_subscriptions()
            
            await self.send(text_data=json.dumps({
                'type': 'auth_success',
                'user_id': user.id,
                'message': 'Authenticated successfully'
            }))
            
            logger.info(f"User authenticated: {user.username} ({self.channel_name})")
            
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            await self.send_error("Authentication failed")
    
    async def handle_subscribe(self, data: Dict[str, Any]):
        """Handle symbol subscription"""
        if not self.user:
            await self.send_error("Authentication required")
            return
        
        try:
            symbols = data.get('symbols', [])
            if not symbols:
                await self.send_error("No symbols provided")
                return
            
            # Check subscription limit
            total_subscriptions = len(self.subscribed_symbols) + len(symbols)
            if total_subscriptions > self.max_subscriptions:
                await self.send_error(f"Subscription limit exceeded ({self.max_subscriptions})")
                return
            
            # Subscribe to symbols
            subscribed_symbols = []
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    await self.subscribe_to_symbol(symbol)
                    subscribed_symbols.append(symbol)
            
            if subscribed_symbols:
                await self.log_event('subscribe', {'symbols': subscribed_symbols})
                
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'symbols': subscribed_symbols,
                    'count': len(subscribed_symbols)
                }))
            
        except Exception as e:
            logger.error(f"Subscribe error: {str(e)}")
            await self.send_error("Subscription failed")
    
    async def handle_unsubscribe(self, data: Dict[str, Any]):
        """Handle symbol unsubscription"""
        if not self.user:
            await self.send_error("Authentication required")
            return
        
        try:
            symbols = data.get('symbols', [])
            if not symbols:
                await self.send_error("No symbols provided")
                return
            
            # Unsubscribe from symbols
            unsubscribed_symbols = []
            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    await self.unsubscribe_from_symbol(symbol)
                    unsubscribed_symbols.append(symbol)
            
            if unsubscribed_symbols:
                await self.log_event('unsubscribe', {'symbols': unsubscribed_symbols})
                
                await self.send(text_data=json.dumps({
                    'type': 'unsubscribed',
                    'symbols': unsubscribed_symbols
                }))
            
        except Exception as e:
            logger.error(f"Unsubscribe error: {str(e)}")
            await self.send_error("Unsubscription failed")
    
    async def handle_place_order(self, data: Dict[str, Any]):
        """Handle order placement"""
        if not self.user:
            await self.send_error("Authentication required")
            return
        
        try:
            order_data = {
                'symbol': data.get('symbol'),
                'side': data.get('side'),
                'quantity': data.get('quantity'),
                'order_type': data.get('order_type', 'market'),
                'price': data.get('price'),
            }
            
            # Validate required fields
            if not all([order_data['symbol'], order_data['side'], order_data['quantity']]):
                await self.send_error("Missing required order fields")
                return
            
            # Place order
            order = await self.place_order(order_data)
            if order:
                await self.log_event('place_order', {'order_id': order.order_id})
                
                # Send confirmation
                await self.send(text_data=json.dumps({
                    'type': 'order_placed',
                    'order_id': order.order_id,
                    'status': order.status,
                    'message': 'Order placed successfully'
                }))
            
        except Exception as e:
            logger.error(f"Order placement error: {str(e)}")
            await self.send_error("Order placement failed")
    
    async def handle_ping(self, data: Dict[str, Any]):
        """Handle ping message"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_price_update(self, symbol: str, price_data: Dict[str, Any]):
        """Send price update to client"""
        if symbol in self.subscribed_symbols:
            try:
                await self.send(text_data=json.dumps(price_data))
                await self.log_event('message_sent', {'type': 'price_update', 'symbol': symbol})
            except Exception as e:
                logger.error(f"Failed to send price update: {str(e)}")
    
    async def send_market_alert(self, alert_data: Dict[str, Any]):
        """Send market alert to client"""
        try:
            await self.send(text_data=json.dumps(alert_data))
            await self.log_event('message_sent', {'type': 'market_alert'})
        except Exception as e:
            logger.error(f"Failed to send market alert: {str(e)}")
    
    async def send_order_update(self, order_data: Dict[str, Any]):
        """Send order execution update to client"""
        try:
            await self.send(text_data=json.dumps(order_data))
            await self.log_event('message_sent', {'type': 'order_update'})
        except Exception as e:
            logger.error(f"Failed to send order update: {str(e)}")
    
    async def send_error(self, message: str, code: str = 'error'):
        """Send error message to client"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': code,
                'message': message
            }))
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")
    
    # Database operations
    @database_sync_to_async
    def create_connection_record(self) -> WebSocketConnection:
        """Create connection record in database"""
        return WebSocketConnection.objects.create(
            channel_name=self.channel_name,
            status='connected',
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent()
        )
    
    @database_sync_to_async
    def update_connection_auth(self, user: User):
        """Update connection with authenticated user"""
        self.connection.authenticate(user)
    
    @database_sync_to_async
    def cleanup_connection(self):
        """Clean up connection and subscriptions"""
        if self.connection:
            self.connection.disconnect()
            
            # Deactivate subscriptions
            SymbolSubscription.objects.filter(
                user=self.connection.user,
                is_active=True
            ).update(is_active=False)
    
    @database_sync_to_async
    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log connection event"""
        if self.connection:
            ConnectionEvent.objects.create(
                connection=self.connection,
                event_type=event_type,
                event_data=event_data
            )
    
    @database_sync_to_async
    def authenticate_user(self, token: str) -> Optional[User]:
        """Authenticate user with JWT token"""
        try:
            return self.jwt_service.get_user_from_token(token)
        except Exception:
            return None
    
    @database_sync_to_async
    def subscribe_to_symbol(self, symbol: str):
        """Subscribe user to symbol"""
        subscription, created = SymbolSubscription.objects.get_or_create(
            user=self.user,
            symbol=symbol.upper(),
            defaults={'is_active': True}
        )
        if not created:
            subscription.activate()
        
        self.subscribed_symbols.add(symbol.upper())
        self.connection.increment_subscriptions()
    
    @database_sync_to_async
    def unsubscribe_from_symbol(self, symbol: str):
        """Unsubscribe user from symbol"""
        try:
            subscription = SymbolSubscription.objects.get(
                user=self.user,
                symbol=symbol.upper(),
                is_active=True
            )
            subscription.deactivate()
            self.subscribed_symbols.discard(symbol.upper())
            self.connection.decrement_subscriptions()
        except SymbolSubscription.DoesNotExist:
            pass
    
    @database_sync_to_async
    def load_existing_subscriptions(self):
        """Load user's existing active subscriptions"""
        subscriptions = SymbolSubscription.objects.filter(
            user=self.user,
            is_active=True
        ).values_list('symbol', flat=True)
        
        self.subscribed_symbols = set(subscriptions)
        
        if subscriptions:
            self.connection.subscription_count = len(subscriptions)
            self.connection.save()
    
    @database_sync_to_async
    def place_order(self, order_data: Dict[str, Any]) -> Optional[Order]:
        """Place order through order service"""
        try:
            return self.order_service.place_order(self.user, order_data)
        except Exception:
            return None
    
    def get_client_ip(self) -> Optional[str]:
        """Get client IP address from headers"""
        try:
            headers = dict(self.scope.get('headers', []))
            x_forwarded_for = headers.get(b'x-forwarded-for')
            if x_forwarded_for:
                return x_forwarded_for.decode().split(',')[0].strip()
            return self.scope.get('client')[0] if self.scope.get('client') else None
        except Exception:
            return None
    
    def get_user_agent(self) -> Optional[str]:
        """Get client user agent from headers"""
        try:
            headers = dict(self.scope.get('headers', []))
            user_agent = headers.get(b'user-agent')
            return user_agent.decode() if user_agent else None
        except Exception:
            return None
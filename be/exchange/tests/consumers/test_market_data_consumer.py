"""
Tests for MarketDataConsumer
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User

from exchange.consumers import MarketDataConsumer
from exchange.tests.factories import UserFactory, SymbolSubscriptionFactory


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestMarketDataConsumer:
    """Test MarketDataConsumer WebSocket functionality"""
    
    def setup_method(self):
        """Set up test data"""
        self.user = UserFactory()
        
    async def test_websocket_connect(self):
        """Test WebSocket connection"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        
        connected, subprotocol = await communicator.connect()
        
        assert connected
        
        # Should receive connection established message
        message = await communicator.receive_json_from()
        assert message['type'] == 'connection_established'
        assert 'max_subscriptions' in message
        
        await communicator.disconnect()
    
    async def test_websocket_authentication_success(self):
        """Test successful WebSocket authentication"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock JWT authentication
        with patch('exchange.consumers.market_data_consumer.JWTTokenService') as mock_jwt:
            mock_jwt_instance = Mock()
            mock_jwt_instance.get_user_from_token.return_value = self.user
            mock_jwt.return_value = mock_jwt_instance
            
            # Send authentication message
            await communicator.send_json_to({
                'type': 'auth',
                'token': 'valid_jwt_token'
            })
            
            # Should receive auth success message
            message = await communicator.receive_json_from()
            assert message['type'] == 'auth_success'
            assert message['user_id'] == self.user.id
        
        await communicator.disconnect()
    
    async def test_websocket_authentication_failure(self):
        """Test failed WebSocket authentication"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock JWT authentication failure
        with patch('exchange.consumers.market_data_consumer.JWTTokenService') as mock_jwt:
            mock_jwt_instance = Mock()
            mock_jwt_instance.get_user_from_token.return_value = None
            mock_jwt.return_value = mock_jwt_instance
            
            # Send authentication message with invalid token
            await communicator.send_json_to({
                'type': 'auth',
                'token': 'invalid_jwt_token'
            })
            
            # Should receive error message
            message = await communicator.receive_json_from()
            assert message['type'] == 'error'
            assert 'Invalid token' in message['message']
        
        await communicator.disconnect()
    
    async def test_websocket_subscribe_without_auth(self):
        """Test subscribing without authentication"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Try to subscribe without authentication
        await communicator.send_json_to({
            'type': 'subscribe',
            'symbols': ['AAPL']
        })
        
        # Should receive error message
        message = await communicator.receive_json_from()
        assert message['type'] == 'error'
        assert 'Authentication required' in message['message']
        
        await communicator.disconnect()
    
    async def test_websocket_subscribe_success(self):
        """Test successful symbol subscription"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock authentication
        consumer = communicator.application
        consumer.user = self.user
        
        # Send subscription message
        await communicator.send_json_to({
            'type': 'subscribe',
            'symbols': ['AAPL', 'GOOGL']
        })
        
        # Should receive subscribed confirmation
        message = await communicator.receive_json_from()
        assert message['type'] == 'subscribed'
        assert set(message['symbols']) == {'AAPL', 'GOOGL'}
        assert message['count'] == 2
        
        await communicator.disconnect()
    
    async def test_websocket_subscribe_no_symbols(self):
        """Test subscribing with no symbols"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock authentication
        consumer = communicator.application
        consumer.user = self.user
        
        # Send subscription message with no symbols
        await communicator.send_json_to({
            'type': 'subscribe',
            'symbols': []
        })
        
        # Should receive error message
        message = await communicator.receive_json_from()
        assert message['type'] == 'error'
        assert 'No symbols provided' in message['message']
        
        await communicator.disconnect()
    
    async def test_websocket_unsubscribe(self):
        """Test symbol unsubscription"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock authentication and existing subscriptions
        consumer = communicator.application
        consumer.user = self.user
        consumer.subscribed_symbols = {'AAPL', 'GOOGL', 'MSFT'}
        
        # Send unsubscribe message
        await communicator.send_json_to({
            'type': 'unsubscribe',
            'symbols': ['GOOGL', 'MSFT']
        })
        
        # Should receive unsubscribed confirmation
        message = await communicator.receive_json_from()
        assert message['type'] == 'unsubscribed'
        assert set(message['symbols']) == {'GOOGL', 'MSFT'}
        
        await communicator.disconnect()
    
    async def test_websocket_place_order(self):
        """Test order placement via WebSocket"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock authentication
        consumer = communicator.application
        consumer.user = self.user
        
        # Mock order service
        with patch('exchange.consumers.market_data_consumer.OrderService') as mock_order_service:
            mock_order = Mock()
            mock_order.order_id = 'ord_123456789'
            mock_order.status = 'submitted'
            
            mock_service = Mock()
            mock_service.place_order.return_value = mock_order
            mock_order_service.return_value = mock_service
            
            # Send place order message
            await communicator.send_json_to({
                'type': 'place_order',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 100,
                'order_type': 'market'
            })
            
            # Should receive order placed confirmation
            message = await communicator.receive_json_from()
            assert message['type'] == 'order_placed'
            assert message['order_id'] == 'ord_123456789'
            assert message['status'] == 'submitted'
        
        await communicator.disconnect()
    
    async def test_websocket_ping_pong(self):
        """Test ping-pong mechanism"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Send ping message
        await communicator.send_json_to({
            'type': 'ping'
        })
        
        # Should receive pong response
        message = await communicator.receive_json_from()
        assert message['type'] == 'pong'
        assert 'timestamp' in message
        
        await communicator.disconnect()
    
    async def test_websocket_invalid_message_type(self):
        """Test handling of invalid message types"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Send message with invalid type
        await communicator.send_json_to({
            'type': 'invalid_type'
        })
        
        # Should receive error message
        message = await communicator.receive_json_from()
        assert message['type'] == 'error'
        assert 'Unknown message type' in message['message']
        
        await communicator.disconnect()
    
    async def test_websocket_invalid_json(self):
        """Test handling of invalid JSON"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Send invalid JSON
        await communicator.send_text_to("invalid json {")
        
        # Should receive error message
        message = await communicator.receive_json_from()
        assert message['type'] == 'error'
        assert 'Invalid JSON format' in message['message']
        
        await communicator.disconnect()
    
    async def test_websocket_disconnect_cleanup(self):
        """Test cleanup on disconnect"""
        communicator = WebsocketCommunicator(MarketDataConsumer.as_asgi(), "/ws/market-data/")
        await communicator.connect()
        
        # Mock consumer state
        consumer = communicator.application
        consumer.user = self.user
        consumer.connection = Mock()
        consumer.connection.disconnect = Mock()
        
        # Disconnect
        await communicator.disconnect()
        
        # Verify cleanup was called
        consumer.connection.disconnect.assert_called_once()
    
    async def test_send_price_update(self):
        """Test sending price update to client"""
        consumer = MarketDataConsumer()
        consumer.subscribed_symbols = {'AAPL'}
        consumer.send = AsyncMock()
        
        price_data = {
            'type': 'price_update',
            'symbol': 'AAPL',
            'price': 150.25
        }
        
        await consumer.send_price_update('AAPL', price_data)
        
        consumer.send.assert_called_once()
        args = consumer.send.call_args[1]
        assert 'text_data' in args
        
        sent_data = json.loads(args['text_data'])
        assert sent_data == price_data
    
    async def test_send_price_update_not_subscribed(self):
        """Test not sending price update for unsubscribed symbol"""
        consumer = MarketDataConsumer()
        consumer.subscribed_symbols = {'GOOGL'}  # Not subscribed to AAPL
        consumer.send = AsyncMock()
        
        price_data = {
            'type': 'price_update',
            'symbol': 'AAPL',
            'price': 150.25
        }
        
        await consumer.send_price_update('AAPL', price_data)
        
        consumer.send.assert_not_called()
    
    async def test_send_market_alert(self):
        """Test sending market alert to client"""
        consumer = MarketDataConsumer()
        consumer.send = AsyncMock()
        
        alert_data = {
            'type': 'market_alert',
            'symbol': 'AAPL',
            'severity': 'high',
            'title': 'Earnings Beat'
        }
        
        await consumer.send_market_alert(alert_data)
        
        consumer.send.assert_called_once()
        args = consumer.send.call_args[1]
        sent_data = json.loads(args['text_data'])
        assert sent_data == alert_data
    
    async def test_send_order_update(self):
        """Test sending order update to client"""
        consumer = MarketDataConsumer()
        consumer.send = AsyncMock()
        
        order_data = {
            'type': 'order_executed',
            'order_id': 'ord_123456789',
            'status': 'filled'
        }
        
        await consumer.send_order_update(order_data)
        
        consumer.send.assert_called_once()
        args = consumer.send.call_args[1]
        sent_data = json.loads(args['text_data'])
        assert sent_data == order_data
    
    def test_get_client_ip(self):
        """Test extracting client IP address"""
        consumer = MarketDataConsumer()
        
        # Test with X-Forwarded-For header
        consumer.scope = {
            'headers': [(b'x-forwarded-for', b'192.168.1.1, 10.0.0.1')]
        }
        
        ip = consumer.get_client_ip()
        assert ip == '192.168.1.1'
        
        # Test with client info
        consumer.scope = {
            'headers': [],
            'client': ('127.0.0.1', 8000)
        }
        
        ip = consumer.get_client_ip()
        assert ip == '127.0.0.1'
    
    def test_get_user_agent(self):
        """Test extracting user agent"""
        consumer = MarketDataConsumer()
        consumer.scope = {
            'headers': [(b'user-agent', b'Mozilla/5.0 (Test Browser)')]
        }
        
        user_agent = consumer.get_user_agent()
        assert user_agent == 'Mozilla/5.0 (Test Browser)'
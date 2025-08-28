"""
Redis pub/sub service for real-time market data distribution
"""

import asyncio
import json
import logging
import redis
from typing import Dict, Any, Callable, Optional
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.models import User

from exchange.models import WebSocketConnection, SymbolSubscription

logger = logging.getLogger(__name__)


class RedisPubSubService:
    """Service for managing Redis pub/sub for market data distribution"""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.channel_layer = get_channel_layer()
        self.channels = {
            'price_updates': 'market_data:price_updates',
            'market_events': 'market_data:events',
            'order_updates': 'market_data:orders'
        }
        self.is_listening = False
        self.subscribers = {}  # Channel name -> callback mapping
        
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance"""
        config = settings.REDIS_CONFIG
        return redis.Redis(
            host=config['HOST'],
            port=config['PORT'],
            db=config['DB'],
            decode_responses=True
        )
    
    async def start_listening(self):
        """Start listening to Redis channels"""
        if self.is_listening:
            logger.warning("Redis pub/sub service is already listening")
            return
        
        self.is_listening = True
        logger.info("Starting Redis pub/sub listener...")
        
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(
                self.channels['price_updates'],
                self.channels['market_events'],
                self.channels['order_updates']
            )
            
            # Start listening for messages
            async for message in pubsub.listen():
                if not self.is_listening:
                    break
                    
                if message['type'] == 'message':
                    await self._handle_redis_message(message)
                    
        except Exception as e:
            logger.error(f"Error in Redis pub/sub listener: {str(e)}")
        finally:
            self.is_listening = False
            logger.info("Redis pub/sub listener stopped")
    
    async def stop_listening(self):
        """Stop listening to Redis channels"""
        self.is_listening = False
        logger.info("Stopping Redis pub/sub listener...")
    
    async def _handle_redis_message(self, message: Dict[str, Any]):
        """Handle incoming Redis message"""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            action = data.get('action')
            
            if channel == self.channels['price_updates']:
                await self._handle_price_update(data)
            elif channel == self.channels['market_events']:
                await self._handle_market_event(data)
            elif channel == self.channels['order_updates']:
                await self._handle_order_update(data)
            else:
                logger.warning(f"Unknown channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error handling Redis message: {str(e)}")
    
    async def _handle_price_update(self, data: Dict[str, Any]):
        """Handle price update message"""
        try:
            price_data = data.get('data', {})
            symbol = price_data.get('symbol')
            
            if not symbol:
                return
            
            # Get users subscribed to this symbol
            subscribed_users = await self._get_subscribed_users(symbol)
            
            if not subscribed_users:
                return
            
            # Send to all subscribed WebSocket connections
            for user_id in subscribed_users:
                connections = await self._get_user_connections(user_id)
                for connection in connections:
                    await self._send_to_websocket(
                        connection.channel_name,
                        'send_price_update',
                        {
                            'symbol': symbol,
                            'price_data': price_data
                        }
                    )
            
            logger.debug(f"Sent price update for {symbol} to {len(subscribed_users)} users")
            
        except Exception as e:
            logger.error(f"Error handling price update: {str(e)}")
    
    async def _handle_market_event(self, data: Dict[str, Any]):
        """Handle market event message"""
        try:
            event_data = data.get('data', {})
            symbol = event_data.get('symbol')
            
            if not symbol:
                return
            
            # Get users subscribed to this symbol
            subscribed_users = await self._get_subscribed_users(symbol)
            
            # Send to all subscribed WebSocket connections
            for user_id in subscribed_users:
                connections = await self._get_user_connections(user_id)
                for connection in connections:
                    await self._send_to_websocket(
                        connection.channel_name,
                        'send_market_alert',
                        {'alert_data': event_data}
                    )
            
            logger.info(f"Sent market event for {symbol} to {len(subscribed_users)} users")
            
        except Exception as e:
            logger.error(f"Error handling market event: {str(e)}")
    
    async def _handle_order_update(self, data: Dict[str, Any]):
        """Handle order update message"""
        try:
            action = data.get('action')
            user_id = data.get('user_id')
            order_data = data.get('data', {})
            
            if not user_id:
                return
            
            # Send to user's WebSocket connections
            connections = await self._get_user_connections(user_id)
            for connection in connections:
                if action == 'order_update':
                    await self._send_to_websocket(
                        connection.channel_name,
                        'send_order_update',
                        {'order_data': order_data}
                    )
            
            logger.debug(f"Sent order update to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling order update: {str(e)}")
    
    async def _send_to_websocket(
        self,
        channel_name: str,
        method: str,
        data: Dict[str, Any]
    ):
        """Send message to WebSocket consumer"""
        try:
            await self.channel_layer.send(channel_name, {
                'type': method,
                **data
            })
        except Exception as e:
            logger.error(f"Error sending to WebSocket {channel_name}: {str(e)}")
    
    # Database operations (async wrappers)
    async def _get_subscribed_users(self, symbol: str) -> list:
        """Get list of user IDs subscribed to symbol"""
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_users():
            return list(SymbolSubscription.objects.filter(
                symbol=symbol.upper(),
                is_active=True
            ).values_list('user_id', flat=True))
        
        return await get_users()
    
    async def _get_user_connections(self, user_id: int) -> list:
        """Get active WebSocket connections for user"""
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_connections():
            return list(WebSocketConnection.objects.filter(
                user_id=user_id,
                status='authenticated'
            ))
        
        return await get_connections()
    
    # Publishing methods
    def publish_price_update(self, price_data: Dict[str, Any]):
        """Publish price update to Redis"""
        try:
            message = {
                'action': 'price_update',
                'data': price_data
            }
            
            self.redis_client.publish(
                self.channels['price_updates'],
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error publishing price update: {str(e)}")
    
    def publish_market_event(self, event_data: Dict[str, Any]):
        """Publish market event to Redis"""
        try:
            message = {
                'action': 'market_event',
                'data': event_data
            }
            
            self.redis_client.publish(
                self.channels['market_events'],
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error publishing market event: {str(e)}")
    
    def publish_order_update(self, user_id: int, order_data: Dict[str, Any]):
        """Publish order update to Redis"""
        try:
            message = {
                'action': 'order_update',
                'user_id': user_id,
                'data': order_data
            }
            
            self.redis_client.publish(
                self.channels['order_updates'],
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error publishing order update: {str(e)}")
    
    # Utility methods
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get Redis channel statistics"""
        try:
            stats = {}
            for name, channel in self.channels.items():
                # Get number of subscribers (Redis PUBSUB NUMSUB command)
                result = self.redis_client.execute_command('PUBSUB', 'NUMSUB', channel)
                subscriber_count = result[1] if len(result) > 1 else 0
                stats[name] = {
                    'channel': channel,
                    'subscribers': subscriber_count
                }
            
            return {
                'is_listening': self.is_listening,
                'channels': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting channel stats: {str(e)}")
            return {'is_listening': self.is_listening, 'channels': {}}
    
    def clear_redis_data(self):
        """Clear all Redis data (for testing)"""
        try:
            # Get all keys matching our patterns
            patterns = [
                'market_data:*',
                'user_subscriptions:*',
                'websocket_connections:*'
            ]
            
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            logger.info("Cleared Redis data")
            
        except Exception as e:
            logger.error(f"Error clearing Redis data: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection"""
        try:
            # Test Redis connection
            start_time = asyncio.get_event_loop().time()
            self.redis_client.ping()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'is_listening': self.is_listening
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'is_listening': self.is_listening
            }
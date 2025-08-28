"""
Market data service for exchange integration
"""

import redis
import json
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from exchange.models import MarketDataSnapshot, SymbolSubscription, MarketEvent

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for managing market data operations"""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.price_channel = "market_data:price_updates"
        self.event_channel = "market_data:events"
        
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance"""
        config = settings.REDIS_CONFIG
        return redis.Redis(
            host=config['HOST'],
            port=config['PORT'],
            db=config['DB'],
            decode_responses=True
        )
    
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price for a symbol"""
        try:
            latest_data = MarketDataSnapshot.objects.filter(
                symbol=symbol.upper()
            ).first()
            
            if latest_data:
                return latest_data.price
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    def get_latest_market_data(self, symbol: str) -> Optional[MarketDataSnapshot]:
        """Get latest market data snapshot for symbol"""
        try:
            return MarketDataSnapshot.objects.filter(
                symbol=symbol.upper()
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return None
    
    def get_market_data_history(
        self, 
        symbol: str, 
        hours: int = 24
    ) -> List[MarketDataSnapshot]:
        """Get market data history for symbol"""
        try:
            cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
            
            return list(MarketDataSnapshot.objects.filter(
                symbol=symbol.upper(),
                timestamp__gte=cutoff_time
            ).order_by('-timestamp'))
            
        except Exception as e:
            logger.error(f"Error getting market data history for {symbol}: {str(e)}")
            return []
    
    def store_market_data(self, market_data: Dict[str, Any]) -> MarketDataSnapshot:
        """Store market data snapshot"""
        try:
            snapshot = MarketDataSnapshot.objects.create(
                symbol=market_data['symbol'].upper(),
                price=Decimal(str(market_data['price'])),
                change=Decimal(str(market_data.get('change', 0))),
                change_percent=Decimal(str(market_data.get('change_percent', 0))),
                volume=market_data.get('volume', 0),
                bid=Decimal(str(market_data.get('bid', market_data['price']))),
                ask=Decimal(str(market_data.get('ask', market_data['price']))),
                timestamp=timezone.now(),
                exchange=market_data.get('exchange', 'SIMULATOR')
            )
            
            # Publish to Redis for real-time distribution
            self.publish_price_update(snapshot)
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            raise
    
    def publish_price_update(self, snapshot: MarketDataSnapshot) -> None:
        """Publish price update to Redis channel"""
        try:
            message = {
                'action': 'price_update',
                'data': snapshot.to_websocket_message()
            }
            
            self.redis_client.publish(
                self.price_channel,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error publishing price update: {str(e)}")
    
    def publish_market_event(self, event: MarketEvent) -> None:
        """Publish market event to Redis channel"""
        try:
            message = {
                'action': 'market_event',
                'data': event.to_websocket_message()
            }
            
            self.redis_client.publish(
                self.event_channel,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error publishing market event: {str(e)}")
    
    def get_subscribed_users(self, symbol: str) -> List[int]:
        """Get list of user IDs subscribed to symbol"""
        try:
            user_ids = SymbolSubscription.objects.filter(
                symbol=symbol.upper(),
                is_active=True
            ).values_list('user_id', flat=True)
            
            return list(user_ids)
            
        except Exception as e:
            logger.error(f"Error getting subscribed users for {symbol}: {str(e)}")
            return []
    
    def get_user_subscriptions(self, user: User) -> List[str]:
        """Get list of symbols user is subscribed to"""
        try:
            symbols = SymbolSubscription.objects.filter(
                user=user,
                is_active=True
            ).values_list('symbol', flat=True)
            
            return list(symbols)
            
        except Exception as e:
            logger.error(f"Error getting user subscriptions: {str(e)}")
            return []
    
    def create_subscription(self, user: User, symbol: str) -> SymbolSubscription:
        """Create or activate symbol subscription"""
        try:
            subscription, created = SymbolSubscription.objects.get_or_create(
                user=user,
                symbol=symbol.upper(),
                defaults={'is_active': True}
            )
            
            if not created and not subscription.is_active:
                subscription.activate()
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    def remove_subscription(self, user: User, symbol: str) -> bool:
        """Remove/deactivate symbol subscription"""
        try:
            subscription = SymbolSubscription.objects.get(
                user=user,
                symbol=symbol.upper(),
                is_active=True
            )
            subscription.deactivate()
            return True
            
        except SymbolSubscription.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error removing subscription: {str(e)}")
            return False
    
    def cleanup_old_data(self, hours: int = None) -> int:
        """Clean up old market data snapshots"""
        try:
            if hours is None:
                hours = settings.EXCHANGE_SETTINGS.get('MARKET_DATA_RETENTION_HOURS', 24)
            
            cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
            
            deleted_count, _ = MarketDataSnapshot.objects.filter(
                timestamp__lt=cutoff_time
            ).delete()
            
            logger.info(f"Cleaned up {deleted_count} old market data records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            return 0
    
    def get_market_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get market statistics for symbol"""
        try:
            # Get data from last 24 hours
            history = self.get_market_data_history(symbol, hours=24)
            
            if not history:
                return {}
            
            prices = [float(snapshot.price) for snapshot in history]
            volumes = [snapshot.volume for snapshot in history]
            
            stats = {
                'symbol': symbol.upper(),
                'current_price': float(history[0].price),
                'high_24h': max(prices),
                'low_24h': min(prices),
                'volume_24h': sum(volumes),
                'price_change_24h': float(history[0].change),
                'price_change_percent_24h': float(history[0].change_percent),
                'data_points': len(history),
                'last_updated': history[0].timestamp.isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting market statistics: {str(e)}")
            return {}
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is supported"""
        # For now, accept any symbol format
        # In production, this would check against supported symbols
        if not symbol or len(symbol) > 10:
            return False
        
        # Basic validation for symbol format
        return symbol.replace('-', '').replace('.', '').isalnum()
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols"""
        # For the simulator, return a predefined list
        return [
            'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN',
            'SPY', 'QQQ', 'VTI', 'VOO',
            'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD'
        ]
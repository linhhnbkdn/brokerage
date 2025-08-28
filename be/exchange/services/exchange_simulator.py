"""
Exchange simulator service for generating dummy market data and executing orders
"""

import random
import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

from exchange.models import MarketDataSnapshot, Order, MarketEvent
from exchange.services.market_data_service import MarketDataService
from exchange.services.order_service import OrderService

logger = logging.getLogger(__name__)


class ExchangeSimulator:
    """Simulates exchange functionality with dummy data"""
    
    def __init__(self):
        self.market_data_service = MarketDataService()
        self.order_service = OrderService()
        self.is_running = False
        self.symbols = self._get_supported_symbols()
        self.price_data = self._initialize_price_data()
        self.update_interval = settings.EXCHANGE_SETTINGS.get('PRICE_UPDATE_INTERVAL', 2)
        
    def _get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols for simulation"""
        return [
            'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NFLX',
            'SPY', 'QQQ', 'VTI', 'VOO', 'IWM',
            'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'SOL-USD'
        ]
    
    def _initialize_price_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize price data for all symbols"""
        base_prices = {
            'AAPL': 150.00, 'GOOGL': 2800.00, 'MSFT': 380.00,
            'TSLA': 250.00, 'AMZN': 3400.00, 'META': 320.00,
            'NFLX': 450.00, 'SPY': 450.00, 'QQQ': 380.00,
            'VTI': 240.00, 'VOO': 420.00, 'IWM': 200.00,
            'BTC-USD': 45000.00, 'ETH-USD': 3200.00, 'ADA-USD': 0.85,
            'DOT-USD': 25.00, 'SOL-USD': 180.00
        }
        
        price_data = {}
        for symbol in self.symbols:
            base_price = base_prices.get(symbol, 100.00)
            price_data[symbol] = {
                'current_price': Decimal(str(base_price)),
                'previous_close': Decimal(str(base_price)),
                'daily_high': Decimal(str(base_price * 1.02)),
                'daily_low': Decimal(str(base_price * 0.98)),
                'volume': random.randint(100000, 5000000),
                'volatility': random.uniform(0.01, 0.05),  # Daily volatility
                'trend': random.choice([-1, 0, 1])  # -1: down, 0: sideways, 1: up
            }
        
        return price_data
    
    async def start_simulation(self):
        """Start the exchange simulation"""
        if self.is_running:
            logger.warning("Exchange simulator is already running")
            return
        
        self.is_running = True
        logger.info("Starting exchange simulator...")
        
        # Start concurrent tasks
        await asyncio.gather(
            self._price_generation_loop(),
            self._order_processing_loop(),
            self._market_events_loop(),
            return_exceptions=True
        )
    
    async def stop_simulation(self):
        """Stop the exchange simulation"""
        self.is_running = False
        logger.info("Exchange simulator stopped")
    
    async def _price_generation_loop(self):
        """Main loop for generating price updates"""
        logger.info("Starting price generation loop")
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    # Generate new price
                    new_price_data = self._generate_price_update(symbol)
                    
                    # Store in database
                    await self._store_market_data_async(symbol, new_price_data)
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in price generation loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _order_processing_loop(self):
        """Process pending orders"""
        logger.info("Starting order processing loop")
        
        while self.is_running:
            try:
                await self._process_pending_orders()
                await asyncio.sleep(1)  # Check orders more frequently
                
            except Exception as e:
                logger.error(f"Error in order processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _market_events_loop(self):
        """Generate random market events"""
        logger.info("Starting market events loop")
        
        while self.is_running:
            try:
                # Generate events less frequently
                if random.random() < 0.1:  # 10% chance every interval
                    await self._generate_market_event()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in market events loop: {str(e)}")
                await asyncio.sleep(1)
    
    def _generate_price_update(self, symbol: str) -> Dict[str, Any]:
        """Generate realistic price update for symbol"""
        try:
            price_info = self.price_data[symbol]
            current_price = price_info['current_price']
            volatility = price_info['volatility']
            trend = price_info['trend']
            
            # Generate price change using random walk with trend
            base_change = random.normalvariate(0, float(current_price) * volatility)
            trend_factor = trend * float(current_price) * 0.001  # Small trend influence
            price_change = base_change + trend_factor
            
            # Calculate new price
            new_price = current_price + Decimal(str(price_change))
            new_price = max(new_price, current_price * Decimal('0.01'))  # Minimum price check
            
            # Update price data
            price_info['current_price'] = new_price
            price_info['daily_high'] = max(price_info['daily_high'], new_price)
            price_info['daily_low'] = min(price_info['daily_low'], new_price)
            
            # Calculate changes
            change = new_price - price_info['previous_close']
            change_percent = (change / price_info['previous_close']) * 100 if price_info['previous_close'] else Decimal('0')
            
            # Generate bid/ask spread
            spread_percent = Decimal(str(random.uniform(0.001, 0.01)))  # 0.1% to 1% spread
            spread = new_price * spread_percent
            bid = new_price - (spread / 2)
            ask = new_price + (spread / 2)
            
            # Update volume (simulate trading activity)
            volume_change = random.randint(-50000, 100000)
            price_info['volume'] = max(10000, price_info['volume'] + volume_change)
            
            # Occasionally change trend
            if random.random() < 0.05:  # 5% chance
                price_info['trend'] = random.choice([-1, 0, 1])
            
            return {
                'symbol': symbol,
                'price': float(new_price),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': price_info['volume'],
                'bid': float(bid),
                'ask': float(ask),
                'high': float(price_info['daily_high']),
                'low': float(price_info['daily_low'])
            }
            
        except Exception as e:
            logger.error(f"Error generating price update for {symbol}: {str(e)}")
            return {}
    
    async def _store_market_data_async(self, symbol: str, price_data: Dict[str, Any]):
        """Store market data asynchronously"""
        try:
            # Use database_sync_to_async for database operations
            from channels.db import database_sync_to_async
            
            @database_sync_to_async
            def store_data():
                return self.market_data_service.store_market_data(price_data)
            
            await store_data()
            
        except Exception as e:
            logger.error(f"Error storing market data for {symbol}: {str(e)}")
    
    async def _process_pending_orders(self):
        """Process pending market and limit orders"""
        try:
            from channels.db import database_sync_to_async
            
            @database_sync_to_async
            def get_pending_orders():
                return list(Order.objects.filter(
                    status__in=['submitted', 'partial']
                ).select_related('user'))
            
            pending_orders = await get_pending_orders()
            
            for order in pending_orders:
                try:
                    if order.order_type == 'market':
                        await self._execute_market_order(order)
                    elif order.order_type == 'limit':
                        await self._check_limit_order(order)
                        
                except Exception as e:
                    logger.error(f"Error processing order {order.order_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error processing pending orders: {str(e)}")
    
    async def _execute_market_order(self, order: Order):
        """Execute market order immediately"""
        try:
            from channels.db import database_sync_to_async
            
            @database_sync_to_async
            def execute_order():
                return self.order_service.simulate_market_order_execution(order)
            
            await execute_order()
            
        except Exception as e:
            logger.error(f"Error executing market order {order.order_id}: {str(e)}")
    
    async def _check_limit_order(self, order: Order):
        """Check if limit order should be executed"""
        try:
            current_price = self.price_data[order.symbol]['current_price']
            
            should_execute = False
            if order.side == 'buy' and current_price <= order.price:
                should_execute = True
            elif order.side == 'sell' and current_price >= order.price:
                should_execute = True
            
            if should_execute:
                from channels.db import database_sync_to_async
                
                @database_sync_to_async
                def execute_limit_order():
                    execution_data = {
                        'quantity': order.remaining_quantity,
                        'price': order.price,
                        'commission': min(
                            Decimal('9.99'),
                            order.remaining_quantity * order.price * Decimal('0.001')
                        )
                    }
                    return self.order_service.execute_order(order, execution_data)
                
                await execute_limit_order()
                
        except Exception as e:
            logger.error(f"Error checking limit order {order.order_id}: {str(e)}")
    
    async def _generate_market_event(self):
        """Generate random market event"""
        try:
            symbol = random.choice(self.symbols)
            event_types = [
                'earnings_beat', 'earnings_miss', 'dividend_announcement',
                'market_news', 'technical_alert'
            ]
            impacts = ['low', 'medium', 'high']
            
            event_type = random.choice(event_types)
            impact = random.choice(impacts)
            
            # Generate event content
            event_content = self._generate_event_content(symbol, event_type, impact)
            
            from channels.db import database_sync_to_async
            
            @database_sync_to_async
            def create_event():
                return MarketEvent.objects.create(
                    symbol=symbol,
                    event_type=event_type,
                    impact=impact,
                    title=event_content['title'],
                    description=event_content['description']
                )
            
            event = await create_event()
            
            # Publish event
            @database_sync_to_async
            def publish_event():
                self.market_data_service.publish_market_event(event)
            
            await publish_event()
            
            logger.info(f"Generated market event: {event_type} for {symbol} ({impact})")
            
        except Exception as e:
            logger.error(f"Error generating market event: {str(e)}")
    
    def _generate_event_content(self, symbol: str, event_type: str, impact: str) -> Dict[str, str]:
        """Generate event content based on type"""
        content_templates = {
            'earnings_beat': {
                'title': f"{symbol} Beats Quarterly Earnings Expectations",
                'description': f"{symbol} reported stronger than expected quarterly results, beating analyst estimates."
            },
            'earnings_miss': {
                'title': f"{symbol} Misses Quarterly Earnings Expectations", 
                'description': f"{symbol} reported weaker than expected quarterly results, missing analyst estimates."
            },
            'dividend_announcement': {
                'title': f"{symbol} Announces Dividend Payment",
                'description': f"{symbol} announced a dividend payment to shareholders."
            },
            'market_news': {
                'title': f"Market News Alert for {symbol}",
                'description': f"Breaking news affecting {symbol} and related securities."
            },
            'technical_alert': {
                'title': f"Technical Analysis Alert for {symbol}",
                'description': f"{symbol} has triggered a technical indicator signal."
            }
        }
        
        return content_templates.get(event_type, {
            'title': f"Market Update for {symbol}",
            'description': f"Market update affecting {symbol}."
        })
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        return {
            'is_running': self.is_running,
            'symbols_count': len(self.symbols),
            'update_interval': self.update_interval,
            'price_data_available': len(self.price_data) > 0,
            'supported_symbols': self.symbols
        }
    
    def reset_price_data(self):
        """Reset all price data to initial values"""
        self.price_data = self._initialize_price_data()
        logger.info("Price data reset to initial values")
    
    def set_symbol_trend(self, symbol: str, trend: int):
        """Manually set trend for a symbol (-1: down, 0: sideways, 1: up)"""
        if symbol in self.price_data and trend in [-1, 0, 1]:
            self.price_data[symbol]['trend'] = trend
            logger.info(f"Set trend for {symbol} to {trend}")
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current information for a symbol"""
        if symbol not in self.price_data:
            return None
        
        info = self.price_data[symbol].copy()
        # Convert Decimal to float for JSON serialization
        for key, value in info.items():
            if isinstance(value, Decimal):
                info[key] = float(value)
        
        return info
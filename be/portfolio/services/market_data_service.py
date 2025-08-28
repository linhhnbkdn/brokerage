"""
Market data service for portfolio price updates
"""

from decimal import Decimal
from typing import Optional, Dict, List
import requests
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache


class MarketDataService:
    """Service for fetching market data and prices"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes cache for real-time prices
        self.daily_cache_timeout = 3600  # 1 hour cache for historical data
    
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current market price for a symbol
        
        Args:
            symbol: Stock/crypto symbol
            
        Returns:
            Current price as Decimal or None if not found
        """
        try:
            # Check cache first
            cache_key = f"price_{symbol.upper()}"
            cached_price = cache.get(cache_key)
            
            if cached_price:
                return Decimal(str(cached_price))
            
            # Fetch from external API (placeholder implementation)
            price = self._fetch_price_from_api(symbol)
            
            if price:
                # Cache the result
                cache.set(cache_key, float(price), self.cache_timeout)
                return price
            
            return None
            
        except Exception as e:
            # Log error and return None
            print(f"Error fetching price for {symbol}: {str(e)}")
            return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        Get current prices for multiple symbols
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dictionary mapping symbol to price
        """
        prices = {}
        
        # Try to get from cache first
        cached_symbols = []
        uncached_symbols = []
        
        for symbol in symbols:
            cache_key = f"price_{symbol.upper()}"
            cached_price = cache.get(cache_key)
            
            if cached_price:
                prices[symbol.upper()] = Decimal(str(cached_price))
                cached_symbols.append(symbol)
            else:
                uncached_symbols.append(symbol)
        
        # Fetch uncached prices
        if uncached_symbols:
            try:
                batch_prices = self._fetch_multiple_prices_from_api(uncached_symbols)
                
                for symbol, price in batch_prices.items():
                    if price:
                        prices[symbol.upper()] = price
                        cache_key = f"price_{symbol.upper()}"
                        cache.set(cache_key, float(price), self.cache_timeout)
                    else:
                        prices[symbol.upper()] = None
            except Exception as e:
                print(f"Error fetching batch prices: {str(e)}")
                # Set None for all uncached symbols
                for symbol in uncached_symbols:
                    prices[symbol.upper()] = None
        
        return prices
    
    def get_historical_prices(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        Get historical price data for a symbol
        
        Args:
            symbol: Stock/crypto symbol
            days: Number of days of historical data
            
        Returns:
            List of price data dictionaries
        """
        try:
            cache_key = f"historical_{symbol.upper()}_{days}d"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return cached_data
            
            # Fetch from external API
            historical_data = self._fetch_historical_from_api(symbol, days)
            
            if historical_data:
                # Cache the result for longer since historical data doesn't change
                cache.set(cache_key, historical_data, self.daily_cache_timeout)
                return historical_data
            
            return []
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return []
    
    def get_market_status(self) -> Dict:
        """
        Get current market status information
        
        Returns:
            Dictionary with market status information
        """
        try:
            cache_key = "market_status"
            cached_status = cache.get(cache_key)
            
            if cached_status:
                return cached_status
            
            # For now, return a simple market status
            # In production, this would fetch from a real market data API
            now = datetime.now()
            is_market_hours = 9 <= now.hour < 16 and now.weekday() < 5
            
            status = {
                'is_open': is_market_hours,
                'next_open': self._calculate_next_market_open(now),
                'timezone': 'US/Eastern',
                'last_updated': now.isoformat()
            }
            
            # Cache for 1 minute
            cache.set(cache_key, status, 60)
            return status
            
        except Exception as e:
            print(f"Error fetching market status: {str(e)}")
            return {
                'is_open': False,
                'next_open': None,
                'timezone': 'US/Eastern',
                'last_updated': datetime.now().isoformat()
            }
    
    def _fetch_price_from_api(self, symbol: str) -> Optional[Decimal]:
        """
        Fetch single price from external API
        This is a placeholder implementation
        """
        # In production, this would call a real market data API like:
        # - Alpha Vantage
        # - IEX Cloud
        # - Yahoo Finance
        # - Polygon.io
        # - etc.
        
        # For development/testing, return simulated prices
        if hasattr(settings, 'USE_SIMULATED_MARKET_DATA') and settings.USE_SIMULATED_MARKET_DATA:
            return self._get_simulated_price(symbol)
        
        # Placeholder for real API implementation
        # try:
        #     api_key = getattr(settings, 'MARKET_DATA_API_KEY', None)
        #     if not api_key:
        #         return None
        #     
        #     url = f"https://api.example.com/v1/quote/{symbol}"
        #     headers = {'Authorization': f'Bearer {api_key}'}
        #     response = requests.get(url, headers=headers, timeout=10)
        #     
        #     if response.status_code == 200:
        #         data = response.json()
        #         return Decimal(str(data['price']))
        #     
        #     return None
        # except Exception:
        #     return None
        
        return self._get_simulated_price(symbol)
    
    def _fetch_multiple_prices_from_api(self, symbols: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        Fetch multiple prices from external API
        """
        prices = {}
        
        # In production, use batch API calls for better performance
        for symbol in symbols:
            prices[symbol] = self._fetch_price_from_api(symbol)
        
        return prices
    
    def _fetch_historical_from_api(self, symbol: str, days: int) -> List[Dict]:
        """
        Fetch historical data from external API
        """
        # Placeholder implementation with simulated data
        historical_data = []
        
        base_price = self._get_simulated_price(symbol) or Decimal('100.00')
        
        for i in range(days):
            # Simulate price movements
            date_offset = timedelta(days=days - i - 1)
            price_date = datetime.now().date() - date_offset
            
            # Random-ish price movement
            price_change = Decimal(str((i % 7 - 3) * 0.02))  # -6% to +6% variation
            price = base_price * (1 + price_change)
            
            historical_data.append({
                'date': price_date.isoformat(),
                'open': float(price * Decimal('0.995')),
                'high': float(price * Decimal('1.015')),
                'low': float(price * Decimal('0.985')),
                'close': float(price),
                'volume': 1000000 + (i * 10000)
            })
        
        return historical_data
    
    def _get_simulated_price(self, symbol: str) -> Decimal:
        """
        Generate simulated prices for development/testing
        """
        import hashlib
        
        # Generate consistent but varying prices based on symbol
        hash_input = f"{symbol}{datetime.now().strftime('%Y-%m-%d-%H')}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        
        # Base prices for common symbols
        base_prices = {
            'AAPL': Decimal('150.00'),
            'GOOGL': Decimal('2500.00'),
            'MSFT': Decimal('300.00'),
            'TSLA': Decimal('800.00'),
            'SPY': Decimal('400.00'),
            'QQQ': Decimal('350.00'),
            'BTC': Decimal('45000.00'),
            'ETH': Decimal('3000.00'),
        }
        
        base_price = base_prices.get(symbol.upper(), Decimal('100.00'))
        
        # Add some variation based on hash
        variation = Decimal(str((hash_value % 21 - 10) / 100))  # -10% to +10%
        final_price = base_price * (1 + variation)
        
        return final_price.quantize(Decimal('0.01'))
    
    def _calculate_next_market_open(self, current_time: datetime) -> str:
        """Calculate next market open time"""
        # Simplified logic - in production would handle holidays, etc.
        if current_time.weekday() >= 5:  # Weekend
            days_until_monday = 7 - current_time.weekday()
            next_open = current_time + timedelta(days=days_until_monday)
            next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
        elif current_time.hour >= 16:  # After market close
            next_open = current_time + timedelta(days=1)
            next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
        else:  # Before market open
            next_open = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
        
        return next_open.isoformat()
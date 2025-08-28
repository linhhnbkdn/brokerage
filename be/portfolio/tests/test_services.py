"""
Test cases for portfolio services
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User

from portfolio.services.portfolio_service import PortfolioService
from portfolio.services.market_data_service import MarketDataService
from portfolio.services.snapshot_service import SnapshotService
from portfolio.services.performance_calculator import PerformanceCalculator
from portfolio.models import Position, PortfolioSnapshot, PerformanceMetrics
from portfolio.tests.factories import (
    UserFactory,
    UserBalanceFactory,
    PositionFactory,
    ProfitablePositionFactory,
    LosingPositionFactory,
    PortfolioSnapshotFactory,
    PerformanceMetricsFactory,
    create_user_with_portfolio
)


@pytest.mark.django_db
class TestPortfolioService:
    """Test cases for PortfolioService"""
    
    def setup_method(self):
        """Set up test data"""
        self.user = UserFactory()
        self.user_balance = UserBalanceFactory(user=self.user, available_balance=Decimal('10000.00'))
        self.portfolio_service = PortfolioService()
        
        # Mock market data service
        self.mock_market_service = Mock()
        self.portfolio_service.market_data_service = self.mock_market_service
    
    def test_get_portfolio_overview_with_positions(self):
        """Test portfolio overview calculation with positions"""
        # Create test positions
        positions = [
            ProfitablePositionFactory(user=self.user, symbol='AAPL', quantity=Decimal('100'), average_cost=Decimal('150'), current_price=Decimal('160')),
            LosingPositionFactory(user=self.user, symbol='GOOGL', quantity=Decimal('50'), average_cost=Decimal('2000'), current_price=Decimal('1900'))
        ]
        
        overview = self.portfolio_service.get_portfolio_overview(self.user)
        
        # Test calculated values
        assert overview['positions_count'] == 2
        assert overview['total_value'] == Decimal('111000.00')  # (100*160) + (50*1900)
        assert overview['total_cost_basis'] == Decimal('115000.00')  # (100*150) + (50*2000)
        assert overview['total_gain_loss'] == Decimal('-4000.00')  # 111000 - 115000
        assert overview['cash_balance'] == Decimal('10000.00')
        assert overview['total_portfolio_value'] == Decimal('121000.00')  # 111000 + 10000
        
        # Test asset allocation
        assert 'asset_allocation' in overview
        assert len(overview['positions_data']) == 2
    
    def test_get_portfolio_overview_no_positions(self):
        """Test portfolio overview with no positions"""
        overview = self.portfolio_service.get_portfolio_overview(self.user)
        
        assert overview['positions_count'] == 0
        assert overview['total_value'] == Decimal('0.00')
        assert overview['total_cost_basis'] == Decimal('0.00')
        assert overview['cash_balance'] == Decimal('10000.00')
        assert overview['total_portfolio_value'] == Decimal('10000.00')
        assert overview['asset_allocation'] == {}
    
    def test_add_position_success(self):
        """Test successful position addition"""
        self.mock_market_service.get_current_price.return_value = Decimal('155.00')
        
        position_data = {
            'symbol': 'AAPL',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': Decimal('100'),
            'average_cost': Decimal('150.00'),
            'current_price': Decimal('150.00')
        }
        
        position = self.portfolio_service.add_position(self.user, position_data)
        
        assert position.user == self.user
        assert position.symbol == 'AAPL'
        assert position.quantity == Decimal('100')
        assert position.current_price == Decimal('155.00')  # Updated by market service
        
        # Verify market service was called
        self.mock_market_service.get_current_price.assert_called_once_with('AAPL')
    
    def test_add_position_duplicate_symbol(self):
        """Test adding position with duplicate symbol fails"""
        # Create existing position
        PositionFactory(user=self.user, symbol='AAPL', status='active')
        
        position_data = {
            'symbol': 'AAPL',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': Decimal('100'),
            'average_cost': Decimal('150.00')
        }
        
        with pytest.raises(Exception) as excinfo:
            self.portfolio_service.add_position(self.user, position_data)
        
        assert 'already exists' in str(excinfo.value)
    
    def test_update_position(self):
        """Test position update functionality"""
        position = PositionFactory(user=self.user, quantity=Decimal('100'), current_price=Decimal('150'))
        
        update_data = {
            'quantity': Decimal('150'),
            'current_price': Decimal('160')
        }
        
        updated_position = self.portfolio_service.update_position(position, update_data)
        
        assert updated_position.quantity == Decimal('150')
        assert updated_position.current_price == Decimal('160')
    
    def test_close_position(self):
        """Test position closing functionality"""
        position = PositionFactory(user=self.user, status='active')
        
        closed_position = self.portfolio_service.close_position(position)
        
        assert closed_position.status == 'closed'
        assert closed_position.closed_at is not None
    
    def test_update_portfolio_prices(self):
        """Test bulk price update for portfolio"""
        # Create positions
        positions = [
            PositionFactory(user=self.user, symbol='AAPL', current_price=Decimal('150')),
            PositionFactory(user=self.user, symbol='GOOGL', current_price=Decimal('2000'))
        ]
        
        # Mock price updates
        self.mock_market_service.get_current_price.side_effect = [
            Decimal('155.00'),  # AAPL new price
            Decimal('2100.00')  # GOOGL new price
        ]
        
        updated_count = self.portfolio_service.update_portfolio_prices(self.user)
        
        assert updated_count == 2
        
        # Verify positions were updated
        positions[0].refresh_from_db()
        positions[1].refresh_from_db()
        
        assert positions[0].current_price == Decimal('155.00')
        assert positions[1].current_price == Decimal('2100.00')
    
    def test_get_portfolio_allocation(self):
        """Test portfolio allocation calculation"""
        # Create positions with different instrument types
        PositionFactory(user=self.user, instrument_type='stock', symbol='AAPL', quantity=Decimal('100'), current_price=Decimal('150'))
        PositionFactory(user=self.user, instrument_type='stock', symbol='GOOGL', quantity=Decimal('10'), current_price=Decimal('2000'))
        PositionFactory(user=self.user, instrument_type='etf', symbol='SPY', quantity=Decimal('50'), current_price=Decimal('400'))
        
        allocation = self.portfolio_service.get_portfolio_allocation(self.user)
        
        # Total portfolio: 15000 + 20000 + 20000 + 10000 (cash) = 65000
        assert allocation['total_portfolio_value'] == Decimal('65000.00')
        assert allocation['cash_balance'] == Decimal('10000.00')
        
        # Test allocation by instrument type
        assert 'stock' in allocation['allocation_by_type']
        assert 'etf' in allocation['allocation_by_type']
        
        stock_allocation = allocation['allocation_by_type']['stock']
        assert stock_allocation['total_value'] == Decimal('35000.00')  # 15000 + 20000
        assert stock_allocation['count'] == 2
        
        etf_allocation = allocation['allocation_by_type']['etf']
        assert etf_allocation['total_value'] == Decimal('20000.00')
        assert etf_allocation['count'] == 1
    
    def test_calculate_daily_performance(self):
        """Test daily performance calculation"""
        # Create yesterday's snapshot
        yesterday = date.today() - timedelta(days=1)
        PortfolioSnapshotFactory(
            user=self.user,
            snapshot_date=yesterday,
            total_value=Decimal('25000.00'),
            cash_balance=Decimal('10000.00')
        )
        
        current_value = Decimal('36000.00')  # Current portfolio value
        
        day_gain_loss, day_gain_loss_percent = self.portfolio_service._calculate_daily_performance(
            self.user, current_value
        )
        
        # Yesterday total was 35000, today is 36000, gain of 1000
        assert day_gain_loss == Decimal('1000.00')
        expected_percent = (Decimal('1000.00') / Decimal('35000.00')) * 100
        assert abs(day_gain_loss_percent - expected_percent) < Decimal('0.01')
    
    def test_diversification_score_calculation(self):
        """Test diversification score calculation"""
        # Test with well-diversified portfolio
        allocation_data = {
            'stock': {'percentage': Decimal('40.00')},
            'bond': {'percentage': Decimal('30.00')},
            'etf': {'percentage': Decimal('20.00')},
            'crypto': {'percentage': Decimal('10.00')}
        }
        
        score = self.portfolio_service._calculate_diversification_score(allocation_data)
        assert score > Decimal('70.00')  # Should be high for diversified portfolio
        
        # Test with concentrated portfolio
        concentrated_allocation = {
            'stock': {'percentage': Decimal('90.00')},
            'cash': {'percentage': Decimal('10.00')}
        }
        
        concentrated_score = self.portfolio_service._calculate_diversification_score(concentrated_allocation)
        assert concentrated_score < score  # Should be lower for concentrated portfolio


@pytest.mark.django_db 
class TestMarketDataService:
    """Test cases for MarketDataService"""
    
    def setup_method(self):
        """Set up test data"""
        self.market_service = MarketDataService()
    
    def test_get_current_price_cached(self):
        """Test current price retrieval with caching"""
        with patch('django.core.cache.cache.get') as mock_get, \
             patch('django.core.cache.cache.set') as mock_set:
            
            # Test cache miss
            mock_get.return_value = None
            
            with patch.object(self.market_service, '_fetch_price_from_api', return_value=Decimal('150.00')):
                price = self.market_service.get_current_price('AAPL')
                
                assert price == Decimal('150.00')
                mock_set.assert_called_once()
            
            # Test cache hit
            mock_get.return_value = 155.00
            
            price = self.market_service.get_current_price('AAPL')
            assert price == Decimal('155.00')
    
    def test_get_multiple_prices(self):
        """Test batch price retrieval"""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        with patch('django.core.cache.cache.get') as mock_get, \
             patch.object(self.market_service, '_fetch_multiple_prices_from_api') as mock_batch:
            
            # All symbols not cached
            mock_get.return_value = None
            mock_batch.return_value = {
                'AAPL': Decimal('150.00'),
                'GOOGL': Decimal('2000.00'),
                'MSFT': Decimal('300.00')
            }
            
            prices = self.market_service.get_multiple_prices(symbols)
            
            assert len(prices) == 3
            assert prices['AAPL'] == Decimal('150.00')
            mock_batch.assert_called_once()
    
    def test_get_historical_prices(self):
        """Test historical price data retrieval"""
        with patch('django.core.cache.cache.get') as mock_get, \
             patch.object(self.market_service, '_fetch_historical_from_api') as mock_historical:
            
            mock_get.return_value = None
            mock_historical.return_value = [
                {'date': '2024-01-01', 'open': 150.0, 'high': 155.0, 'low': 148.0, 'close': 152.0, 'volume': 1000000}
            ]
            
            historical_data = self.market_service.get_historical_prices('AAPL', 30)
            
            assert len(historical_data) == 1
            assert historical_data[0]['symbol'] is None or 'date' in historical_data[0]
            mock_historical.assert_called_once_with('AAPL', 30)
    
    def test_get_market_status(self):
        """Test market status retrieval"""
        status_data = self.market_service.get_market_status()
        
        assert 'is_open' in status_data
        assert 'next_open' in status_data
        assert 'timezone' in status_data
        assert 'last_updated' in status_data
        assert isinstance(status_data['is_open'], bool)
    
    def test_simulated_price_generation(self):
        """Test simulated price generation consistency"""
        # Same symbol should return consistent price within the same hour
        price1 = self.market_service._get_simulated_price('AAPL')
        price2 = self.market_service._get_simulated_price('AAPL')
        
        assert price1 == price2  # Should be consistent within same hour
        assert price1 > 0  # Should be positive
        
        # Different symbols should return different prices
        aapl_price = self.market_service._get_simulated_price('AAPL')
        googl_price = self.market_service._get_simulated_price('GOOGL')
        
        assert aapl_price != googl_price


@pytest.mark.django_db
class TestSnapshotService:
    """Test cases for SnapshotService"""
    
    def setup_method(self):
        """Set up test data"""
        self.user = UserFactory()
        self.user_balance = UserBalanceFactory(user=self.user)
        self.snapshot_service = SnapshotService()
    
    def test_create_daily_snapshot(self):
        """Test daily snapshot creation"""
        # Create positions
        positions = [
            PositionFactory(user=self.user, symbol='AAPL'),
            PositionFactory(user=self.user, symbol='GOOGL')
        ]
        
        snapshot_date = date.today()
        snapshot = self.snapshot_service.create_daily_snapshot(self.user, snapshot_date)
        
        assert snapshot.user == self.user
        assert snapshot.snapshot_date == snapshot_date
        assert snapshot.cash_balance == self.user_balance.available_balance
        assert snapshot.holdings_data['position_count'] == 2
        assert 'asset_allocation' in snapshot.holdings_data
    
    def test_create_snapshot_force_recreate(self):
        """Test snapshot recreation with force flag"""
        snapshot_date = date.today()
        
        # Create initial snapshot
        original_snapshot = self.snapshot_service.create_daily_snapshot(self.user, snapshot_date)
        original_id = original_snapshot.snapshot_id
        
        # Create positions and recreate
        PositionFactory(user=self.user, symbol='AAPL')
        new_snapshot = self.snapshot_service.create_daily_snapshot(
            self.user, snapshot_date, force_recreate=True
        )
        
        assert new_snapshot.snapshot_id != original_id
        assert new_snapshot.snapshot_date == snapshot_date
    
    def test_create_snapshots_for_date_range(self):
        """Test bulk snapshot creation for date range"""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        snapshots = self.snapshot_service.create_snapshots_for_date_range(
            self.user, start_date, end_date
        )
        
        assert len(snapshots) == 8  # 7 days + today
        assert all(s.user == self.user for s in snapshots)
        assert min(s.snapshot_date for s in snapshots) == start_date
        assert max(s.snapshot_date for s in snapshots) == end_date
    
    def test_get_snapshots_for_period(self):
        """Test retrieving snapshots for specific period"""
        # Create snapshots over multiple days
        dates = [date.today() - timedelta(days=i) for i in range(10)]
        snapshots = [
            PortfolioSnapshotFactory(user=self.user, snapshot_date=d) 
            for d in dates
        ]
        
        start_date = date.today() - timedelta(days=5)
        end_date = date.today()
        
        period_snapshots = self.snapshot_service.get_snapshots_for_period(
            self.user, start_date, end_date
        )
        
        assert len(period_snapshots) == 6  # 5 days + today
        assert all(start_date <= s.snapshot_date <= end_date for s in period_snapshots)
    
    def test_calculate_snapshot_metrics(self):
        """Test metrics calculation from snapshots"""
        # Create snapshots with progression
        snapshots = []
        base_value = Decimal('10000.00')
        
        for i in range(30):
            snapshot_date = date.today() - timedelta(days=30 - i - 1)
            total_value = base_value + (i * Decimal('100.00'))  # Steady growth
            
            snapshot = PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=snapshot_date,
                total_value=total_value,
                cash_balance=Decimal('5000.00'),
                total_cost_basis=base_value
            )
            snapshots.append(snapshot)
        
        metrics = self.snapshot_service.calculate_snapshot_metrics(snapshots)
        
        assert metrics['period_days'] == 30
        assert metrics['start_value'] == Decimal('15000.00')  # 10000 + 5000 cash
        assert metrics['end_value'] == Decimal('17900.00')    # 12900 + 5000 cash
        assert metrics['total_return'] > 0
        assert 'volatility' in metrics
        assert 'max_drawdown' in metrics
    
    def test_generate_chart_data(self):
        """Test chart data generation from snapshots"""
        snapshots = [
            PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=date.today() - timedelta(days=i),
                total_value=Decimal('10000') + Decimal(i * 100)
            )
            for i in range(5)
        ]
        
        chart_data = self.snapshot_service.generate_snapshot_chart_data(snapshots)
        
        assert len(chart_data) == 5
        
        # Verify chart data structure
        for data_point in chart_data:
            assert 'date' in data_point
            assert 'timestamp' in data_point
            assert 'total_value' in data_point
            assert 'portfolio_value' in data_point
            assert 'cash_balance' in data_point
            assert isinstance(data_point['total_value'], float)
    
    def test_cleanup_old_snapshots(self):
        """Test cleanup of old snapshots"""
        # Create old and recent snapshots
        old_date = date.today() - timedelta(days=400)  # Older than default 365 days
        recent_date = date.today() - timedelta(days=30)
        
        old_snapshot = PortfolioSnapshotFactory(user=self.user, snapshot_date=old_date)
        recent_snapshot = PortfolioSnapshotFactory(user=self.user, snapshot_date=recent_date)
        
        deleted_count = self.snapshot_service.cleanup_old_snapshots(self.user, keep_days=365)
        
        assert deleted_count == 1
        
        # Verify only old snapshot was deleted
        assert not PortfolioSnapshot.objects.filter(snapshot_id=old_snapshot.snapshot_id).exists()
        assert PortfolioSnapshot.objects.filter(snapshot_id=recent_snapshot.snapshot_id).exists()


@pytest.mark.django_db
class TestPerformanceCalculator:
    """Test cases for PerformanceCalculator"""
    
    def setup_method(self):
        """Set up test data"""
        self.calculator = PerformanceCalculator()
        self.user = UserFactory()
    
    def test_calculate_period_metrics(self):
        """Test comprehensive metrics calculation for a period"""
        # Create snapshots with known progression
        snapshots = []
        base_value = Decimal('10000.00')
        
        for i in range(30):
            snapshot_date = date.today() - timedelta(days=30 - i - 1)
            # Simulate 5% growth over 30 days with some volatility
            growth_factor = 1 + (i * 0.05 / 30)  
            volatility = 0.01 * (i % 3 - 1)  # Add some volatility
            total_value = base_value * Decimal(str(growth_factor + volatility))
            
            snapshot = PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=snapshot_date,
                total_value=total_value,
                cash_balance=Decimal('2000.00')
            )
            snapshots.append(snapshot)
        
        metrics = self.calculator.calculate_period_metrics(
            user=self.user,
            period='1M',
            snapshots=snapshots,
            benchmark_data={'return': Decimal('3.00')}
        )
        
        assert metrics is not None
        assert metrics.user == self.user
        assert metrics.period == '1M'
        assert metrics.total_return is not None
        assert metrics.volatility is not None
        assert metrics.sharpe_ratio is not None
        assert metrics.benchmark_return == Decimal('3.00')
        assert metrics.alpha is not None  # Should be total_return - benchmark_return
    
    def test_calculate_rolling_metrics(self):
        """Test rolling metrics calculation"""
        # Create 60 days of snapshots
        snapshots = []
        for i in range(60):
            snapshot_date = date.today() - timedelta(days=60 - i - 1)
            total_value = Decimal('10000') + Decimal(i * 50)  # Linear growth
            
            snapshot = PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=snapshot_date,
                total_value=total_value,
                cash_balance=Decimal('1000')
            )
            snapshots.append(snapshot)
        
        rolling_metrics = self.calculator.calculate_rolling_metrics(snapshots, window_days=30)
        
        # Should have 31 data points (60 - 30 + 1)
        assert len(rolling_metrics) == 31
        
        # Verify structure of rolling metrics
        for metric in rolling_metrics:
            assert 'date' in metric
            assert 'total_return' in metric
            assert 'volatility' in metric
            assert 'sharpe_ratio' in metric
            assert 'start_value' in metric
            assert 'end_value' in metric
    
    def test_compare_with_benchmark(self):
        """Test portfolio vs benchmark comparison"""
        # Create portfolio snapshots
        snapshots = [
            PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=date.today() - timedelta(days=i),
                total_value=Decimal('10000') * (1 + i * Decimal('0.01')),  # 1% daily growth
                cash_balance=Decimal('1000')
            )
            for i in range(10)
        ]
        
        # Create benchmark data (0.5% daily growth)
        benchmark_data = []
        for i in range(10):
            benchmark_data.append({
                'date': (date.today() - timedelta(days=i)).isoformat(),
                'close': 100 * (1 + i * 0.005)
            })
        
        comparison = self.calculator.compare_with_benchmark(snapshots, benchmark_data)
        
        assert 'beta' in comparison
        assert 'alpha' in comparison
        assert 'correlation' in comparison
        assert 'tracking_error' in comparison
        assert 'portfolio_cumulative_return' in comparison
        assert 'benchmark_cumulative_return' in comparison
        assert 'outperformance' in comparison
        
        # Portfolio should outperform benchmark (1% vs 0.5% daily)
        assert comparison['outperformance'] > 0
    
    def test_total_return_calculation(self):
        """Test total return calculation"""
        start_value = Decimal('10000.00')
        end_value = Decimal('10500.00')
        
        total_return = self.calculator._calculate_total_return(start_value, end_value)
        
        expected_return = Decimal('5.0000')  # 5% return
        assert total_return == expected_return
    
    def test_annualized_return_calculation(self):
        """Test annualized return calculation"""
        total_return = Decimal('5.00')  # 5% return
        days = 30  # 30 days
        
        annualized_return = self.calculator._calculate_annualized_return(total_return, days)
        
        assert annualized_return is not None
        assert annualized_return > total_return  # Should be higher when annualized
    
    def test_volatility_calculation(self):
        """Test volatility calculation from snapshots"""
        # Create snapshots with known volatility pattern
        snapshots = []
        values = [10000, 10100, 9950, 10200, 9900, 10150, 10050]  # Volatile pattern
        
        for i, value in enumerate(values):
            snapshot = PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=date.today() - timedelta(days=len(values) - i - 1),
                total_value=Decimal(str(value)),
                cash_balance=Decimal('1000')
            )
            snapshots.append(snapshot)
        
        volatility = self.calculator._calculate_volatility(snapshots)
        
        assert volatility is not None
        assert volatility > 0  # Should have positive volatility
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation"""
        # Create snapshots with known drawdown
        snapshots = []
        values = [10000, 11000, 12000, 10500, 9500, 11500]  # Peak at 12000, trough at 9500
        
        for i, value in enumerate(values):
            snapshot = PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=date.today() - timedelta(days=len(values) - i - 1),
                total_value=Decimal(str(value)),
                cash_balance=Decimal('1000')
            )
            snapshots.append(snapshot)
        
        max_drawdown = self.calculator._calculate_max_drawdown(snapshots)
        
        # Max drawdown should be (12000-9500)/12000 * 100 = 20.83%
        expected_drawdown = Decimal('20.83')
        assert abs(max_drawdown - expected_drawdown) < Decimal('0.1')
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        annualized_return = Decimal('12.00')  # 12% return
        volatility = Decimal('15.00')  # 15% volatility
        
        sharpe_ratio = self.calculator._calculate_sharpe_ratio(annualized_return, volatility)
        
        # Sharpe ratio = (12 - 2) / 15 = 0.67 (assuming 2% risk-free rate)
        expected_sharpe = Decimal('0.67')
        assert abs(sharpe_ratio - expected_sharpe) < Decimal('0.1')
    
    def test_beta_calculation(self):
        """Test beta calculation"""
        # Portfolio returns: more volatile than benchmark
        portfolio_returns = [Decimal('0.02'), Decimal('-0.01'), Decimal('0.03'), Decimal('-0.015')]
        benchmark_returns = [Decimal('0.01'), Decimal('-0.005'), Decimal('0.015'), Decimal('-0.01')]
        
        beta = self.calculator._calculate_beta(portfolio_returns, benchmark_returns)
        
        assert beta is not None
        assert beta > 0  # Should be positive for correlated assets
    
    def test_correlation_calculation(self):
        """Test correlation coefficient calculation"""
        # Create perfectly correlated returns
        portfolio_returns = [Decimal('0.01'), Decimal('0.02'), Decimal('-0.01'), Decimal('0.015')]
        benchmark_returns = [Decimal('0.005'), Decimal('0.01'), Decimal('-0.005'), Decimal('0.0075')]  # Half the portfolio returns
        
        correlation = self.calculator._calculate_correlation(portfolio_returns, benchmark_returns)
        
        assert correlation is not None
        assert correlation > Decimal('0.8')  # Should be highly correlated
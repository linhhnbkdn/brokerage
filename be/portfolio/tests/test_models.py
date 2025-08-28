"""
Test cases for portfolio models
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from portfolio.models import Position, PortfolioSnapshot, PerformanceMetrics
from portfolio.tests.factories import (
    UserFactory,
    UserBalanceFactory,
    PositionFactory,
    ProfitablePositionFactory,
    LosingPositionFactory,
    PortfolioSnapshotFactory,
    HistoricalSnapshotFactory,
    PerformanceMetricsFactory,
    create_user_with_portfolio
)


@pytest.mark.django_db
class TestPositionModel:
    """Test cases for Position model"""
    
    def test_position_creation(self):
        """Test creating a position with valid data"""
        position = PositionFactory()
        
        assert position.position_id is not None
        assert position.user is not None
        assert position.symbol is not None
        assert position.quantity > 0
        assert position.average_cost > 0
        assert position.status == 'active'
        assert position.opened_at is not None
    
    def test_position_string_representation(self):
        """Test position string representation"""
        position = PositionFactory(symbol='AAPL', quantity=Decimal('100'))
        expected = f"{position.user.email} - AAPL (100)"
        assert str(position) == expected
    
    def test_get_cost_basis(self):
        """Test cost basis calculation"""
        position = PositionFactory(
            quantity=Decimal('100'),
            average_cost=Decimal('150.00')
        )
        assert position.get_cost_basis() == Decimal('15000.00')
    
    def test_get_current_value(self):
        """Test current value calculation"""
        position = PositionFactory(
            quantity=Decimal('100'),
            current_price=Decimal('155.00')
        )
        assert position.get_current_value() == Decimal('15500.00')
    
    def test_get_unrealized_gain_loss(self):
        """Test unrealized gain/loss calculation"""
        position = ProfitablePositionFactory(
            quantity=Decimal('100'),
            average_cost=Decimal('150.00'),
            current_price=Decimal('165.00')
        )
        expected_gain = Decimal('1500.00')  # (165-150) * 100
        assert position.get_unrealized_gain_loss() == expected_gain
    
    def test_get_unrealized_gain_loss_percent(self):
        """Test unrealized gain/loss percentage calculation"""
        position = ProfitablePositionFactory(
            quantity=Decimal('100'),
            average_cost=Decimal('150.00'),
            current_price=Decimal('165.00')
        )
        expected_percent = Decimal('10.00')  # (1500/15000) * 100
        assert position.get_unrealized_gain_loss_percent() == expected_percent
    
    def test_is_profitable(self):
        """Test profitability check"""
        profitable_position = ProfitablePositionFactory()
        losing_position = LosingPositionFactory()
        
        assert profitable_position.is_profitable() is True
        assert losing_position.is_profitable() is False
    
    def test_update_current_price(self):
        """Test price update functionality"""
        position = PositionFactory(current_price=Decimal('150.00'))
        new_price = Decimal('160.00')
        
        old_update_time = position.last_price_update
        position.update_current_price(new_price)
        
        assert position.current_price == new_price
        assert position.last_price_update != old_update_time
    
    def test_position_summary(self):
        """Test position summary generation"""
        position = PositionFactory(
            symbol='AAPL',
            quantity=Decimal('100'),
            average_cost=Decimal('150.00'),
            current_price=Decimal('155.00')
        )
        summary = position.get_position_summary()
        
        assert summary['symbol'] == 'AAPL'
        assert Decimal(summary['quantity']) == Decimal('100')
        assert Decimal(summary['cost_basis']) == Decimal('15000.00')
        assert Decimal(summary['current_value']) == Decimal('15500.00')
        assert 'position_id' in summary
        assert 'unrealized_gain_loss' in summary
    
    def test_unique_constraint(self):
        """Test unique constraint for user + symbol + status"""
        user = UserFactory()
        PositionFactory(user=user, symbol='AAPL', status='active')
        
        with pytest.raises(IntegrityError):
            PositionFactory(user=user, symbol='AAPL', status='active')
    
    def test_position_validation(self):
        """Test position field validation"""
        with pytest.raises(ValidationError):
            position = PositionFactory.build(quantity=Decimal('-10'))
            position.full_clean()


@pytest.mark.django_db
class TestPortfolioSnapshotModel:
    """Test cases for PortfolioSnapshot model"""
    
    def test_snapshot_creation(self):
        """Test creating a snapshot with valid data"""
        snapshot = PortfolioSnapshotFactory()
        
        assert snapshot.snapshot_id is not None
        assert snapshot.user is not None
        assert snapshot.snapshot_date is not None
        assert snapshot.total_value >= 0
        assert snapshot.cash_balance >= 0
        assert isinstance(snapshot.holdings_data, dict)
    
    def test_snapshot_string_representation(self):
        """Test snapshot string representation"""
        snapshot = PortfolioSnapshotFactory(
            snapshot_date=date(2024, 1, 15),
            total_value=Decimal('25000.00')
        )
        expected = f"{snapshot.user.email} - 2024-01-15 ($25000.00)"
        assert str(snapshot) == expected
    
    def test_calculate_total_value_with_cash(self):
        """Test total value calculation including cash"""
        snapshot = PortfolioSnapshotFactory(
            total_value=Decimal('25000.00'),
            cash_balance=Decimal('5000.00')
        )
        expected_total = Decimal('30000.00')
        assert snapshot.calculate_total_value_with_cash() == expected_total
    
    def test_get_cash_allocation_percent(self):
        """Test cash allocation percentage calculation"""
        snapshot = PortfolioSnapshotFactory(
            total_value=Decimal('25000.00'),
            cash_balance=Decimal('5000.00')
        )
        expected_percent = Decimal('16.67')  # 5000/30000 * 100, rounded
        actual_percent = snapshot.get_cash_allocation_percent().quantize(Decimal('0.01'))
        assert actual_percent == expected_percent
    
    def test_is_profitable(self):
        """Test profitability check for snapshot"""
        profitable_snapshot = PortfolioSnapshotFactory(total_gain_loss=Decimal('1000.00'))
        losing_snapshot = PortfolioSnapshotFactory(total_gain_loss=Decimal('-500.00'))
        
        assert profitable_snapshot.is_profitable() is True
        assert losing_snapshot.is_profitable() is False
    
    def test_create_daily_snapshot(self):
        """Test daily snapshot creation class method"""
        user = UserFactory()
        UserBalanceFactory(user=user, available_balance=Decimal('5000.00'))
        
        # Create some positions
        positions = [
            PositionFactory(user=user, symbol='AAPL'),
            PositionFactory(user=user, symbol='GOOGL')
        ]
        
        positions_data = [pos.get_position_summary() for pos in positions]
        cash_balance = Decimal('5000.00')
        
        snapshot = PortfolioSnapshot.create_daily_snapshot(
            user=user,
            positions_data=positions_data,
            cash_balance=cash_balance
        )
        
        assert snapshot.user == user
        assert snapshot.cash_balance == cash_balance
        assert snapshot.holdings_data['position_count'] == len(positions_data)
        assert 'asset_allocation' in snapshot.holdings_data
    
    def test_snapshot_summary(self):
        """Test snapshot summary generation"""
        snapshot = PortfolioSnapshotFactory()
        summary = snapshot.get_snapshot_summary()
        
        assert 'snapshot_id' in summary
        assert 'snapshot_date' in summary
        assert 'total_value' in summary
        assert 'cash_balance' in summary
        assert 'total_portfolio_value' in summary
        assert 'holdings_count' in summary
    
    def test_unique_constraint_user_date(self):
        """Test unique constraint for user + snapshot_date"""
        user = UserFactory()
        snapshot_date = date.today()
        
        PortfolioSnapshotFactory(user=user, snapshot_date=snapshot_date)
        
        with pytest.raises(IntegrityError):
            PortfolioSnapshotFactory(user=user, snapshot_date=snapshot_date)


@pytest.mark.django_db
class TestPerformanceMetricsModel:
    """Test cases for PerformanceMetrics model"""
    
    def test_metrics_creation(self):
        """Test creating performance metrics with valid data"""
        metrics = PerformanceMetricsFactory()
        
        assert metrics.metrics_id is not None
        assert metrics.user is not None
        assert metrics.period in ['1M', '3M', '6M', '1Y']
        assert metrics.start_date < metrics.end_date
        assert metrics.calculated_at is not None
    
    def test_metrics_string_representation(self):
        """Test metrics string representation"""
        metrics = PerformanceMetricsFactory(
            period='1M',
            total_return=Decimal('5.25')
        )
        expected = f"{metrics.user.email} - 1M (5.25%)"
        assert str(metrics) == expected
    
    def test_outperformed_benchmark(self):
        """Test benchmark outperformance check"""
        # Metrics that outperformed benchmark
        good_metrics = PerformanceMetricsFactory(
            total_return=Decimal('8.50'),
            benchmark_return=Decimal('6.00')
        )
        assert good_metrics.outperformed_benchmark() is True
        
        # Metrics that underperformed benchmark
        poor_metrics = PerformanceMetricsFactory(
            total_return=Decimal('4.50'),
            benchmark_return=Decimal('6.00')
        )
        assert poor_metrics.outperformed_benchmark() is False
        
        # Metrics without benchmark
        no_benchmark = PerformanceMetricsFactory(benchmark_return=None)
        assert no_benchmark.outperformed_benchmark() is False
    
    def test_is_profitable(self):
        """Test profitability check"""
        profitable_metrics = PerformanceMetricsFactory(total_return=Decimal('5.25'))
        losing_metrics = PerformanceMetricsFactory(total_return=Decimal('-2.50'))
        
        assert profitable_metrics.is_profitable() is True
        assert losing_metrics.is_profitable() is False
    
    def test_get_risk_adjusted_return(self):
        """Test risk-adjusted return (Sharpe ratio) retrieval"""
        metrics = PerformanceMetricsFactory(sharpe_ratio=Decimal('0.85'))
        assert metrics.get_risk_adjusted_return() == Decimal('0.85')
        
        metrics_no_sharpe = PerformanceMetricsFactory(sharpe_ratio=None)
        assert metrics_no_sharpe.get_risk_adjusted_return() == Decimal('0.0000')
    
    def test_calculate_metrics_class_method(self):
        """Test metrics calculation class method"""
        portfolio_data = create_user_with_portfolio(snapshot_count=30)
        user = portfolio_data['user']
        snapshots = portfolio_data['snapshots']
        
        # Test calculation
        metrics = PerformanceMetrics.calculate_metrics(
            user=user,
            period='1M',
            snapshots=snapshots,
            benchmark_data={'return': Decimal('4.50')}
        )
        
        assert metrics is not None
        assert metrics.user == user
        assert metrics.period == '1M'
        assert metrics.total_return is not None
        assert metrics.volatility is not None
        assert metrics.benchmark_return == Decimal('4.50')
    
    def test_calculate_volatility_helper(self):
        """Test volatility calculation helper method"""
        # Create test values with known volatility
        values = [Decimal('100'), Decimal('102'), Decimal('98'), Decimal('105'), Decimal('97')]
        volatility = PerformanceMetrics._calculate_volatility(values)
        
        assert volatility is not None
        assert volatility > 0
    
    def test_calculate_max_drawdown_helper(self):
        """Test max drawdown calculation helper method"""
        # Create test values with known drawdown
        values = [Decimal('100'), Decimal('110'), Decimal('95'), Decimal('105'), Decimal('90')]
        max_drawdown = PerformanceMetrics._calculate_max_drawdown(values)
        
        # Max drawdown should be (110-90)/110 * 100 = 18.18%
        expected = Decimal('18.18')
        assert abs(max_drawdown - expected) < Decimal('0.1')
    
    def test_metrics_summary(self):
        """Test metrics summary generation"""
        metrics = PerformanceMetricsFactory()
        summary = metrics.get_metrics_summary()
        
        assert 'metrics_id' in summary
        assert 'period' in summary
        assert 'period_display' in summary
        assert 'total_return' in summary
        assert 'volatility' in summary
        assert 'is_profitable' in summary
        assert 'outperformed_benchmark' in summary
    
    def test_unique_constraint(self):
        """Test unique constraint for user + period + dates"""
        user = UserFactory()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        PerformanceMetricsFactory(
            user=user,
            period='1M',
            start_date=start_date,
            end_date=end_date
        )
        
        with pytest.raises(IntegrityError):
            PerformanceMetricsFactory(
                user=user,
                period='1M',
                start_date=start_date,
                end_date=end_date
            )


@pytest.mark.django_db
class TestModelIntegration:
    """Test integration between models"""
    
    def test_complete_portfolio_workflow(self):
        """Test complete workflow from positions to metrics"""
        # Create user with complete portfolio
        portfolio_data = create_user_with_portfolio(
            position_count=5,
            snapshot_count=30
        )
        
        user = portfolio_data['user']
        positions = portfolio_data['positions']
        snapshots = portfolio_data['snapshots']
        metrics = portfolio_data['metrics']
        
        # Verify all data was created correctly
        assert len(positions) == 5
        assert len(snapshots) == 30
        assert len(metrics) == 4  # 1M, 3M, 6M, 1Y
        
        # Verify relationships
        assert all(pos.user == user for pos in positions)
        assert all(snap.user == user for snap in snapshots)
        assert all(metric.user == user for metric in metrics)
        
        # Test portfolio calculations
        total_value = sum(pos.get_current_value() for pos in positions)
        assert total_value > 0
        
        # Test snapshot data consistency
        latest_snapshot = max(snapshots, key=lambda s: s.snapshot_date)
        assert latest_snapshot.holdings_data['position_count'] == len(positions)
        
        # Test metrics calculations
        yearly_metrics = next(m for m in metrics if m.period == '1Y')
        assert yearly_metrics.total_return is not None
        assert yearly_metrics.starting_value < yearly_metrics.ending_value
    
    def test_user_deletion_cascade(self):
        """Test cascade deletion when user is deleted"""
        portfolio_data = create_user_with_portfolio(position_count=2, snapshot_count=5)
        user = portfolio_data['user']
        
        # Verify data exists
        assert Position.objects.filter(user=user).count() == 2
        assert PortfolioSnapshot.objects.filter(user=user).count() == 5
        assert PerformanceMetrics.objects.filter(user=user).count() == 4
        
        # Delete user
        user_id = user.id
        user.delete()
        
        # Verify cascade deletion
        assert Position.objects.filter(user_id=user_id).count() == 0
        assert PortfolioSnapshot.objects.filter(user_id=user_id).count() == 0
        assert PerformanceMetrics.objects.filter(user_id=user_id).count() == 0
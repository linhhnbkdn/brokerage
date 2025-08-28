"""
Test cases for portfolio serializers
"""

import pytest
from decimal import Decimal
from datetime import date
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

from portfolio.serializers import (
    PositionSerializer,
    PositionSummarySerializer,
    PositionCreateSerializer,
    PortfolioOverviewSerializer,
    PortfolioPerformanceSerializer,
    PortfolioSnapshotSerializer,
    PortfolioSnapshotSummarySerializer,
    SnapshotCreateSerializer,
    PerformanceMetricsSerializer,
    PerformanceMetricsSummarySerializer,
    MetricsCalculationRequestSerializer
)
from portfolio.tests.factories import (
    UserFactory,
    PositionFactory,
    ProfitablePositionFactory,
    PortfolioSnapshotFactory,
    PerformanceMetricsFactory,
    BenchmarkMetricsFactory
)


@pytest.mark.django_db
class TestPositionSerializers:
    """Test cases for position-related serializers"""
    
    def test_position_serializer(self):
        """Test detailed position serializer"""
        position = ProfitablePositionFactory()
        serializer = PositionSerializer(position)
        data = serializer.data
        
        # Test all required fields are present
        required_fields = [
            'position_id', 'symbol', 'instrument_type', 'name',
            'quantity', 'average_cost', 'current_price',
            'cost_basis', 'current_value', 'unrealized_gain_loss',
            'unrealized_gain_loss_percent', 'status', 'opened_at',
            'is_profitable'
        ]
        
        for field in required_fields:
            assert field in data
        
        # Test calculated fields
        assert Decimal(data['cost_basis']) == position.get_cost_basis()
        assert Decimal(data['current_value']) == position.get_current_value()
        assert Decimal(data['unrealized_gain_loss']) == position.get_unrealized_gain_loss()
        assert data['is_profitable'] == position.is_profitable()
    
    def test_position_summary_serializer(self):
        """Test lightweight position summary serializer"""
        position = PositionFactory()
        serializer = PositionSummarySerializer(position)
        data = serializer.data
        
        # Test only summary fields are present
        expected_fields = [
            'position_id', 'symbol', 'instrument_type', 'quantity',
            'current_price', 'current_value', 'unrealized_gain_loss',
            'unrealized_gain_loss_percent', 'status'
        ]
        
        assert set(data.keys()) == set(expected_fields)
    
    def test_position_create_serializer_valid_data(self):
        """Test position creation with valid data"""
        user = UserFactory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        valid_data = {
            'symbol': 'AAPL',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': '100.00',
            'average_cost': '150.50'
        }
        
        serializer = PositionCreateSerializer(
            data=valid_data,
            context={'request': request}
        )
        
        assert serializer.is_valid()
        position = serializer.save()
        
        assert position.user == user
        assert position.symbol == 'AAPL'
        assert position.quantity == Decimal('100.00')
        assert position.average_cost == Decimal('150.50')
    
    def test_position_create_serializer_validation(self):
        """Test position creation validation"""
        user = UserFactory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        # Test invalid quantity
        invalid_data = {
            'symbol': 'AAPL',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': '-10.00',
            'average_cost': '150.50'
        }
        
        serializer = PositionCreateSerializer(
            data=invalid_data,
            context={'request': request}
        )
        
        assert not serializer.is_valid()
        assert 'quantity' in serializer.errors
    
    def test_position_create_serializer_symbol_formatting(self):
        """Test symbol formatting (uppercase, trimmed)"""
        user = UserFactory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        data = {
            'symbol': '  aapl  ',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': '100.00',
            'average_cost': '150.50'
        }
        
        serializer = PositionCreateSerializer(
            data=data,
            context={'request': request}
        )
        
        assert serializer.is_valid()
        assert serializer.validated_data['symbol'] == 'AAPL'


@pytest.mark.django_db
class TestPortfolioOverviewSerializer:
    """Test portfolio overview serializer"""
    
    def test_portfolio_overview_serializer(self):
        """Test portfolio overview data serialization"""
        overview_data = {
            'total_value': Decimal('25000.00'),
            'cash_balance': Decimal('5000.00'),
            'total_portfolio_value': Decimal('30000.00'),
            'total_cost_basis': Decimal('24000.00'),
            'total_gain_loss': Decimal('1000.00'),
            'total_gain_loss_percent': Decimal('4.17'),
            'day_gain_loss': Decimal('250.00'),
            'day_gain_loss_percent': Decimal('0.84'),
            'positions_count': 3,
            'last_updated': '2024-01-15T10:30:00Z',
            'asset_allocation': {
                'stock': {'value': '20000.00', 'percentage': '80.00', 'count': 2},
                'etf': {'value': '5000.00', 'percentage': '20.00', 'count': 1}
            },
            'top_positions': [
                {'symbol': 'AAPL', 'value': '10000.00'},
                {'symbol': 'GOOGL', 'value': '8000.00'}
            ]
        }
        
        serializer = PortfolioOverviewSerializer(overview_data)
        data = serializer.data
        
        # Test all fields are serialized as strings for JSON compatibility
        assert isinstance(data['total_value'], str)
        assert isinstance(data['cash_balance'], str)
        assert isinstance(data['total_gain_loss_percent'], str)
        
        # Test structure
        assert 'asset_allocation' in data
        assert 'top_positions' in data
        assert len(data['top_positions']) == 2


@pytest.mark.django_db
class TestPortfolioPerformanceSerializer:
    """Test portfolio performance serializer"""
    
    def test_portfolio_performance_serializer(self):
        """Test portfolio performance data serialization"""
        performance_data = {
            'period': '1M',
            'period_display': '1 Month',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 1, 31),
            'total_return': Decimal('5.25'),
            'annualized_return': Decimal('12.50'),
            'volatility': Decimal('15.25'),
            'sharpe_ratio': Decimal('0.85'),
            'max_drawdown': Decimal('8.50'),
            'benchmark_return': Decimal('4.80'),
            'alpha': Decimal('0.45'),
            'beta': Decimal('1.15'),
            'outperformed_benchmark': True,
            'starting_value': Decimal('24000.00'),
            'ending_value': Decimal('25260.00'),
            'peak_value': Decimal('26000.00'),
            'is_profitable': True,
            'trading_days': 30,
            'snapshots': [
                {'date': '2024-01-01', 'total_value': '24000.00'},
                {'date': '2024-01-31', 'total_value': '25260.00'}
            ]
        }
        
        serializer = PortfolioPerformanceSerializer(performance_data)
        data = serializer.data
        
        # Test decimal fields are converted to strings
        decimal_fields = [
            'total_return', 'annualized_return', 'volatility',
            'sharpe_ratio', 'max_drawdown', 'benchmark_return',
            'alpha', 'beta', 'starting_value', 'ending_value', 'peak_value'
        ]
        
        for field in decimal_fields:
            if data[field] is not None:
                assert isinstance(data[field], str)
        
        # Test boolean and integer fields
        assert isinstance(data['outperformed_benchmark'], bool)
        assert isinstance(data['is_profitable'], bool)
        assert isinstance(data['trading_days'], int)
        
        # Test snapshots structure
        assert 'snapshots' in data
        assert len(data['snapshots']) == 2


@pytest.mark.django_db
class TestSnapshotSerializers:
    """Test snapshot-related serializers"""
    
    def test_portfolio_snapshot_serializer(self):
        """Test detailed portfolio snapshot serializer"""
        snapshot = PortfolioSnapshotFactory()
        serializer = PortfolioSnapshotSerializer(snapshot)
        data = serializer.data
        
        # Test all required fields
        required_fields = [
            'snapshot_id', 'snapshot_date', 'snapshot_time',
            'total_value', 'cash_balance', 'total_portfolio_value',
            'total_cost_basis', 'day_gain_loss', 'day_gain_loss_percent',
            'total_gain_loss', 'total_gain_loss_percent',
            'cash_allocation_percent', 'holdings_data',
            'holdings_count', 'is_profitable'
        ]
        
        for field in required_fields:
            assert field in data
        
        # Test calculated fields
        assert data['is_profitable'] == snapshot.is_profitable()
        assert Decimal(data['total_portfolio_value']) == snapshot.calculate_total_value_with_cash()
    
    def test_portfolio_snapshot_summary_serializer(self):
        """Test lightweight snapshot summary serializer"""
        snapshot = PortfolioSnapshotFactory()
        serializer = PortfolioSnapshotSummarySerializer(snapshot)
        data = serializer.data
        
        # Test only summary fields are present
        expected_fields = [
            'snapshot_date', 'total_value', 'cash_balance',
            'total_portfolio_value', 'day_gain_loss',
            'day_gain_loss_percent', 'total_gain_loss_percent'
        ]
        
        assert set(data.keys()) == set(expected_fields)
    
    def test_snapshot_create_serializer(self):
        """Test snapshot creation serializer"""
        valid_data = {
            'snapshot_date': '2024-01-15',
            'force_recreate': False
        }
        
        serializer = SnapshotCreateSerializer(data=valid_data)
        assert serializer.is_valid()
        
        # Test date validation (future date should fail)
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=1)
        
        invalid_data = {
            'snapshot_date': future_date.isoformat(),
            'force_recreate': False
        }
        
        serializer = SnapshotCreateSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'snapshot_date' in serializer.errors


@pytest.mark.django_db
class TestMetricsSerializers:
    """Test performance metrics serializers"""
    
    def test_performance_metrics_serializer(self):
        """Test detailed performance metrics serializer"""
        metrics = BenchmarkMetricsFactory()
        serializer = PerformanceMetricsSerializer(metrics)
        data = serializer.data
        
        # Test all required fields
        required_fields = [
            'metrics_id', 'period', 'period_display', 'start_date',
            'end_date', 'calculated_at', 'total_return', 'annualized_return',
            'volatility', 'sharpe_ratio', 'max_drawdown', 'benchmark_return',
            'alpha', 'beta', 'starting_value', 'ending_value',
            'outperformed_benchmark', 'is_profitable', 'risk_adjusted_return'
        ]
        
        for field in required_fields:
            assert field in data
        
        # Test calculated fields
        assert data['period_display'] == metrics.get_period_display()
        assert data['outperformed_benchmark'] == metrics.outperformed_benchmark()
        assert data['is_profitable'] == metrics.is_profitable()
    
    def test_performance_metrics_summary_serializer(self):
        """Test lightweight metrics summary serializer"""
        metrics = PerformanceMetricsFactory()
        serializer = PerformanceMetricsSummarySerializer(metrics)
        data = serializer.data
        
        # Test only summary fields are present
        expected_fields = [
            'period', 'period_display', 'total_return',
            'volatility', 'sharpe_ratio', 'is_profitable', 'calculated_at'
        ]
        
        assert set(data.keys()) == set(expected_fields)
    
    def test_metrics_calculation_request_serializer(self):
        """Test metrics calculation request serializer"""
        valid_data = {
            'period': '1M',
            'force_recalculate': True,
            'include_benchmark': True,
            'benchmark_symbol': 'SPY'
        }
        
        serializer = MetricsCalculationRequestSerializer(data=valid_data)
        assert serializer.is_valid()
        
        # Test invalid period
        invalid_data = {
            'period': 'INVALID',
            'force_recalculate': False,
            'include_benchmark': True,
            'benchmark_symbol': 'SPY'
        }
        
        serializer = MetricsCalculationRequestSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'period' in serializer.errors
    
    def test_benchmark_symbol_formatting(self):
        """Test benchmark symbol formatting"""
        data = {
            'period': '1M',
            'benchmark_symbol': '  spy  '
        }
        
        serializer = MetricsCalculationRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['benchmark_symbol'] == 'SPY'


@pytest.mark.django_db
class TestSerializerEdgeCases:
    """Test edge cases and error handling in serializers"""
    
    def test_position_serializer_with_none_values(self):
        """Test position serializer handles None values gracefully"""
        position = PositionFactory(
            last_price_update=None,
            closed_at=None,
            total_dividends=Decimal('0.00')
        )
        
        serializer = PositionSerializer(position)
        data = serializer.data
        
        assert data['last_price_update'] is None
        assert data['closed_at'] is None
        assert data['total_dividends'] == '0.00'
    
    def test_performance_serializer_with_null_metrics(self):
        """Test performance serializer handles null metric values"""
        metrics = PerformanceMetricsFactory(
            annualized_return=None,
            volatility=None,
            sharpe_ratio=None,
            benchmark_return=None,
            alpha=None,
            beta=None
        )
        
        serializer = PerformanceMetricsSerializer(metrics)
        data = serializer.data
        
        null_fields = [
            'annualized_return', 'volatility', 'sharpe_ratio',
            'benchmark_return', 'alpha', 'beta'
        ]
        
        for field in null_fields:
            assert data[field] is None
    
    def test_decimal_to_string_conversion(self):
        """Test consistent decimal to string conversion"""
        snapshot = PortfolioSnapshotFactory(
            total_value=Decimal('12345.6789'),
            cash_balance=Decimal('1000.0000'),
            day_gain_loss_percent=Decimal('0.0000')
        )
        
        serializer = PortfolioSnapshotSerializer(snapshot)
        data = serializer.data
        
        # Test precision is maintained in string conversion
        assert data['total_value'] == '12345.68'
        assert data['cash_balance'] == '1000.00'
        assert data['day_gain_loss_percent'] == '0.0000'
    
    def test_serializer_context_handling(self):
        """Test serializers properly handle context"""
        user = UserFactory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user
        
        data = {
            'symbol': 'TEST',
            'instrument_type': 'stock',
            'name': 'Test Corp',
            'quantity': '50.00',
            'average_cost': '100.00'
        }
        
        # Test with context
        serializer = PositionCreateSerializer(
            data=data,
            context={'request': request}
        )
        assert serializer.is_valid()
        
        position = serializer.save()
        assert position.user == user
        
        # Test without context should fail
        serializer_no_context = PositionCreateSerializer(data=data)
        assert serializer_no_context.is_valid()
        
        with pytest.raises(ValueError):  # Should fail on save without user context
            serializer_no_context.save()
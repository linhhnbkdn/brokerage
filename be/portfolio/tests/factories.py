"""
Test factories for portfolio models
"""

import factory
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth.models import User
from portfolio.models import Position, PortfolioSnapshot, PerformanceMetrics
from banking.models import UserBalance


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model"""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class UserBalanceFactory(factory.django.DjangoModelFactory):
    """Factory for UserBalance model"""
    
    class Meta:
        model = UserBalance
    
    user = factory.SubFactory(UserFactory)
    available_balance = factory.LazyFunction(lambda: Decimal('10000.00'))
    pending_balance = factory.LazyFunction(lambda: Decimal('0.00'))
    total_balance = factory.LazyAttribute(lambda obj: obj.available_balance + obj.pending_balance)


class PositionFactory(factory.django.DjangoModelFactory):
    """Factory for Position model"""
    
    class Meta:
        model = Position
    
    user = factory.SubFactory(UserFactory)
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY'])
    instrument_type = factory.Iterator(['stock', 'etf', 'bond'])
    name = factory.LazyAttribute(lambda obj: f'{obj.symbol} Corporation')
    quantity = factory.LazyFunction(lambda: Decimal('100.00'))
    average_cost = factory.LazyFunction(lambda: Decimal('150.00'))
    current_price = factory.LazyFunction(lambda: Decimal('155.00'))
    status = 'active'


class ClosedPositionFactory(PositionFactory):
    """Factory for closed positions"""
    
    status = 'closed'
    closed_at = factory.Faker('date_time_this_year')


class PortfolioSnapshotFactory(factory.django.DjangoModelFactory):
    """Factory for PortfolioSnapshot model"""
    
    class Meta:
        model = PortfolioSnapshot
    
    user = factory.SubFactory(UserFactory)
    snapshot_date = factory.LazyFunction(lambda: date.today())
    total_value = factory.LazyFunction(lambda: Decimal('25000.00'))
    cash_balance = factory.LazyFunction(lambda: Decimal('5000.00'))
    total_cost_basis = factory.LazyFunction(lambda: Decimal('24000.00'))
    day_gain_loss = factory.LazyFunction(lambda: Decimal('250.00'))
    day_gain_loss_percent = factory.LazyFunction(lambda: Decimal('1.02'))
    total_gain_loss = factory.LazyFunction(lambda: Decimal('1000.00'))
    total_gain_loss_percent = factory.LazyFunction(lambda: Decimal('4.17'))
    holdings_data = factory.LazyFunction(lambda: {
        'positions': [],
        'position_count': 0,
        'asset_allocation': {}
    })


class HistoricalSnapshotFactory(PortfolioSnapshotFactory):
    """Factory for historical snapshots"""
    
    @factory.lazy_attribute
    def snapshot_date(self):
        return date.today() - timedelta(days=factory.Faker('random_int', min=1, max=365).generate())


class PerformanceMetricsFactory(factory.django.DjangoModelFactory):
    """Factory for PerformanceMetrics model"""
    
    class Meta:
        model = PerformanceMetrics
    
    user = factory.SubFactory(UserFactory)
    period = factory.Iterator(['1M', '3M', '6M', '1Y'])
    start_date = factory.LazyFunction(lambda: date.today() - timedelta(days=30))
    end_date = factory.LazyFunction(lambda: date.today())
    total_return = factory.LazyFunction(lambda: Decimal('5.25'))
    annualized_return = factory.LazyFunction(lambda: Decimal('12.50'))
    volatility = factory.LazyFunction(lambda: Decimal('15.25'))
    sharpe_ratio = factory.LazyFunction(lambda: Decimal('0.85'))
    max_drawdown = factory.LazyFunction(lambda: Decimal('8.50'))
    starting_value = factory.LazyFunction(lambda: Decimal('24000.00'))
    ending_value = factory.LazyFunction(lambda: Decimal('25260.00'))
    peak_value = factory.LazyFunction(lambda: Decimal('26000.00'))
    trading_days = 30


class BenchmarkMetricsFactory(PerformanceMetricsFactory):
    """Factory with benchmark data"""
    
    benchmark_return = factory.LazyFunction(lambda: Decimal('4.80'))
    alpha = factory.LazyFunction(lambda: Decimal('0.45'))
    beta = factory.LazyFunction(lambda: Decimal('1.15'))


# Trait mixins for common scenarios
class ProfitablePositionTrait:
    """Trait for profitable positions"""
    current_price = factory.LazyAttribute(lambda obj: obj.average_cost * Decimal('1.20'))


class LosingPositionTrait:
    """Trait for losing positions"""
    current_price = factory.LazyAttribute(lambda obj: obj.average_cost * Decimal('0.80'))


class HighVolumePositionTrait:
    """Trait for high volume positions"""
    quantity = factory.LazyFunction(lambda: Decimal('1000.00'))


class CryptoPositionTrait:
    """Trait for crypto positions"""
    symbol = factory.Iterator(['BTC', 'ETH', 'ADA', 'DOT'])
    instrument_type = 'crypto'
    average_cost = factory.LazyFunction(lambda: Decimal('45000.00'))
    current_price = factory.LazyFunction(lambda: Decimal('47000.00'))


class ETFPositionTrait:
    """Trait for ETF positions"""
    symbol = factory.Iterator(['SPY', 'QQQ', 'VTI', 'VOO'])
    instrument_type = 'etf'
    average_cost = factory.LazyFunction(lambda: Decimal('400.00'))
    current_price = factory.LazyFunction(lambda: Decimal('405.00'))


# Factory with traits
class ProfitablePositionFactory(PositionFactory, ProfitablePositionTrait):
    pass


class LosingPositionFactory(PositionFactory, LosingPositionTrait):
    pass


class CryptoPositionFactory(PositionFactory, CryptoPositionTrait):
    pass


class ETFPositionFactory(PositionFactory, ETFPositionTrait):
    pass


# Batch factories for creating multiple related objects
def create_user_with_portfolio(user_kwargs=None, position_count=3, snapshot_count=30):
    """Create a user with complete portfolio data"""
    user_kwargs = user_kwargs or {}
    user = UserFactory(**user_kwargs)
    
    # Create user balance
    UserBalanceFactory(user=user)
    
    # Create positions
    positions = []
    for i in range(position_count):
        if i == 0:
            position = ProfitablePositionFactory(user=user)
        elif i == 1:
            position = LosingPositionFactory(user=user)
        else:
            position = PositionFactory(user=user)
        positions.append(position)
    
    # Create historical snapshots
    snapshots = []
    for i in range(snapshot_count):
        snapshot_date = date.today() - timedelta(days=snapshot_count - i - 1)
        base_value = Decimal('24000.00') + (i * Decimal('50.00'))
        
        snapshot = PortfolioSnapshotFactory(
            user=user,
            snapshot_date=snapshot_date,
            total_value=base_value,
            total_cost_basis=Decimal('24000.00'),
            total_gain_loss=base_value - Decimal('24000.00'),
            holdings_data={
                'positions': [pos.get_position_summary() for pos in positions],
                'position_count': len(positions),
                'asset_allocation': _calculate_mock_allocation(positions)
            }
        )
        snapshots.append(snapshot)
    
    # Create performance metrics
    metrics = []
    for period in ['1M', '3M', '6M', '1Y']:
        metric = PerformanceMetricsFactory(user=user, period=period)
        metrics.append(metric)
    
    return {
        'user': user,
        'positions': positions,
        'snapshots': snapshots,
        'metrics': metrics
    }


def _calculate_mock_allocation(positions):
    """Calculate mock asset allocation for test data"""
    allocation = {}
    total_value = sum(pos.get_current_value() for pos in positions)
    
    if total_value == 0:
        return allocation
    
    for position in positions:
        instrument_type = position.instrument_type
        position_value = position.get_current_value()
        
        if instrument_type not in allocation:
            allocation[instrument_type] = {
                'value': '0.00',
                'count': 0,
                'percentage': '0.00'
            }
        
        current_value = Decimal(allocation[instrument_type]['value']) + position_value
        allocation[instrument_type]['value'] = str(current_value)
        allocation[instrument_type]['count'] += 1
    
    # Calculate percentages
    for instrument_type in allocation:
        value = Decimal(allocation[instrument_type]['value'])
        percentage = (value / total_value) * 100 if total_value > 0 else Decimal('0.00')
        allocation[instrument_type]['percentage'] = str(percentage)
    
    return allocation
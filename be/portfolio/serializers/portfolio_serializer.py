"""
Serializers for portfolio overview and performance data
"""

from rest_framework import serializers
from decimal import Decimal
from portfolio.models import Position
from banking.models import UserBalance


class PortfolioOverviewSerializer(serializers.Serializer):
    """Portfolio overview data serializer"""
    
    total_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    cash_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_portfolio_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_cost_basis = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_gain_loss = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gain_loss_percent = serializers.DecimalField(max_digits=8, decimal_places=4)
    day_gain_loss = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    day_gain_loss_percent = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    positions_count = serializers.IntegerField()
    last_updated = serializers.DateTimeField()
    
    # Asset allocation
    asset_allocation = serializers.DictField(child=serializers.DictField(), allow_null=True)
    
    # Top positions (optional)
    top_positions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_null=True
    )

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        # Ensure decimal values are strings for JSON serialization
        decimal_fields = [
            'total_value', 'cash_balance', 'total_portfolio_value',
            'total_cost_basis', 'total_gain_loss', 'total_gain_loss_percent',
            'day_gain_loss', 'day_gain_loss_percent'
        ]
        
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation


class PortfolioPerformanceSerializer(serializers.Serializer):
    """Portfolio performance data for charts and analysis"""
    
    period = serializers.CharField()
    period_display = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    # Performance metrics
    total_return = serializers.DecimalField(max_digits=8, decimal_places=4)
    annualized_return = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    volatility = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    sharpe_ratio = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    max_drawdown = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    
    # Benchmark comparison
    benchmark_return = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    alpha = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    beta = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    outperformed_benchmark = serializers.BooleanField()
    
    # Portfolio values
    starting_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    ending_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    peak_value = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    
    # Time series data
    snapshots = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    
    # Additional context
    is_profitable = serializers.BooleanField()
    trading_days = serializers.IntegerField(allow_null=True)

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        # Ensure decimal values are strings for JSON serialization
        decimal_fields = [
            'total_return', 'annualized_return', 'volatility', 'sharpe_ratio',
            'max_drawdown', 'benchmark_return', 'alpha', 'beta',
            'starting_value', 'ending_value', 'peak_value'
        ]
        
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation


class AssetAllocationSerializer(serializers.Serializer):
    """Asset allocation breakdown serializer"""
    
    instrument_type = serializers.CharField()
    value = serializers.DecimalField(max_digits=18, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    count = serializers.IntegerField()
    positions = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        representation['value'] = str(representation['value'])
        representation['percentage'] = str(representation['percentage'])
        return representation


class PortfolioSummarySerializer(serializers.Serializer):
    """Quick portfolio summary for dashboard widgets"""
    
    total_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    day_change = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    day_change_percent = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    positions_count = serializers.IntegerField()
    cash_balance = serializers.DecimalField(max_digits=15, decimal_places=2)

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        decimal_fields = ['total_value', 'day_change', 'day_change_percent', 'cash_balance']
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation
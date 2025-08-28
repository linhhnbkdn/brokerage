"""
Serializers for PerformanceMetrics model
"""

from rest_framework import serializers
from portfolio.models import PerformanceMetrics


class PerformanceMetricsSerializer(serializers.ModelSerializer):
    """Performance metrics serializer"""
    
    period_display = serializers.SerializerMethodField()
    outperformed_benchmark = serializers.SerializerMethodField()
    is_profitable = serializers.SerializerMethodField()
    risk_adjusted_return = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceMetrics
        fields = [
            'metrics_id',
            'period',
            'period_display',
            'start_date',
            'end_date',
            'calculated_at',
            'total_return',
            'annualized_return',
            'time_weighted_return',
            'volatility',
            'sharpe_ratio',
            'max_drawdown',
            'benchmark_return',
            'alpha',
            'beta',
            'starting_value',
            'ending_value',
            'peak_value',
            'trading_days',
            'number_of_trades',
            'outperformed_benchmark',
            'is_profitable',
            'risk_adjusted_return',
            'calculation_notes',
        ]
        read_only_fields = [
            'metrics_id',
            'calculated_at',
            'period_display',
            'outperformed_benchmark',
            'is_profitable',
            'risk_adjusted_return',
        ]

    def get_period_display(self, obj):
        return obj.get_period_display()

    def get_outperformed_benchmark(self, obj):
        return obj.outperformed_benchmark()

    def get_is_profitable(self, obj):
        return obj.is_profitable()

    def get_risk_adjusted_return(self, obj):
        return str(obj.get_risk_adjusted_return())

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        # Ensure decimal values are strings for JSON serialization
        decimal_fields = [
            'total_return', 'annualized_return', 'time_weighted_return',
            'volatility', 'sharpe_ratio', 'max_drawdown',
            'benchmark_return', 'alpha', 'beta',
            'starting_value', 'ending_value', 'peak_value'
        ]
        
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation


class PerformanceMetricsSummarySerializer(serializers.ModelSerializer):
    """Lightweight metrics serializer for overview displays"""
    
    period_display = serializers.SerializerMethodField()
    is_profitable = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceMetrics
        fields = [
            'period',
            'period_display',
            'total_return',
            'volatility',
            'sharpe_ratio',
            'is_profitable',
            'calculated_at',
        ]

    def get_period_display(self, obj):
        return obj.get_period_display()

    def get_is_profitable(self, obj):
        return obj.is_profitable()

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        decimal_fields = ['total_return', 'volatility', 'sharpe_ratio']
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation


class MetricsCalculationRequestSerializer(serializers.Serializer):
    """Serializer for requesting metrics calculation"""
    
    period = serializers.ChoiceField(
        choices=PerformanceMetrics.PERIOD_CHOICES,
        required=True
    )
    force_recalculate = serializers.BooleanField(default=False)
    include_benchmark = serializers.BooleanField(default=True)
    benchmark_symbol = serializers.CharField(
        max_length=10,
        default='SPY',
        help_text="Benchmark symbol (default: SPY for S&P 500)"
    )

    def validate_benchmark_symbol(self, value):
        """Validate benchmark symbol format"""
        if value:
            return value.upper().strip()
        return value
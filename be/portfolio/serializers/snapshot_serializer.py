"""
Serializers for PortfolioSnapshot model
"""

from rest_framework import serializers
from portfolio.models import PortfolioSnapshot


class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    """Portfolio snapshot serializer"""
    
    total_portfolio_value = serializers.SerializerMethodField()
    cash_allocation_percent = serializers.SerializerMethodField()
    is_profitable = serializers.SerializerMethodField()
    holdings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioSnapshot
        fields = [
            'snapshot_id',
            'snapshot_date',
            'snapshot_time',
            'total_value',
            'cash_balance',
            'total_portfolio_value',
            'total_cost_basis',
            'day_gain_loss',
            'day_gain_loss_percent',
            'total_gain_loss',
            'total_gain_loss_percent',
            'cash_allocation_percent',
            'holdings_data',
            'market_indexes',
            'holdings_count',
            'is_profitable',
        ]
        read_only_fields = [
            'snapshot_id',
            'snapshot_time',
            'total_portfolio_value',
            'cash_allocation_percent',
            'holdings_count',
            'is_profitable',
        ]

    def get_total_portfolio_value(self, obj):
        return str(obj.calculate_total_value_with_cash())

    def get_cash_allocation_percent(self, obj):
        return str(obj.get_cash_allocation_percent())

    def get_is_profitable(self, obj):
        return obj.is_profitable()

    def get_holdings_count(self, obj):
        return len(obj.holdings_data.get('positions', []))

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        # Ensure decimal values are strings for JSON serialization
        decimal_fields = [
            'total_value', 'cash_balance', 'total_cost_basis',
            'day_gain_loss', 'day_gain_loss_percent',
            'total_gain_loss', 'total_gain_loss_percent'
        ]
        
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation


class PortfolioSnapshotSummarySerializer(serializers.ModelSerializer):
    """Lightweight snapshot serializer for time series data"""
    
    total_portfolio_value = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioSnapshot
        fields = [
            'snapshot_date',
            'total_value',
            'cash_balance',
            'total_portfolio_value',
            'day_gain_loss',
            'day_gain_loss_percent',
            'total_gain_loss_percent',
        ]

    def get_total_portfolio_value(self, obj):
        return str(obj.calculate_total_value_with_cash())

    def to_representation(self, instance):
        """Convert data to proper format"""
        representation = super().to_representation(instance)
        
        decimal_fields = [
            'total_value', 'cash_balance', 'day_gain_loss',
            'day_gain_loss_percent', 'total_gain_loss_percent'
        ]
        
        for field in decimal_fields:
            if representation[field] is not None:
                representation[field] = str(representation[field])
        
        return representation


class SnapshotCreateSerializer(serializers.Serializer):
    """Serializer for creating snapshots via API"""
    
    snapshot_date = serializers.DateField(required=False)
    force_recreate = serializers.BooleanField(default=False)
    
    def validate_snapshot_date(self, value):
        """Validate snapshot date is not in the future"""
        from datetime import date
        
        if value and value > date.today():
            raise serializers.ValidationError("Snapshot date cannot be in the future")
        return value
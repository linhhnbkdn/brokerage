"""
Serializers for Position model
"""

from rest_framework import serializers
from portfolio.models import Position


class PositionSerializer(serializers.ModelSerializer):
    """Detailed Position serializer"""
    
    cost_basis = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    unrealized_gain_loss = serializers.SerializerMethodField()
    unrealized_gain_loss_percent = serializers.SerializerMethodField()
    is_profitable = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'position_id',
            'symbol',
            'instrument_type',
            'name',
            'quantity',
            'average_cost',
            'current_price',
            'cost_basis',
            'current_value',
            'unrealized_gain_loss',
            'unrealized_gain_loss_percent',
            'status',
            'opened_at',
            'closed_at',
            'last_price_update',
            'total_dividends',
            'is_profitable',
        ]
        read_only_fields = [
            'position_id',
            'opened_at',
            'closed_at',
            'last_price_update',
            'cost_basis',
            'current_value',
            'unrealized_gain_loss',
            'unrealized_gain_loss_percent',
            'is_profitable',
        ]

    def get_cost_basis(self, obj):
        return str(obj.get_cost_basis())

    def get_current_value(self, obj):
        return str(obj.get_current_value())

    def get_unrealized_gain_loss(self, obj):
        return str(obj.get_unrealized_gain_loss())

    def get_unrealized_gain_loss_percent(self, obj):
        return str(obj.get_unrealized_gain_loss_percent())

    def get_is_profitable(self, obj):
        return obj.is_profitable()


class PositionSummarySerializer(serializers.ModelSerializer):
    """Lightweight Position serializer for lists"""
    
    current_value = serializers.SerializerMethodField()
    unrealized_gain_loss = serializers.SerializerMethodField()
    unrealized_gain_loss_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'position_id',
            'symbol',
            'instrument_type',
            'quantity',
            'current_price',
            'current_value',
            'unrealized_gain_loss',
            'unrealized_gain_loss_percent',
            'status',
        ]

    def get_current_value(self, obj):
        return str(obj.get_current_value())

    def get_unrealized_gain_loss(self, obj):
        return str(obj.get_unrealized_gain_loss())

    def get_unrealized_gain_loss_percent(self, obj):
        return str(obj.get_unrealized_gain_loss_percent())


class PositionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new positions"""
    
    class Meta:
        model = Position
        fields = [
            'symbol',
            'instrument_type', 
            'name',
            'quantity',
            'average_cost',
        ]

    def validate_symbol(self, value):
        """Validate symbol format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Symbol is required")
        return value.upper().strip()

    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate_average_cost(self, value):
        """Validate average cost is positive"""
        if value <= 0:
            raise serializers.ValidationError("Average cost must be greater than 0")
        return value

    def create(self, validated_data):
        """Create position with current user"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
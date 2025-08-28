"""
Market data serializers
"""

from rest_framework import serializers
from exchange.models import MarketDataSnapshot


class MarketDataSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for MarketDataSnapshot"""
    
    spread = serializers.SerializerMethodField()
    spread_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketDataSnapshot
        fields = [
            'id', 'symbol', 'price', 'change', 'change_percent',
            'volume', 'bid', 'ask', 'spread', 'spread_percent',
            'timestamp', 'exchange', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_spread(self, obj):
        """Get bid-ask spread"""
        return float(obj.get_spread())
    
    def get_spread_percent(self, obj):
        """Get bid-ask spread percentage"""
        return float(obj.get_spread_percent())
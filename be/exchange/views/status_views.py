"""
Status views for exchange app
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from exchange.models import MarketDataSnapshot, Order, SymbolSubscription, WebSocketConnection
from exchange.services import ExchangeSimulator, RedisPubSubService


class ExchangeStatusView(APIView):
    """View for exchange system status"""
    
    permission_classes = []  # Public endpoint
    
    def get(self, request):
        """Get exchange system status"""
        try:
            # Database counts
            market_data_count = MarketDataSnapshot.objects.count()
            orders_count = Order.objects.count()
            active_subscriptions = SymbolSubscription.objects.filter(is_active=True).count()
            active_connections = WebSocketConnection.objects.filter(
                status__in=['connected', 'authenticated']
            ).count()
            
            # System status
            exchange_settings = settings.EXCHANGE_SETTINGS
            simulator = ExchangeSimulator()
            pubsub_service = RedisPubSubService()
            
            # Redis health check
            redis_status = pubsub_service.health_check()
            
            status_data = {
                'status': 'healthy',
                'timestamp': '2024-01-15T10:30:00Z',
                'database': {
                    'market_data_snapshots': market_data_count,
                    'orders': orders_count,
                    'active_subscriptions': active_subscriptions,
                    'active_connections': active_connections
                },
                'exchange': {
                    'simulator_enabled': exchange_settings.get('ENABLE_MARKET_SIMULATOR', True),
                    'price_update_interval': exchange_settings.get('PRICE_UPDATE_INTERVAL', 2),
                    'max_subscriptions_per_user': exchange_settings.get('MAX_SUBSCRIPTIONS_PER_USER', 50),
                    'data_retention_hours': exchange_settings.get('MARKET_DATA_RETENTION_HOURS', 24)
                },
                'services': {
                    'redis': redis_status,
                    'simulator': simulator.get_simulation_status(),
                    'websocket_channels': pubsub_service.get_channel_stats()
                }
            }
            
            return Response(status_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Error retrieving status: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
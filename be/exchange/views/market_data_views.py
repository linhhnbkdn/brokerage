"""
Market data API views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from exchange.models import MarketDataSnapshot
from exchange.serializers import MarketDataSnapshotSerializer
from exchange.services import MarketDataService


class MarketDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for market data operations"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = MarketDataSnapshotSerializer
    
    def get_queryset(self):
        """Get market data queryset with filtering"""
        queryset = MarketDataSnapshot.objects.all()
        
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol=symbol.upper())
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def current_prices(self, request):
        """Get current prices for symbols"""
        symbols = request.query_params.get('symbols', '').split(',')
        symbols = [s.strip().upper() for s in symbols if s.strip()]
        
        if not symbols:
            return Response(
                {'error': 'No symbols provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = MarketDataService()
        prices = {}
        
        for symbol in symbols:
            latest_data = service.get_latest_market_data(symbol)
            if latest_data:
                prices[symbol] = MarketDataSnapshotSerializer(latest_data).data
            else:
                prices[symbol] = None
        
        return Response(prices)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get market statistics for a symbol"""
        symbol = request.query_params.get('symbol')
        
        if not symbol:
            return Response(
                {'error': 'Symbol parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = MarketDataService()
        stats = service.get_market_statistics(symbol.upper())
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def supported_symbols(self, request):
        """Get list of supported symbols"""
        service = MarketDataService()
        symbols = service.get_supported_symbols()
        
        return Response({'symbols': symbols})
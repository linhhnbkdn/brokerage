"""
URL patterns for exchange app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from exchange.views import (
    MarketDataViewSet, OrderViewSet, SubscriptionViewSet,
    ExchangeStatusView, MarketEventViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'market-data', MarketDataViewSet, basename='market-data')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')
router.register(r'events', MarketEventViewSet, basename='events')

app_name = 'exchange'

urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
    
    # Status endpoint
    path('api/v1/status/', ExchangeStatusView.as_view(), name='exchange-status'),
    
    # WebSocket endpoints are handled by routing.py
]
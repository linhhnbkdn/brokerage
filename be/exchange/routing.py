"""
WebSocket routing for exchange app
"""

from django.urls import re_path
from .consumers import MarketDataConsumer

websocket_urlpatterns = [
    re_path(r'ws/market-data/$', MarketDataConsumer.as_asgi()),
]
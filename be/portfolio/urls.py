"""
Portfolio app URL configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioOverviewViewSet,
    PortfolioPerformanceViewSet,
    PositionViewSet,
    PortfolioSnapshotViewSet,
    PerformanceMetricsViewSet,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'positions', PositionViewSet, basename='positions')
router.register(r'snapshots', PortfolioSnapshotViewSet, basename='snapshots')
router.register(r'metrics', PerformanceMetricsViewSet, basename='metrics')

app_name = 'portfolio'

urlpatterns = [
    # Portfolio overview endpoints (custom viewsets without model CRUD)
    path('overview/', PortfolioOverviewViewSet.as_view({'get': 'overview'}), name='overview'),
    
    # Portfolio performance endpoints
    path('performance/', PortfolioPerformanceViewSet.as_view({'get': 'performance'}), name='performance'),
    path('performance/summary/', PortfolioPerformanceViewSet.as_view({'get': 'summary'}), name='performance-summary'),
    
    # Include router URLs for model-based viewsets
    path('', include(router.urls)),
]
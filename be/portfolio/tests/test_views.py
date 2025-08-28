"""
Test cases for portfolio API views
"""

import pytest
import json
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from authentication.services.jwt_token_service import JWTTokenService
from portfolio.models import Position, PortfolioSnapshot, PerformanceMetrics
from portfolio.tests.factories import (
    UserFactory,
    UserBalanceFactory,
    PositionFactory,
    ProfitablePositionFactory,
    LosingPositionFactory,
    PortfolioSnapshotFactory,
    PerformanceMetricsFactory,
    create_user_with_portfolio
)


class BasePortfolioTestCase(APITestCase):
    """Base test case with authentication helpers"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.user_balance = UserBalanceFactory(user=self.user)
        self.client = APIClient()
        
        # Generate JWT token for authentication
        self.jwt_service = JWTTokenService()
        self.access_token = self.jwt_service.generate_access_token(self.user.id)
        
    def authenticate(self):
        """Authenticate API client with JWT token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def create_portfolio_data(self, position_count=3, snapshot_count=30):
        """Create complete portfolio data for user"""
        return create_user_with_portfolio(
            user_kwargs={'id': self.user.id},
            position_count=position_count,
            snapshot_count=snapshot_count
        )


@pytest.mark.django_db
class TestPortfolioOverviewViews(BasePortfolioTestCase):
    """Test portfolio overview API endpoints"""
    
    def test_portfolio_overview_success(self):
        """Test successful portfolio overview retrieval"""
        self.authenticate()
        
        # Create test positions
        positions = [
            ProfitablePositionFactory(user=self.user, symbol='AAPL'),
            LosingPositionFactory(user=self.user, symbol='GOOGL'),
            PositionFactory(user=self.user, symbol='MSFT')
        ]
        
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'total_value' in data
        assert 'cash_balance' in data
        assert 'total_portfolio_value' in data
        assert 'positions_count' in data
        assert data['positions_count'] == 3
        assert 'asset_allocation' in data
        assert 'last_updated' in data
    
    def test_portfolio_overview_no_positions(self):
        """Test portfolio overview with no positions"""
        self.authenticate()
        
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert data['positions_count'] == 0
        assert Decimal(data['total_value']) == Decimal('0.00')
        assert Decimal(data['cash_balance']) == self.user_balance.available_balance
    
    def test_portfolio_overview_unauthorized(self):
        """Test portfolio overview without authentication"""
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_portfolio_overview_with_daily_performance(self):
        """Test overview includes daily performance comparison"""
        self.authenticate()
        
        # Create position and yesterday's snapshot
        PositionFactory(user=self.user)
        yesterday = date.today() - timedelta(days=1)
        PortfolioSnapshotFactory(
            user=self.user,
            snapshot_date=yesterday,
            total_value=Decimal('10000.00'),
            cash_balance=Decimal('2000.00')
        )
        
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'day_gain_loss' in data
        assert 'day_gain_loss_percent' in data
        # Values might be None if no comparison available
    
    @patch('portfolio.views.portfolio_views.PortfolioOverviewViewSet._calculate_asset_allocation')
    def test_portfolio_overview_asset_allocation_calculation(self, mock_allocation):
        """Test asset allocation calculation is called"""
        self.authenticate()
        
        mock_allocation.return_value = {
            'stock': {'value': '10000.00', 'percentage': '100.00', 'count': 1}
        }
        
        PositionFactory(user=self.user, instrument_type='stock')
        
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert mock_allocation.called
        
        data = response.json()['data']
        assert 'asset_allocation' in data
        assert 'stock' in data['asset_allocation']


@pytest.mark.django_db
class TestPortfolioPerformanceViews(BasePortfolioTestCase):
    """Test portfolio performance API endpoints"""
    
    def test_performance_with_valid_period(self):
        """Test performance endpoint with valid period"""
        self.authenticate()
        
        # Create portfolio data
        portfolio_data = create_user_with_portfolio(
            user_kwargs={'email': self.user.email, 'username': self.user.username},
            position_count=2,
            snapshot_count=30
        )
        
        # Update user reference
        self.user = portfolio_data['user']
        self.authenticate()
        
        url = reverse('portfolio:performance')
        response = self.client.get(url, {'period': '1M'})
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert data['period'] == '1M'
        assert 'total_return' in data
        assert 'snapshots' in data
        assert isinstance(data['snapshots'], list)
    
    def test_performance_invalid_period(self):
        """Test performance endpoint with invalid period"""
        self.authenticate()
        
        url = reverse('portfolio:performance')
        response = self.client.get(url, {'period': 'INVALID'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid period' in response.json()['message']
    
    def test_performance_no_data(self):
        """Test performance endpoint with no snapshot data"""
        self.authenticate()
        
        url = reverse('portfolio:performance')
        response = self.client.get(url, {'period': '1M'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'No portfolio data available' in response.json()['message']
    
    def test_performance_summary(self):
        """Test performance summary endpoint"""
        self.authenticate()
        
        # Create recent snapshot and metrics
        PortfolioSnapshotFactory(user=self.user, snapshot_date=date.today())
        PerformanceMetricsFactory(user=self.user, period='1M')
        PerformanceMetricsFactory(user=self.user, period='3M')
        
        url = reverse('portfolio:performance-summary')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'current_value' in data
        assert 'recent_metrics' in data
        assert len(data['recent_metrics']) == 2
    
    @patch('portfolio.models.PerformanceMetrics.calculate_metrics')
    def test_performance_metrics_calculation(self, mock_calculate):
        """Test that metrics are calculated when not exist"""
        self.authenticate()
        
        # Create snapshots but no metrics
        snapshots = [
            PortfolioSnapshotFactory(user=self.user, snapshot_date=date.today() - timedelta(days=i))
            for i in range(5)
        ]
        
        mock_metrics = MagicMock()
        mock_metrics.total_return = Decimal('5.25')
        mock_metrics.volatility = Decimal('15.25')
        mock_calculate.return_value = mock_metrics
        
        url = reverse('portfolio:performance')
        response = self.client.get(url, {'period': '1M'})
        
        assert response.status_code == status.HTTP_200_OK
        assert mock_calculate.called


@pytest.mark.django_db
class TestPositionViews(BasePortfolioTestCase):
    """Test position CRUD API endpoints"""
    
    def test_list_positions(self):
        """Test listing user positions"""
        self.authenticate()
        
        # Create positions
        positions = [
            PositionFactory(user=self.user, symbol='AAPL', status='active'),
            PositionFactory(user=self.user, symbol='GOOGL', status='active'),
            PositionFactory(user=self.user, symbol='MSFT', status='closed')
        ]
        
        url = reverse('portfolio:positions-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'positions' in data
        assert 'summary' in data
        assert len(data['positions']) == 2  # Only active positions by default
        
        # Test status filtering
        response = self.client.get(url, {'status': 'closed'})
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert len(data['positions']) == 1
    
    def test_create_position(self):
        """Test creating a new position"""
        self.authenticate()
        
        position_data = {
            'symbol': 'AAPL',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': '100.00',
            'average_cost': '150.50'
        }
        
        url = reverse('portfolio:positions-list')
        response = self.client.post(url, position_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()['data']
        assert data['symbol'] == 'AAPL'
        assert data['quantity'] == '100.00'
        assert data['average_cost'] == '150.50'
        
        # Verify position was created in database
        position = Position.objects.get(user=self.user, symbol='AAPL')
        assert position.quantity == Decimal('100.00')
    
    def test_create_duplicate_position(self):
        """Test creating duplicate active position fails"""
        self.authenticate()
        
        # Create existing position
        PositionFactory(user=self.user, symbol='AAPL', status='active')
        
        position_data = {
            'symbol': 'AAPL',
            'instrument_type': 'stock',
            'name': 'Apple Inc.',
            'quantity': '100.00',
            'average_cost': '150.50'
        }
        
        url = reverse('portfolio:positions-list')
        response = self.client.post(url, position_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already exists' in response.json()['message']
    
    def test_retrieve_position(self):
        """Test retrieving specific position"""
        self.authenticate()
        
        position = PositionFactory(user=self.user, symbol='AAPL')
        
        url = reverse('portfolio:positions-detail', kwargs={'position_id': position.position_id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert data['symbol'] == 'AAPL'
        assert data['position_id'] == str(position.position_id)
    
    def test_update_position(self):
        """Test updating existing position"""
        self.authenticate()
        
        position = PositionFactory(user=self.user, quantity=Decimal('100'))
        
        update_data = {
            'quantity': '150.00',
            'current_price': '160.00'
        }
        
        url = reverse('portfolio:positions-detail', kwargs={'position_id': position.position_id})
        response = self.client.put(url, update_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify update in database
        position.refresh_from_db()
        assert position.quantity == Decimal('150.00')
        assert position.current_price == Decimal('160.00')
    
    def test_close_position(self):
        """Test closing (deleting) a position"""
        self.authenticate()
        
        position = PositionFactory(user=self.user, status='active')
        
        url = reverse('portfolio:positions-detail', kwargs={'position_id': position.position_id})
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify position was marked as closed
        position.refresh_from_db()
        assert position.status == 'closed'
    
    def test_update_position_price(self):
        """Test updating position current price"""
        self.authenticate()
        
        position = PositionFactory(user=self.user, current_price=Decimal('150.00'))
        
        price_data = {'current_price': '165.50'}
        
        url = reverse('portfolio:positions-update-price', kwargs={'position_id': position.position_id})
        response = self.client.post(url, price_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify price update
        position.refresh_from_db()
        assert position.current_price == Decimal('165.50')
        assert position.last_price_update is not None
    
    def test_position_performance(self):
        """Test individual position performance endpoint"""
        self.authenticate()
        
        position = ProfitablePositionFactory(user=self.user)
        
        url = reverse('portfolio:positions-performance', kwargs={'position_id': position.position_id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert data['position_id'] == str(position.position_id)
        assert 'current_performance' in data
        assert 'is_profitable' in data['current_performance']
    
    def test_portfolio_allocation(self):
        """Test portfolio allocation endpoint"""
        self.authenticate()
        
        # Create positions with different instrument types
        PositionFactory(user=self.user, instrument_type='stock', symbol='AAPL')
        PositionFactory(user=self.user, instrument_type='stock', symbol='GOOGL')
        PositionFactory(user=self.user, instrument_type='etf', symbol='SPY')
        
        url = reverse('portfolio:positions-allocation')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'total_value' in data
        assert 'allocation' in data
        assert len(data['allocation']) == 2  # stock and etf
        
        # Verify allocation structure
        for allocation in data['allocation']:
            assert 'instrument_type' in allocation
            assert 'value' in allocation
            assert 'percentage' in allocation
            assert 'count' in allocation
            assert 'positions' in allocation


@pytest.mark.django_db
class TestSnapshotViews(BasePortfolioTestCase):
    """Test portfolio snapshot API endpoints"""
    
    def test_list_snapshots(self):
        """Test listing portfolio snapshots"""
        self.authenticate()
        
        # Create snapshots
        snapshots = [
            PortfolioSnapshotFactory(user=self.user, snapshot_date=date.today() - timedelta(days=i))
            for i in range(5)
        ]
        
        url = reverse('portfolio:snapshots-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'snapshots' in data
        assert 'summary' in data
        assert len(data['snapshots']) == 5
    
    def test_create_snapshot(self):
        """Test creating new portfolio snapshot"""
        self.authenticate()
        
        # Create positions for snapshot
        PositionFactory(user=self.user, symbol='AAPL')
        PositionFactory(user=self.user, symbol='GOOGL')
        
        snapshot_data = {
            'snapshot_date': date.today().isoformat(),
            'force_recreate': False
        }
        
        url = reverse('portfolio:snapshots-create-snapshot')
        response = self.client.post(url, snapshot_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()['data']
        assert 'snapshot_id' in data
        assert data['snapshot_date'] == snapshot_data['snapshot_date']
    
    def test_get_latest_snapshot(self):
        """Test getting latest portfolio snapshot"""
        self.authenticate()
        
        # Create snapshots with different dates
        older_snapshot = PortfolioSnapshotFactory(
            user=self.user,
            snapshot_date=date.today() - timedelta(days=5)
        )
        latest_snapshot = PortfolioSnapshotFactory(
            user=self.user,
            snapshot_date=date.today()
        )
        
        url = reverse('portfolio:snapshots-latest')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert data['snapshot_id'] == str(latest_snapshot.snapshot_id)
    
    def test_get_chart_data(self):
        """Test getting snapshot data formatted for charts"""
        self.authenticate()
        
        # Create snapshots for chart
        snapshots = [
            PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=date.today() - timedelta(days=i),
                total_value=Decimal('10000') + Decimal(i * 100)
            )
            for i in range(10)
        ]
        
        url = reverse('portfolio:snapshots-chart-data')
        response = self.client.get(url, {'period': '1M'})
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'chart_data' in data
        assert 'period' in data
        assert len(data['chart_data']) == 10
        
        # Verify chart data structure
        chart_point = data['chart_data'][0]
        assert 'date' in chart_point
        assert 'total_value' in chart_point
        assert 'gain_loss_percent' in chart_point


@pytest.mark.django_db
class TestMetricsViews(BasePortfolioTestCase):
    """Test performance metrics API endpoints"""
    
    def test_list_metrics(self):
        """Test listing performance metrics"""
        self.authenticate()
        
        # Create metrics for different periods
        metrics = [
            PerformanceMetricsFactory(user=self.user, period='1M'),
            PerformanceMetricsFactory(user=self.user, period='3M'),
            PerformanceMetricsFactory(user=self.user, period='1Y')
        ]
        
        url = reverse('portfolio:metrics-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'metrics_by_period' in data
        assert 'available_periods' in data
        assert len(data['available_periods']) == 3
    
    def test_calculate_metrics(self):
        """Test metrics calculation endpoint"""
        self.authenticate()
        
        # Create snapshots for calculation
        snapshots = [
            PortfolioSnapshotFactory(
                user=self.user,
                snapshot_date=date.today() - timedelta(days=30 - i)
            )
            for i in range(30)
        ]
        
        calculation_data = {
            'period': '1M',
            'force_recalculate': True,
            'include_benchmark': True,
            'benchmark_symbol': 'SPY'
        }
        
        url = reverse('portfolio:metrics-calculate')
        response = self.client.post(url, calculation_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()['data']
        assert 'period' in data
        assert 'total_return' in data
        assert data['period'] == '1M'
    
    def test_metrics_summary(self):
        """Test metrics summary endpoint"""
        self.authenticate()
        
        # Create metrics for multiple periods
        periods = ['1M', '3M', '6M', '1Y']
        for period in periods:
            PerformanceMetricsFactory(user=self.user, period=period)
        
        url = reverse('portfolio:metrics-summary')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'metrics_by_period' in data
        assert 'summary_statistics' in data
        
        # Verify all periods are included
        for period in periods:
            assert period in data['metrics_by_period']
            assert data['metrics_by_period'][period] is not None
    
    def test_compare_metrics(self):
        """Test metrics comparison endpoint"""
        self.authenticate()
        
        # Create metrics for comparison
        periods = ['1M', '3M', '6M']
        for period in periods:
            PerformanceMetricsFactory(
                user=self.user,
                period=period,
                total_return=Decimal(f'{periods.index(period) + 1}.50')  # Different returns
            )
        
        url = reverse('portfolio:metrics-compare')
        response = self.client.get(url, {'periods': '1M,3M,6M'})
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        assert 'comparison_data' in data
        assert 'best_performing_period' in data
        assert len(data['comparison_data']) == 3
        
        # Verify best performing period identification
        assert data['best_performing_period']['period'] == '6M'  # Highest return


@pytest.mark.django_db
class TestViewPermissions(BasePortfolioTestCase):
    """Test API endpoint permissions and security"""
    
    def test_user_data_isolation(self):
        """Test users can only access their own data"""
        self.authenticate()
        
        # Create data for current user
        my_position = PositionFactory(user=self.user, symbol='AAPL')
        
        # Create data for another user
        other_user = UserFactory()
        other_position = PositionFactory(user=other_user, symbol='GOOGL')
        
        # Test position list only returns current user's data
        url = reverse('portfolio:positions-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()['data']
        symbols = [pos['symbol'] for pos in data['positions']]
        assert 'AAPL' in symbols
        assert 'GOOGL' not in symbols
        
        # Test cannot access other user's position directly
        url = reverse('portfolio:positions-detail', kwargs={'position_id': other_position.position_id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_jwt_token_validation(self):
        """Test JWT token validation on protected endpoints"""
        # Test without token
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with valid token
        self.authenticate()
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_method_not_allowed(self):
        """Test method not allowed responses"""
        self.authenticate()
        
        # Test POST on overview endpoint (should be GET only)
        url = reverse('portfolio:overview')
        response = self.client.post(url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestErrorHandling(BasePortfolioTestCase):
    """Test error handling in API views"""
    
    def test_invalid_position_id(self):
        """Test handling of invalid position ID"""
        self.authenticate()
        
        invalid_uuid = '00000000-0000-0000-0000-000000000000'
        url = reverse('portfolio:positions-detail', kwargs={'position_id': invalid_uuid})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['error'] is True
    
    def test_invalid_data_format(self):
        """Test handling of invalid data formats"""
        self.authenticate()
        
        # Test invalid JSON
        url = reverse('portfolio:positions-list')
        response = self.client.post(
            url,
            'invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_missing_required_fields(self):
        """Test validation of required fields"""
        self.authenticate()
        
        incomplete_data = {
            'symbol': 'AAPL',
            # Missing required fields
        }
        
        url = reverse('portfolio:positions-list')
        response = self.client.post(url, incomplete_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['error'] is True
        assert 'details' in response.json()
    
    @patch('portfolio.services.portfolio_service.PortfolioService.get_portfolio_overview')
    def test_service_error_handling(self, mock_service):
        """Test handling of service layer errors"""
        self.authenticate()
        
        # Mock service to raise exception
        mock_service.side_effect = Exception('Service error')
        
        url = reverse('portfolio:overview')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Service error' in response.json()['message']
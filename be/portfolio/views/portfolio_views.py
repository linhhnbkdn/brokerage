"""
Portfolio overview and performance API views
"""

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q

from .base import BasePortfolioViewSet
from portfolio.models import Position, PortfolioSnapshot, PerformanceMetrics
from banking.models import UserBalance
from portfolio.serializers import (
    PortfolioOverviewSerializer,
    PortfolioPerformanceSerializer,
    PositionSummarySerializer,
    PerformanceMetricsSerializer
)


class PortfolioOverviewViewSet(BasePortfolioViewSet):
    """Portfolio overview endpoints"""
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        GET /api/portfolio/overview/
        Get current portfolio overview with positions and performance
        """
        try:
            user = request.user
            
            # Get user's active positions
            positions = Position.objects.filter(user=user, status='active')
            
            # Get user's cash balance
            try:
                user_balance = UserBalance.objects.get(user=user)
                cash_balance = user_balance.available_balance
            except UserBalance.DoesNotExist:
                cash_balance = Decimal('0.00')
            
            # Calculate portfolio totals
            total_value = Decimal('0.00')
            total_cost_basis = Decimal('0.00')
            positions_data = []
            
            for position in positions:
                position_value = position.get_current_value()
                position_cost = position.get_cost_basis()
                
                total_value += position_value
                total_cost_basis += position_cost
                
                positions_data.append({
                    'position_id': str(position.position_id),
                    'symbol': position.symbol,
                    'instrument_type': position.instrument_type,
                    'current_value': str(position_value),
                    'cost_basis': str(position_cost),
                    'unrealized_gain_loss': str(position.get_unrealized_gain_loss()),
                    'unrealized_gain_loss_percent': str(position.get_unrealized_gain_loss_percent()),
                })
            
            # Calculate totals
            total_portfolio_value = total_value + cash_balance
            total_gain_loss = total_value - total_cost_basis
            total_gain_loss_percent = Decimal('0.0000')
            if total_cost_basis > 0:
                total_gain_loss_percent = (total_gain_loss / total_cost_basis) * 100
            
            # Get daily performance (compare with yesterday's snapshot)
            yesterday = timezone.now().date() - timedelta(days=1)
            yesterday_snapshot = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date=yesterday
            ).first()
            
            day_gain_loss = None
            day_gain_loss_percent = None
            
            if yesterday_snapshot:
                yesterday_total = yesterday_snapshot.total_value + yesterday_snapshot.cash_balance
                day_gain_loss = total_portfolio_value - yesterday_total
                if yesterday_total > 0:
                    day_gain_loss_percent = (day_gain_loss / yesterday_total) * 100
            
            # Calculate asset allocation
            asset_allocation = self._calculate_asset_allocation(positions_data, total_value)
            
            # Get top positions (by value)
            top_positions = sorted(
                positions_data, 
                key=lambda x: float(x['current_value']), 
                reverse=True
            )[:5]
            
            # Prepare response data
            overview_data = {
                'total_value': total_value,
                'cash_balance': cash_balance,
                'total_portfolio_value': total_portfolio_value,
                'total_cost_basis': total_cost_basis,
                'total_gain_loss': total_gain_loss,
                'total_gain_loss_percent': total_gain_loss_percent,
                'day_gain_loss': day_gain_loss,
                'day_gain_loss_percent': day_gain_loss_percent,
                'positions_count': len(positions_data),
                'last_updated': timezone.now(),
                'asset_allocation': asset_allocation,
                'top_positions': top_positions,
            }
            
            serializer = PortfolioOverviewSerializer(overview_data)
            return self.handle_success_response(serializer.data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving portfolio overview: {str(e)}")
    
    def _calculate_asset_allocation(self, positions_data, total_value):
        """Calculate asset allocation by instrument type"""
        if total_value == 0:
            return {}
        
        allocation = {}
        for position in positions_data:
            instrument_type = position['instrument_type']
            position_value = Decimal(position['current_value'])
            
            if instrument_type not in allocation:
                allocation[instrument_type] = {
                    'value': Decimal('0.00'),
                    'count': 0,
                    'percentage': Decimal('0.00')
                }
            
            allocation[instrument_type]['value'] += position_value
            allocation[instrument_type]['count'] += 1
        
        # Calculate percentages
        for instrument_type in allocation:
            percentage = (allocation[instrument_type]['value'] / total_value) * 100
            allocation[instrument_type]['percentage'] = percentage
            allocation[instrument_type]['value'] = str(allocation[instrument_type]['value'])
            allocation[instrument_type]['percentage'] = str(percentage)
        
        return allocation


class PortfolioPerformanceViewSet(BasePortfolioViewSet):
    """Portfolio performance analysis endpoints"""
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """
        GET /api/portfolio/performance/?period=1M
        Get portfolio performance data for specified period
        """
        try:
            user = request.user
            period = request.query_params.get('period', '1M')
            
            # Validate period
            valid_periods = ['1D', '1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'ALL']
            if period not in valid_periods:
                return self.handle_error_response(f"Invalid period. Choose from: {', '.join(valid_periods)}")
            
            # Calculate date range
            end_date = timezone.now().date()
            start_date = self._calculate_start_date(period, end_date)
            
            # Get snapshots for the period
            snapshots = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date__gte=start_date,
                snapshot_date__lte=end_date
            ).order_by('snapshot_date')
            
            if not snapshots.exists():
                return self.handle_error_response("No portfolio data available for this period")
            
            # Get or calculate performance metrics
            try:
                metrics = PerformanceMetrics.objects.get(
                    user=user,
                    period=period,
                    start_date=start_date,
                    end_date=end_date
                )
            except PerformanceMetrics.DoesNotExist:
                # Calculate metrics if they don't exist
                metrics = PerformanceMetrics.calculate_metrics(
                    user=user,
                    period=period,
                    snapshots=list(snapshots)
                )
            
            if not metrics:
                return self.handle_error_response("Unable to calculate performance metrics")
            
            # Prepare snapshots data for chart
            snapshots_data = []
            for snapshot in snapshots:
                snapshots_data.append({
                    'date': snapshot.snapshot_date.isoformat(),
                    'total_value': str(snapshot.total_value + snapshot.cash_balance),
                    'gain_loss_percent': str(snapshot.total_gain_loss_percent),
                    'day_change_percent': str(snapshot.day_gain_loss_percent),
                })
            
            # Prepare performance data
            performance_data = {
                'period': period,
                'period_display': next(display for code, display in PerformanceMetrics.PERIOD_CHOICES if code == period),
                'start_date': start_date,
                'end_date': end_date,
                'total_return': metrics.total_return,
                'annualized_return': metrics.annualized_return,
                'volatility': metrics.volatility,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'benchmark_return': metrics.benchmark_return,
                'alpha': metrics.alpha,
                'beta': metrics.beta,
                'outperformed_benchmark': metrics.outperformed_benchmark(),
                'starting_value': metrics.starting_value,
                'ending_value': metrics.ending_value,
                'peak_value': metrics.peak_value,
                'is_profitable': metrics.is_profitable(),
                'trading_days': metrics.trading_days,
                'snapshots': snapshots_data,
            }
            
            serializer = PortfolioPerformanceSerializer(performance_data)
            return self.handle_success_response(serializer.data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving performance data: {str(e)}")
    
    def _calculate_start_date(self, period, end_date):
        """Calculate start date based on period"""
        if period == '1D':
            return end_date - timedelta(days=1)
        elif period == '1W':
            return end_date - timedelta(weeks=1)
        elif period == '1M':
            return end_date - timedelta(days=30)
        elif period == '3M':
            return end_date - timedelta(days=90)
        elif period == '6M':
            return end_date - timedelta(days=180)
        elif period == '1Y':
            return end_date - timedelta(days=365)
        elif period == '3Y':
            return end_date - timedelta(days=1095)
        elif period == '5Y':
            return end_date - timedelta(days=1825)
        elif period == 'ALL':
            # Find the earliest snapshot
            earliest = PortfolioSnapshot.objects.filter(
                user=self.request.user
            ).order_by('snapshot_date').first()
            return earliest.snapshot_date if earliest else end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)  # Default to 1 month
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/portfolio/performance/summary/
        Get quick performance summary for dashboard
        """
        try:
            user = request.user
            
            # Get latest snapshot
            latest_snapshot = PortfolioSnapshot.objects.filter(user=user).order_by('-snapshot_date').first()
            
            if not latest_snapshot:
                return self.handle_error_response("No portfolio data available")
            
            # Get recent performance metrics
            recent_metrics = PerformanceMetrics.objects.filter(
                user=user
            ).order_by('-calculated_at')[:3]  # Get last 3 calculations
            
            summary_data = {
                'current_value': latest_snapshot.total_value + latest_snapshot.cash_balance,
                'day_change': latest_snapshot.day_gain_loss,
                'day_change_percent': latest_snapshot.day_gain_loss_percent,
                'total_return_percent': latest_snapshot.total_gain_loss_percent,
                'last_updated': latest_snapshot.snapshot_time,
                'recent_metrics': [
                    {
                        'period': m.period,
                        'period_display': m.get_period_display(),
                        'total_return': str(m.total_return),
                        'is_profitable': m.is_profitable(),
                    }
                    for m in recent_metrics
                ]
            }
            
            return self.handle_success_response(summary_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving performance summary: {str(e)}")
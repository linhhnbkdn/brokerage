"""
Performance metrics API views
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone

from .base import BasePortfolioModelViewSet
from portfolio.models import PerformanceMetrics, PortfolioSnapshot
from portfolio.serializers import (
    PerformanceMetricsSerializer,
    PerformanceMetricsSummarySerializer,
    MetricsCalculationRequestSerializer
)


class PerformanceMetricsViewSet(BasePortfolioModelViewSet):
    """Performance metrics operations"""
    
    queryset = PerformanceMetrics.objects.all()
    serializer_class = PerformanceMetricsSerializer
    lookup_field = 'metrics_id'
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return PerformanceMetricsSummarySerializer
        elif self.action == 'calculate':
            return MetricsCalculationRequestSerializer
        return PerformanceMetricsSerializer
    
    def list(self, request):
        """
        GET /api/portfolio/metrics/
        List performance metrics with optional period filtering
        """
        try:
            queryset = self.get_queryset()
            
            # Filter by period if provided
            period = request.query_params.get('period')
            if period:
                valid_periods = [choice[0] for choice in PerformanceMetrics.PERIOD_CHOICES]
                if period not in valid_periods:
                    return self.handle_error_response(f"Invalid period. Choose from: {', '.join(valid_periods)}")
                queryset = queryset.filter(period=period)
            
            # Order by calculation date (newest first)
            queryset = queryset.order_by('-calculated_at')
            
            serializer = self.get_serializer(queryset, many=True)
            
            # Group by period for better organization
            metrics_by_period = {}
            for metric_data in serializer.data:
                period_key = metric_data['period']
                if period_key not in metrics_by_period:
                    metrics_by_period[period_key] = []
                metrics_by_period[period_key].append(metric_data)
            
            response_data = {
                'metrics_by_period': metrics_by_period,
                'total_metrics': queryset.count(),
                'available_periods': list(metrics_by_period.keys())
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving metrics: {str(e)}")
    
    def retrieve(self, request, metrics_id=None):
        """
        GET /api/portfolio/metrics/{metrics_id}/
        Get detailed metrics information
        """
        try:
            metrics = self.get_queryset().get(metrics_id=metrics_id)
            serializer = PerformanceMetricsSerializer(metrics)
            return self.handle_success_response(serializer.data)
            
        except PerformanceMetrics.DoesNotExist:
            return self.handle_error_response("Metrics not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error retrieving metrics: {str(e)}")
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        POST /api/portfolio/metrics/calculate/
        Calculate performance metrics for a specified period
        """
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    "error": True,
                    "message": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            period = serializer.validated_data['period']
            force_recalculate = serializer.validated_data.get('force_recalculate', False)
            include_benchmark = serializer.validated_data.get('include_benchmark', True)
            benchmark_symbol = serializer.validated_data.get('benchmark_symbol', 'SPY')
            
            # Calculate date range
            end_date = timezone.now().date()
            start_date = self._calculate_start_date(period, end_date)
            
            # Check if metrics already exist
            existing_metrics = PerformanceMetrics.objects.filter(
                user=user,
                period=period,
                start_date=start_date,
                end_date=end_date
            ).first()
            
            if existing_metrics and not force_recalculate:
                serializer = PerformanceMetricsSerializer(existing_metrics)
                return self.handle_success_response(
                    serializer.data,
                    "Using existing metrics. Use force_recalculate=true to recalculate."
                )
            
            # Get snapshots for the period
            snapshots = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date__gte=start_date,
                snapshot_date__lte=end_date
            ).order_by('snapshot_date')
            
            if not snapshots.exists():
                return self.handle_error_response(
                    f"No portfolio snapshots found for period {period}. Create snapshots first."
                )
            
            if snapshots.count() < 2:
                return self.handle_error_response(
                    f"At least 2 snapshots required for metrics calculation. Found {snapshots.count()}."
                )
            
            # Get benchmark data if requested
            benchmark_data = None
            if include_benchmark:
                # TODO: Implement actual benchmark data fetching
                # For now, simulate benchmark data
                benchmark_data = {
                    'symbol': benchmark_symbol,
                    'return': 8.5,  # Simulated S&P 500 return
                    'period': period
                }
            
            # Calculate metrics
            metrics = PerformanceMetrics.calculate_metrics(
                user=user,
                period=period,
                snapshots=list(snapshots),
                benchmark_data=benchmark_data
            )
            
            if not metrics:
                return self.handle_error_response("Failed to calculate performance metrics")
            
            serializer = PerformanceMetricsSerializer(metrics)
            
            return self.handle_success_response(
                serializer.data,
                "Performance metrics calculated successfully",
                status.HTTP_201_CREATED if not existing_metrics else status.HTTP_200_OK
            )
            
        except Exception as e:
            return self.handle_error_response(f"Error calculating metrics: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/portfolio/metrics/summary/
        Get performance metrics summary for all periods
        """
        try:
            user = request.user
            
            # Get latest metrics for each period
            periods = ['1M', '3M', '6M', '1Y', '3Y', '5Y']
            summary_data = {}
            
            for period in periods:
                latest_metric = PerformanceMetrics.objects.filter(
                    user=user,
                    period=period
                ).order_by('-calculated_at').first()
                
                if latest_metric:
                    summary_data[period] = {
                        'period_display': latest_metric.get_period_display(),
                        'total_return': str(latest_metric.total_return),
                        'annualized_return': str(latest_metric.annualized_return) if latest_metric.annualized_return else None,
                        'volatility': str(latest_metric.volatility) if latest_metric.volatility else None,
                        'sharpe_ratio': str(latest_metric.sharpe_ratio) if latest_metric.sharpe_ratio else None,
                        'is_profitable': latest_metric.is_profitable(),
                        'outperformed_benchmark': latest_metric.outperformed_benchmark(),
                        'calculated_at': latest_metric.calculated_at.isoformat(),
                    }
                else:
                    summary_data[period] = None
            
            # Calculate overall statistics
            available_periods = [p for p in periods if summary_data[p] is not None]
            profitable_periods = [p for p in available_periods if summary_data[p]['is_profitable']]
            
            response_data = {
                'metrics_by_period': summary_data,
                'summary_statistics': {
                    'available_periods': len(available_periods),
                    'profitable_periods': len(profitable_periods),
                    'profitability_ratio': len(profitable_periods) / len(available_periods) if available_periods else 0,
                }
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving metrics summary: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        GET /api/portfolio/metrics/compare/?periods=1M,3M,6M,1Y
        Compare performance metrics across multiple periods
        """
        try:
            user = request.user
            periods_param = request.query_params.get('periods', '1M,3M,6M,1Y')
            
            try:
                requested_periods = [p.strip() for p in periods_param.split(',')]
            except:
                return self.handle_error_response("Invalid periods format. Use comma-separated values like: 1M,3M,6M")
            
            valid_periods = [choice[0] for choice in PerformanceMetrics.PERIOD_CHOICES]
            invalid_periods = [p for p in requested_periods if p not in valid_periods]
            
            if invalid_periods:
                return self.handle_error_response(f"Invalid periods: {', '.join(invalid_periods)}")
            
            comparison_data = []
            
            for period in requested_periods:
                latest_metric = PerformanceMetrics.objects.filter(
                    user=user,
                    period=period
                ).order_by('-calculated_at').first()
                
                if latest_metric:
                    comparison_data.append({
                        'period': period,
                        'period_display': latest_metric.get_period_display(),
                        'total_return': str(latest_metric.total_return),
                        'annualized_return': str(latest_metric.annualized_return) if latest_metric.annualized_return else None,
                        'volatility': str(latest_metric.volatility) if latest_metric.volatility else None,
                        'sharpe_ratio': str(latest_metric.sharpe_ratio) if latest_metric.sharpe_ratio else None,
                        'max_drawdown': str(latest_metric.max_drawdown) if latest_metric.max_drawdown else None,
                        'alpha': str(latest_metric.alpha) if latest_metric.alpha else None,
                        'is_profitable': latest_metric.is_profitable(),
                        'calculated_at': latest_metric.calculated_at.isoformat(),
                    })
            
            if not comparison_data:
                return self.handle_error_response("No metrics found for the requested periods")
            
            # Find best performing period
            best_period = max(
                comparison_data, 
                key=lambda x: float(x['total_return']) if x['total_return'] else -float('inf')
            )
            
            response_data = {
                'periods_compared': requested_periods,
                'comparison_data': comparison_data,
                'best_performing_period': {
                    'period': best_period['period'],
                    'period_display': best_period['period_display'],
                    'total_return': best_period['total_return']
                }
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error comparing metrics: {str(e)}")
    
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
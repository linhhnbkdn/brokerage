"""
Portfolio snapshot API views
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from .base import BasePortfolioModelViewSet
from portfolio.models import PortfolioSnapshot, Position
from banking.models import UserBalance
from portfolio.serializers import (
    PortfolioSnapshotSerializer,
    PortfolioSnapshotSummarySerializer,
    SnapshotCreateSerializer
)


class PortfolioSnapshotViewSet(BasePortfolioModelViewSet):
    """Portfolio snapshot operations"""
    
    queryset = PortfolioSnapshot.objects.all()
    serializer_class = PortfolioSnapshotSerializer
    lookup_field = 'snapshot_id'
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return PortfolioSnapshotSummarySerializer
        elif self.action == 'create_snapshot':
            return SnapshotCreateSerializer
        return PortfolioSnapshotSerializer
    
    def list(self, request):
        """
        GET /api/portfolio/snapshots/
        List portfolio snapshots with optional date filtering
        """
        try:
            queryset = self.get_queryset()
            
            # Date filtering
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if start_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(snapshot_date__gte=start_date)
                except ValueError:
                    return self.handle_error_response("Invalid start_date format. Use YYYY-MM-DD")
            
            if end_date:
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(snapshot_date__lte=end_date)
                except ValueError:
                    return self.handle_error_response("Invalid end_date format. Use YYYY-MM-DD")
            
            # Limit results if no date filter provided
            if not start_date and not end_date:
                queryset = queryset[:30]  # Last 30 snapshots
            
            # Order by date (newest first)
            queryset = queryset.order_by('-snapshot_date')
            
            serializer = self.get_serializer(queryset, many=True)
            
            # Add summary statistics
            if queryset:
                latest = queryset.first()
                earliest = queryset.last()
                
                summary = {
                    'total_snapshots': queryset.count(),
                    'date_range': {
                        'start': earliest.snapshot_date,
                        'end': latest.snapshot_date,
                    },
                    'latest_value': str(latest.calculate_total_value_with_cash()),
                    'period_return': None
                }
                
                # Calculate period return if we have both start and end
                if queryset.count() > 1:
                    start_value = earliest.calculate_total_value_with_cash()
                    end_value = latest.calculate_total_value_with_cash()
                    
                    if start_value > 0:
                        period_return = ((end_value - start_value) / start_value) * 100
                        summary['period_return'] = str(period_return)
            else:
                summary = {
                    'total_snapshots': 0,
                    'date_range': None,
                    'latest_value': None,
                    'period_return': None
                }
            
            response_data = {
                'snapshots': serializer.data,
                'summary': summary
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving snapshots: {str(e)}")
    
    def retrieve(self, request, snapshot_id=None):
        """
        GET /api/portfolio/snapshots/{snapshot_id}/
        Get detailed snapshot information
        """
        try:
            snapshot = self.get_queryset().get(snapshot_id=snapshot_id)
            serializer = PortfolioSnapshotSerializer(snapshot)
            return self.handle_success_response(serializer.data)
            
        except PortfolioSnapshot.DoesNotExist:
            return self.handle_error_response("Snapshot not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error retrieving snapshot: {str(e)}")
    
    @transaction.atomic
    @action(detail=False, methods=['post'])
    def create_snapshot(self, request):
        """
        POST /api/portfolio/snapshots/create_snapshot/
        Create a new portfolio snapshot
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
            
            snapshot_date = serializer.validated_data.get('snapshot_date', timezone.now().date())
            force_recreate = serializer.validated_data.get('force_recreate', False)
            
            # Check if snapshot already exists
            existing_snapshot = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date=snapshot_date
            ).first()
            
            if existing_snapshot and not force_recreate:
                return self.handle_error_response(
                    f"Snapshot for {snapshot_date} already exists. Use force_recreate=true to overwrite."
                )
            
            # Get current positions
            positions = Position.objects.filter(user=user, status='active')
            positions_data = [position.get_position_summary() for position in positions]
            
            # Get cash balance
            try:
                user_balance = UserBalance.objects.get(user=user)
                cash_balance = user_balance.available_balance
            except UserBalance.DoesNotExist:
                cash_balance = Decimal('0.00')
            
            # Create snapshot
            snapshot = PortfolioSnapshot.create_daily_snapshot(
                user=user,
                positions_data=positions_data,
                cash_balance=cash_balance
            )
            
            serializer = PortfolioSnapshotSerializer(snapshot)
            
            return self.handle_success_response(
                serializer.data,
                "Snapshot created successfully",
                status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return self.handle_error_response(f"Error creating snapshot: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        GET /api/portfolio/snapshots/latest/
        Get the most recent portfolio snapshot
        """
        try:
            latest_snapshot = self.get_queryset().order_by('-snapshot_date').first()
            
            if not latest_snapshot:
                return self.handle_error_response("No snapshots found", status.HTTP_404_NOT_FOUND)
            
            serializer = PortfolioSnapshotSerializer(latest_snapshot)
            return self.handle_success_response(serializer.data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving latest snapshot: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def chart_data(self, request):
        """
        GET /api/portfolio/snapshots/chart_data/?period=1M
        Get simplified snapshot data for charting
        """
        try:
            period = request.query_params.get('period', '1M')
            
            # Calculate date range
            end_date = timezone.now().date()
            
            if period == '1W':
                start_date = end_date - timedelta(days=7)
            elif period == '1M':
                start_date = end_date - timedelta(days=30)
            elif period == '3M':
                start_date = end_date - timedelta(days=90)
            elif period == '6M':
                start_date = end_date - timedelta(days=180)
            elif period == '1Y':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 1M
            
            snapshots = self.get_queryset().filter(
                snapshot_date__gte=start_date,
                snapshot_date__lte=end_date
            ).order_by('snapshot_date')
            
            chart_data = []
            for snapshot in snapshots:
                chart_data.append({
                    'date': snapshot.snapshot_date.isoformat(),
                    'total_value': str(snapshot.calculate_total_value_with_cash()),
                    'portfolio_value': str(snapshot.total_value),
                    'cash_balance': str(snapshot.cash_balance),
                    'gain_loss_percent': str(snapshot.total_gain_loss_percent),
                    'day_change_percent': str(snapshot.day_gain_loss_percent),
                })
            
            response_data = {
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'data_points': len(chart_data),
                'chart_data': chart_data
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving chart data: {str(e)}")
    
    @action(detail=True, methods=['delete'])
    def delete_snapshot(self, request, snapshot_id=None):
        """
        DELETE /api/portfolio/snapshots/{snapshot_id}/delete_snapshot/
        Delete a specific snapshot
        """
        try:
            snapshot = self.get_queryset().get(snapshot_id=snapshot_id)
            snapshot_date = snapshot.snapshot_date
            snapshot.delete()
            
            return Response({
                "error": False,
                "message": f"Snapshot for {snapshot_date} deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
            
        except PortfolioSnapshot.DoesNotExist:
            return self.handle_error_response("Snapshot not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error deleting snapshot: {str(e)}")
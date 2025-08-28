"""
Portfolio snapshot service for creating and managing daily snapshots
"""

from decimal import Decimal
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from portfolio.models import Position, PortfolioSnapshot
from banking.models import UserBalance


class SnapshotService:
    """Service for portfolio snapshot operations"""
    
    def __init__(self):
        self.portfolio_service = None  # Will be injected via DI
    
    @transaction.atomic
    def create_daily_snapshot(self, user: User, snapshot_date: Optional[date] = None, force_recreate: bool = False) -> PortfolioSnapshot:
        """
        Create a daily portfolio snapshot
        
        Args:
            user: User instance
            snapshot_date: Date for snapshot (defaults to today)
            force_recreate: Whether to recreate if snapshot exists
            
        Returns:
            PortfolioSnapshot instance
        """
        try:
            if not snapshot_date:
                snapshot_date = timezone.now().date()
            
            # Check if snapshot already exists
            existing_snapshot = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date=snapshot_date
            ).first()
            
            if existing_snapshot and not force_recreate:
                return existing_snapshot
            
            # Get current positions
            positions = Position.objects.filter(user=user, status='active')
            positions_data = []
            
            for position in positions:
                position_summary = position.get_position_summary()
                positions_data.append({
                    'position_id': position_summary['position_id'],
                    'symbol': position_summary['symbol'],
                    'instrument_type': position_summary['instrument_type'],
                    'quantity': position_summary['quantity'],
                    'average_cost': position_summary['average_cost'],
                    'current_price': position_summary['current_price'],
                    'cost_basis': position_summary['cost_basis'],
                    'current_value': position_summary['current_value'],
                    'unrealized_gain_loss': position_summary['unrealized_gain_loss'],
                    'unrealized_gain_loss_percent': position_summary['unrealized_gain_loss_percent'],
                })
            
            # Get cash balance
            cash_balance = self._get_user_cash_balance(user)
            
            # Create or update snapshot
            if existing_snapshot:
                existing_snapshot.delete()
            
            snapshot = PortfolioSnapshot.create_daily_snapshot(
                user=user,
                positions_data=positions_data,
                cash_balance=cash_balance
            )
            
            return snapshot
            
        except Exception as e:
            raise Exception(f"Error creating daily snapshot: {str(e)}")
    
    def create_snapshots_for_date_range(self, user: User, start_date: date, end_date: date, force_recreate: bool = False) -> List[PortfolioSnapshot]:
        """
        Create snapshots for a range of dates
        
        Args:
            user: User instance
            start_date: Start date for snapshots
            end_date: End date for snapshots
            force_recreate: Whether to recreate existing snapshots
            
        Returns:
            List of created PortfolioSnapshot instances
        """
        snapshots = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                snapshot = self.create_daily_snapshot(user, current_date, force_recreate)
                snapshots.append(snapshot)
            except Exception as e:
                print(f"Error creating snapshot for {current_date}: {str(e)}")
            
            current_date += timedelta(days=1)
        
        return snapshots
    
    def get_snapshot_for_date(self, user: User, snapshot_date: date) -> Optional[PortfolioSnapshot]:
        """
        Get snapshot for specific date
        
        Args:
            user: User instance
            snapshot_date: Date to get snapshot for
            
        Returns:
            PortfolioSnapshot instance or None
        """
        try:
            return PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date=snapshot_date
            ).first()
        except Exception:
            return None
    
    def get_snapshots_for_period(self, user: User, start_date: date, end_date: date) -> List[PortfolioSnapshot]:
        """
        Get snapshots for a date range
        
        Args:
            user: User instance
            start_date: Start date
            end_date: End date
            
        Returns:
            List of PortfolioSnapshot instances ordered by date
        """
        try:
            return list(PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date__gte=start_date,
                snapshot_date__lte=end_date
            ).order_by('snapshot_date'))
        except Exception:
            return []
    
    def get_latest_snapshot(self, user: User) -> Optional[PortfolioSnapshot]:
        """
        Get the most recent snapshot for a user
        
        Args:
            user: User instance
            
        Returns:
            Latest PortfolioSnapshot instance or None
        """
        try:
            return PortfolioSnapshot.objects.filter(user=user).order_by('-snapshot_date').first()
        except Exception:
            return None
    
    def calculate_snapshot_metrics(self, snapshots: List[PortfolioSnapshot]) -> Dict:
        """
        Calculate metrics from a list of snapshots
        
        Args:
            snapshots: List of PortfolioSnapshot instances
            
        Returns:
            Dictionary with calculated metrics
        """
        try:
            if not snapshots or len(snapshots) < 2:
                return {}
            
            # Sort by date
            sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
            
            first_snapshot = sorted_snapshots[0]
            last_snapshot = sorted_snapshots[-1]
            
            # Calculate basic metrics
            start_value = first_snapshot.calculate_total_value_with_cash()
            end_value = last_snapshot.calculate_total_value_with_cash()
            
            total_return = Decimal('0.00')
            if start_value > 0:
                total_return = ((end_value - start_value) / start_value) * 100
            
            # Calculate volatility
            daily_returns = []
            for i in range(1, len(sorted_snapshots)):
                prev_value = sorted_snapshots[i-1].calculate_total_value_with_cash()
                curr_value = sorted_snapshots[i].calculate_total_value_with_cash()
                
                if prev_value > 0:
                    daily_return = (curr_value - prev_value) / prev_value
                    daily_returns.append(float(daily_return))
            
            volatility = self._calculate_volatility(daily_returns) if daily_returns else Decimal('0.00')
            
            # Find peak and drawdown
            peak_value = max(s.calculate_total_value_with_cash() for s in sorted_snapshots)
            max_drawdown = self._calculate_max_drawdown(sorted_snapshots)
            
            return {
                'period_days': len(sorted_snapshots),
                'start_date': first_snapshot.snapshot_date,
                'end_date': last_snapshot.snapshot_date,
                'start_value': start_value,
                'end_value': end_value,
                'peak_value': peak_value,
                'total_return': total_return,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'daily_returns': daily_returns,
            }
            
        except Exception as e:
            raise Exception(f"Error calculating snapshot metrics: {str(e)}")
    
    def cleanup_old_snapshots(self, user: User, keep_days: int = 365) -> int:
        """
        Clean up old snapshots beyond retention period
        
        Args:
            user: User instance
            keep_days: Number of days to keep (default: 1 year)
            
        Returns:
            Number of snapshots deleted
        """
        try:
            cutoff_date = timezone.now().date() - timedelta(days=keep_days)
            
            old_snapshots = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date__lt=cutoff_date
            )
            
            count = old_snapshots.count()
            old_snapshots.delete()
            
            return count
            
        except Exception as e:
            raise Exception(f"Error cleaning up old snapshots: {str(e)}")
    
    def generate_snapshot_chart_data(self, snapshots: List[PortfolioSnapshot]) -> List[Dict]:
        """
        Generate chart-friendly data from snapshots
        
        Args:
            snapshots: List of PortfolioSnapshot instances
            
        Returns:
            List of dictionaries suitable for charting
        """
        try:
            chart_data = []
            
            for snapshot in sorted(snapshots, key=lambda s: s.snapshot_date):
                chart_data.append({
                    'date': snapshot.snapshot_date.isoformat(),
                    'timestamp': int(snapshot.snapshot_date.strftime('%s')) * 1000,  # JS timestamp
                    'total_value': float(snapshot.calculate_total_value_with_cash()),
                    'portfolio_value': float(snapshot.total_value),
                    'cash_balance': float(snapshot.cash_balance),
                    'gain_loss_percent': float(snapshot.total_gain_loss_percent),
                    'day_change_percent': float(snapshot.day_gain_loss_percent) if snapshot.day_gain_loss_percent else 0,
                })
            
            return chart_data
            
        except Exception as e:
            raise Exception(f"Error generating chart data: {str(e)}")
    
    def _get_user_cash_balance(self, user: User) -> Decimal:
        """Get user's available cash balance"""
        try:
            user_balance = UserBalance.objects.get(user=user)
            return user_balance.available_balance
        except UserBalance.DoesNotExist:
            return Decimal('0.00')
    
    def _calculate_volatility(self, daily_returns: List[float]) -> Decimal:
        """Calculate annualized volatility from daily returns"""
        if not daily_returns or len(daily_returns) < 2:
            return Decimal('0.00')
        
        # Calculate standard deviation
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
        std_dev = variance ** 0.5
        
        # Annualize (multiply by sqrt of 252 trading days)
        annualized_volatility = std_dev * (252 ** 0.5) * 100
        
        return Decimal(str(round(annualized_volatility, 4)))
    
    def _calculate_max_drawdown(self, snapshots: List[PortfolioSnapshot]) -> Decimal:
        """Calculate maximum drawdown from snapshots"""
        if not snapshots or len(snapshots) < 2:
            return Decimal('0.00')
        
        peak = snapshots[0].calculate_total_value_with_cash()
        max_drawdown = Decimal('0.00')
        
        for snapshot in snapshots[1:]:
            value = snapshot.calculate_total_value_with_cash()
            
            if value > peak:
                peak = value
            else:
                drawdown = ((peak - value) / peak) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown
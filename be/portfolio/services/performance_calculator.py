"""
Performance calculation service for portfolio metrics
"""

from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta
import math
from django.contrib.auth.models import User

from portfolio.models import PerformanceMetrics, PortfolioSnapshot


class PerformanceCalculator:
    """Service for calculating portfolio performance metrics"""
    
    def __init__(self):
        self.risk_free_rate = Decimal('0.02')  # 2% risk-free rate
    
    def calculate_period_metrics(
        self, 
        user: User, 
        period: str, 
        snapshots: List[PortfolioSnapshot],
        benchmark_data: Optional[Dict] = None
    ) -> Optional[PerformanceMetrics]:
        """
        Calculate comprehensive performance metrics for a period
        
        Args:
            user: User instance
            period: Period string (e.g., '1M', '3M', '1Y')
            snapshots: List of PortfolioSnapshot instances
            benchmark_data: Optional benchmark comparison data
            
        Returns:
            PerformanceMetrics instance or None
        """
        try:
            if not snapshots or len(snapshots) < 2:
                return None
            
            # Sort snapshots by date
            sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
            
            start_snapshot = sorted_snapshots[0]
            end_snapshot = sorted_snapshots[-1]
            
            # Calculate basic returns
            start_value = start_snapshot.calculate_total_value_with_cash()
            end_value = end_snapshot.calculate_total_value_with_cash()
            
            total_return = self._calculate_total_return(start_value, end_value)
            
            # Calculate time-weighted return
            time_weighted_return = self._calculate_time_weighted_return(sorted_snapshots)
            
            # Calculate annualized return
            days_diff = (end_snapshot.snapshot_date - start_snapshot.snapshot_date).days
            annualized_return = self._calculate_annualized_return(total_return, days_diff)
            
            # Calculate risk metrics
            volatility = self._calculate_volatility(sorted_snapshots)
            max_drawdown = self._calculate_max_drawdown(sorted_snapshots)
            sharpe_ratio = self._calculate_sharpe_ratio(annualized_return, volatility)
            
            # Find peak value
            peak_value = max(s.calculate_total_value_with_cash() for s in sorted_snapshots)
            
            # Benchmark comparison
            benchmark_return = None
            alpha = None
            beta = None
            
            if benchmark_data:
                benchmark_return = Decimal(str(benchmark_data.get('return', 0)))
                alpha = total_return - benchmark_return if benchmark_return else None
                # Beta calculation would require correlation analysis with benchmark
                # For now, we'll leave it as None or calculate a simplified version
            
            # Create or update metrics
            metrics, created = PerformanceMetrics.objects.update_or_create(
                user=user,
                period=period,
                start_date=start_snapshot.snapshot_date,
                end_date=end_snapshot.snapshot_date,
                defaults={
                    'total_return': total_return,
                    'time_weighted_return': time_weighted_return,
                    'annualized_return': annualized_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'benchmark_return': benchmark_return,
                    'alpha': alpha,
                    'beta': beta,
                    'starting_value': start_value,
                    'ending_value': end_value,
                    'peak_value': peak_value,
                    'trading_days': len(sorted_snapshots),
                }
            )
            
            return metrics
            
        except Exception as e:
            raise Exception(f"Error calculating performance metrics: {str(e)}")
    
    def calculate_rolling_metrics(
        self, 
        snapshots: List[PortfolioSnapshot], 
        window_days: int = 30
    ) -> List[Dict]:
        """
        Calculate rolling performance metrics
        
        Args:
            snapshots: List of PortfolioSnapshot instances
            window_days: Rolling window size in days
            
        Returns:
            List of rolling metrics
        """
        try:
            if not snapshots or len(snapshots) < window_days:
                return []
            
            sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
            rolling_metrics = []
            
            for i in range(window_days, len(sorted_snapshots) + 1):
                window_snapshots = sorted_snapshots[i - window_days:i]
                
                start_value = window_snapshots[0].calculate_total_value_with_cash()
                end_value = window_snapshots[-1].calculate_total_value_with_cash()
                
                # Calculate metrics for this window
                total_return = self._calculate_total_return(start_value, end_value)
                volatility = self._calculate_volatility(window_snapshots)
                max_drawdown = self._calculate_max_drawdown(window_snapshots)
                sharpe_ratio = self._calculate_sharpe_ratio(total_return, volatility)
                
                rolling_metrics.append({
                    'date': window_snapshots[-1].snapshot_date,
                    'total_return': total_return,
                    'volatility': volatility,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio,
                    'start_value': start_value,
                    'end_value': end_value,
                })
            
            return rolling_metrics
            
        except Exception as e:
            raise Exception(f"Error calculating rolling metrics: {str(e)}")
    
    def compare_with_benchmark(
        self, 
        portfolio_snapshots: List[PortfolioSnapshot],
        benchmark_data: List[Dict]
    ) -> Dict:
        """
        Compare portfolio performance with benchmark
        
        Args:
            portfolio_snapshots: Portfolio snapshot data
            benchmark_data: Benchmark price data
            
        Returns:
            Dictionary with comparison metrics
        """
        try:
            if not portfolio_snapshots or not benchmark_data:
                return {}
            
            # Calculate portfolio returns
            sorted_snapshots = sorted(portfolio_snapshots, key=lambda s: s.snapshot_date)
            portfolio_returns = self._calculate_daily_returns(sorted_snapshots)
            
            # Calculate benchmark returns (assuming benchmark_data has price info)
            benchmark_returns = []
            for i in range(1, len(benchmark_data)):
                prev_price = Decimal(str(benchmark_data[i-1]['close']))
                curr_price = Decimal(str(benchmark_data[i]['close']))
                
                if prev_price > 0:
                    daily_return = (curr_price - prev_price) / prev_price
                    benchmark_returns.append(daily_return)
            
            # Align returns (take minimum length)
            min_length = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns = portfolio_returns[-min_length:]
            benchmark_returns = benchmark_returns[-min_length:]
            
            if not portfolio_returns or not benchmark_returns:
                return {}
            
            # Calculate comparison metrics
            beta = self._calculate_beta(portfolio_returns, benchmark_returns)
            correlation = self._calculate_correlation(portfolio_returns, benchmark_returns)
            tracking_error = self._calculate_tracking_error(portfolio_returns, benchmark_returns)
            
            # Calculate cumulative returns
            portfolio_cumulative = self._calculate_cumulative_return(portfolio_returns)
            benchmark_cumulative = self._calculate_cumulative_return(benchmark_returns)
            
            alpha = portfolio_cumulative - benchmark_cumulative - (beta * benchmark_cumulative)
            
            return {
                'beta': beta,
                'alpha': alpha,
                'correlation': correlation,
                'tracking_error': tracking_error,
                'portfolio_cumulative_return': portfolio_cumulative,
                'benchmark_cumulative_return': benchmark_cumulative,
                'outperformance': portfolio_cumulative - benchmark_cumulative,
            }
            
        except Exception as e:
            raise Exception(f"Error comparing with benchmark: {str(e)}")
    
    def _calculate_total_return(self, start_value: Decimal, end_value: Decimal) -> Decimal:
        """Calculate total return percentage"""
        if start_value <= 0:
            return Decimal('0.0000')
        
        return ((end_value - start_value) / start_value) * 100
    
    def _calculate_time_weighted_return(self, snapshots: List[PortfolioSnapshot]) -> Decimal:
        """Calculate time-weighted return"""
        if len(snapshots) < 2:
            return Decimal('0.0000')
        
        # For simplified calculation, use geometric mean of daily returns
        daily_returns = self._calculate_daily_returns(snapshots)
        
        if not daily_returns:
            return Decimal('0.0000')
        
        # Calculate geometric mean
        product = Decimal('1.0000')
        for daily_return in daily_returns:
            product *= (1 + daily_return)
        
        if len(daily_returns) == 0:
            return Decimal('0.0000')
        
        geometric_mean = product ** (Decimal('1.0000') / Decimal(str(len(daily_returns))))
        twr = (geometric_mean - 1) * 100
        
        return twr
    
    def _calculate_annualized_return(self, total_return: Decimal, days: int) -> Optional[Decimal]:
        """Calculate annualized return"""
        if days <= 0:
            return None
        
        years = Decimal(str(days)) / Decimal('365.25')
        
        if years <= 0:
            return None
        
        # Convert percentage to decimal, annualize, then back to percentage
        decimal_return = total_return / 100
        growth_factor = 1 + decimal_return
        
        try:
            annualized_growth = growth_factor ** (1 / float(years))
            annualized_return = (annualized_growth - 1) * 100
            return Decimal(str(round(float(annualized_return), 4)))
        except (OverflowError, ValueError):
            return None
    
    def _calculate_volatility(self, snapshots: List[PortfolioSnapshot]) -> Optional[Decimal]:
        """Calculate annualized volatility"""
        daily_returns = self._calculate_daily_returns(snapshots)
        
        if len(daily_returns) < 2:
            return None
        
        # Calculate standard deviation
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
        
        try:
            std_dev = Decimal(str(math.sqrt(float(variance))))
            # Annualize (multiply by sqrt of 252 trading days)
            annualized_volatility = std_dev * Decimal(str(math.sqrt(252))) * 100
            return annualized_volatility
        except (ValueError, OverflowError):
            return None
    
    def _calculate_max_drawdown(self, snapshots: List[PortfolioSnapshot]) -> Decimal:
        """Calculate maximum drawdown"""
        if len(snapshots) < 2:
            return Decimal('0.0000')
        
        peak = snapshots[0].calculate_total_value_with_cash()
        max_drawdown = Decimal('0.0000')
        
        for snapshot in snapshots[1:]:
            value = snapshot.calculate_total_value_with_cash()
            
            if value > peak:
                peak = value
            else:
                if peak > 0:
                    drawdown = ((peak - value) / peak) * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, annualized_return: Optional[Decimal], volatility: Optional[Decimal]) -> Optional[Decimal]:
        """Calculate Sharpe ratio"""
        if annualized_return is None or volatility is None or volatility == 0:
            return None
        
        excess_return = annualized_return - (self.risk_free_rate * 100)
        sharpe_ratio = excess_return / volatility
        
        return sharpe_ratio
    
    def _calculate_daily_returns(self, snapshots: List[PortfolioSnapshot]) -> List[Decimal]:
        """Calculate daily returns from snapshots"""
        daily_returns = []
        
        for i in range(1, len(snapshots)):
            prev_value = snapshots[i-1].calculate_total_value_with_cash()
            curr_value = snapshots[i].calculate_total_value_with_cash()
            
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
        
        return daily_returns
    
    def _calculate_beta(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Optional[Decimal]:
        """Calculate beta (portfolio sensitivity to benchmark)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return None
        
        try:
            # Calculate means
            port_mean = sum(portfolio_returns) / len(portfolio_returns)
            bench_mean = sum(benchmark_returns) / len(benchmark_returns)
            
            # Calculate covariance and variance
            covariance = sum(
                (p - port_mean) * (b - bench_mean) 
                for p, b in zip(portfolio_returns, benchmark_returns)
            ) / len(portfolio_returns)
            
            benchmark_variance = sum(
                (b - bench_mean) ** 2 for b in benchmark_returns
            ) / len(benchmark_returns)
            
            if benchmark_variance == 0:
                return None
            
            beta = covariance / benchmark_variance
            return Decimal(str(round(float(beta), 4)))
            
        except (ValueError, ZeroDivisionError):
            return None
    
    def _calculate_correlation(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Optional[Decimal]:
        """Calculate correlation coefficient"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return None
        
        try:
            # Calculate means
            port_mean = sum(portfolio_returns) / len(portfolio_returns)
            bench_mean = sum(benchmark_returns) / len(benchmark_returns)
            
            # Calculate correlation components
            numerator = sum(
                (p - port_mean) * (b - bench_mean)
                for p, b in zip(portfolio_returns, benchmark_returns)
            )
            
            port_variance = sum((p - port_mean) ** 2 for p in portfolio_returns)
            bench_variance = sum((b - bench_mean) ** 2 for b in benchmark_returns)
            
            denominator = (port_variance * bench_variance) ** Decimal('0.5')
            
            if denominator == 0:
                return None
            
            correlation = numerator / denominator
            return Decimal(str(round(float(correlation), 4)))
            
        except (ValueError, ZeroDivisionError):
            return None
    
    def _calculate_tracking_error(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Optional[Decimal]:
        """Calculate tracking error (standard deviation of return differences)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return None
        
        try:
            # Calculate return differences
            return_differences = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
            
            # Calculate standard deviation of differences
            mean_diff = sum(return_differences) / len(return_differences)
            variance = sum((d - mean_diff) ** 2 for d in return_differences) / len(return_differences)
            
            tracking_error = Decimal(str(math.sqrt(float(variance)))) * 100  # Convert to percentage
            return tracking_error
            
        except (ValueError, ZeroDivisionError):
            return None
    
    def _calculate_cumulative_return(self, daily_returns: List[Decimal]) -> Decimal:
        """Calculate cumulative return from daily returns"""
        cumulative = Decimal('1.0000')
        
        for daily_return in daily_returns:
            cumulative *= (1 + daily_return)
        
        return (cumulative - 1) * 100
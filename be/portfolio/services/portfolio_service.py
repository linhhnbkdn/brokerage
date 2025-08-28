"""
Portfolio business logic service
"""

from decimal import Decimal
from typing import List, Dict, Optional
from datetime import date, datetime
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from portfolio.models import Position, PortfolioSnapshot, PerformanceMetrics
from banking.models import UserBalance


class PortfolioService:
    """Service for portfolio operations and calculations"""
    
    def __init__(self):
        self.market_data_service = None  # Will be injected via DI
    
    def get_portfolio_overview(self, user: User) -> Dict:
        """
        Get comprehensive portfolio overview for a user
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with portfolio overview data
        """
        try:
            # Get active positions
            positions = Position.objects.filter(user=user, status='active')
            
            # Get cash balance
            cash_balance = self._get_user_cash_balance(user)
            
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
                    'position': position,
                    'current_value': position_value,
                    'cost_basis': position_cost,
                    'unrealized_gain_loss': position.get_unrealized_gain_loss(),
                    'unrealized_gain_loss_percent': position.get_unrealized_gain_loss_percent(),
                })
            
            # Calculate totals and percentages
            total_portfolio_value = total_value + cash_balance
            total_gain_loss = total_value - total_cost_basis
            total_gain_loss_percent = self._calculate_percentage_change(total_cost_basis, total_gain_loss)
            
            # Get daily performance
            day_gain_loss, day_gain_loss_percent = self._calculate_daily_performance(user, total_portfolio_value)
            
            # Calculate asset allocation
            asset_allocation = self._calculate_asset_allocation(positions_data, total_value)
            
            return {
                'total_value': total_value,
                'cash_balance': cash_balance,
                'total_portfolio_value': total_portfolio_value,
                'total_cost_basis': total_cost_basis,
                'total_gain_loss': total_gain_loss,
                'total_gain_loss_percent': total_gain_loss_percent,
                'day_gain_loss': day_gain_loss,
                'day_gain_loss_percent': day_gain_loss_percent,
                'positions_count': len(positions_data),
                'positions_data': positions_data,
                'asset_allocation': asset_allocation,
                'last_updated': timezone.now(),
            }
            
        except Exception as e:
            raise Exception(f"Error calculating portfolio overview: {str(e)}")
    
    @transaction.atomic
    def add_position(self, user: User, position_data: Dict) -> Position:
        """
        Add a new position to user's portfolio
        
        Args:
            user: User instance
            position_data: Dictionary with position details
            
        Returns:
            Created Position instance
        """
        try:
            # Check if position already exists
            existing_position = Position.objects.filter(
                user=user,
                symbol=position_data['symbol'],
                status='active'
            ).first()
            
            if existing_position:
                raise ValueError(f"Active position for {position_data['symbol']} already exists")
            
            # Create new position
            position = Position.objects.create(
                user=user,
                symbol=position_data['symbol'].upper(),
                instrument_type=position_data['instrument_type'],
                name=position_data.get('name', position_data['symbol']),
                quantity=position_data['quantity'],
                average_cost=position_data['average_cost'],
                current_price=position_data.get('current_price', position_data['average_cost']),
            )
            
            # Update current price if market data service is available
            if self.market_data_service:
                try:
                    current_price = self.market_data_service.get_current_price(position.symbol)
                    if current_price:
                        position.update_current_price(current_price)
                        position.save()
                except Exception:
                    pass  # Continue without current price update
            
            return position
            
        except Exception as e:
            raise Exception(f"Error adding position: {str(e)}")
    
    @transaction.atomic
    def update_position(self, position: Position, update_data: Dict) -> Position:
        """
        Update an existing position
        
        Args:
            position: Position instance to update
            update_data: Dictionary with update data
            
        Returns:
            Updated Position instance
        """
        try:
            # Update allowed fields
            updatable_fields = ['quantity', 'average_cost', 'current_price', 'name', 'status']
            
            for field, value in update_data.items():
                if field in updatable_fields and hasattr(position, field):
                    setattr(position, field, value)
            
            position.save()
            return position
            
        except Exception as e:
            raise Exception(f"Error updating position: {str(e)}")
    
    def close_position(self, position: Position) -> Position:
        """
        Close a position (mark as closed)
        
        Args:
            position: Position instance to close
            
        Returns:
            Updated Position instance
        """
        try:
            position.status = 'closed'
            position.closed_at = timezone.now()
            position.save()
            return position
            
        except Exception as e:
            raise Exception(f"Error closing position: {str(e)}")
    
    def update_portfolio_prices(self, user: User) -> int:
        """
        Update current prices for all active positions
        
        Args:
            user: User instance
            
        Returns:
            Number of positions updated
        """
        try:
            if not self.market_data_service:
                raise Exception("Market data service not available")
            
            active_positions = Position.objects.filter(user=user, status='active')
            updated_count = 0
            
            for position in active_positions:
                try:
                    current_price = self.market_data_service.get_current_price(position.symbol)
                    if current_price:
                        position.update_current_price(current_price)
                        position.save()
                        updated_count += 1
                except Exception:
                    continue  # Skip positions with price update errors
            
            return updated_count
            
        except Exception as e:
            raise Exception(f"Error updating portfolio prices: {str(e)}")
    
    def get_portfolio_allocation(self, user: User) -> Dict:
        """
        Get detailed portfolio allocation breakdown
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with allocation data
        """
        try:
            positions = Position.objects.filter(user=user, status='active')
            cash_balance = self._get_user_cash_balance(user)
            
            allocation_data = {}
            total_portfolio_value = cash_balance
            
            # Calculate position values and group by instrument type
            for position in positions:
                position_value = position.get_current_value()
                total_portfolio_value += position_value
                
                instrument_type = position.instrument_type
                if instrument_type not in allocation_data:
                    allocation_data[instrument_type] = {
                        'instrument_type': instrument_type,
                        'total_value': Decimal('0.00'),
                        'positions': [],
                        'count': 0
                    }
                
                allocation_data[instrument_type]['total_value'] += position_value
                allocation_data[instrument_type]['count'] += 1
                allocation_data[instrument_type]['positions'].append({
                    'position_id': position.position_id,
                    'symbol': position.symbol,
                    'value': position_value,
                })
            
            # Calculate percentages
            for instrument_type in allocation_data:
                value = allocation_data[instrument_type]['total_value']
                percentage = self._calculate_percentage(total_portfolio_value, value)
                allocation_data[instrument_type]['percentage'] = percentage
                
                # Calculate individual position percentages
                for position_data in allocation_data[instrument_type]['positions']:
                    position_percentage = self._calculate_percentage(total_portfolio_value, position_data['value'])
                    position_data['percentage'] = position_percentage
            
            # Add cash allocation
            cash_percentage = self._calculate_percentage(total_portfolio_value, cash_balance)
            
            return {
                'total_portfolio_value': total_portfolio_value,
                'cash_balance': cash_balance,
                'cash_percentage': cash_percentage,
                'allocation_by_type': allocation_data,
                'diversification_score': self._calculate_diversification_score(allocation_data)
            }
            
        except Exception as e:
            raise Exception(f"Error calculating portfolio allocation: {str(e)}")
    
    def _get_user_cash_balance(self, user: User) -> Decimal:
        """Get user's available cash balance"""
        try:
            user_balance = UserBalance.objects.get(user=user)
            return user_balance.available_balance
        except UserBalance.DoesNotExist:
            return Decimal('0.00')
    
    def _calculate_daily_performance(self, user: User, current_total_value: Decimal) -> tuple:
        """Calculate daily gain/loss compared to previous day"""
        try:
            from datetime import timedelta
            yesterday = timezone.now().date() - timedelta(days=1)
            
            yesterday_snapshot = PortfolioSnapshot.objects.filter(
                user=user,
                snapshot_date=yesterday
            ).first()
            
            if yesterday_snapshot:
                yesterday_total = yesterday_snapshot.calculate_total_value_with_cash()
                day_gain_loss = current_total_value - yesterday_total
                day_gain_loss_percent = self._calculate_percentage_change(yesterday_total, day_gain_loss)
                return day_gain_loss, day_gain_loss_percent
            
            return None, None
            
        except Exception:
            return None, None
    
    def _calculate_asset_allocation(self, positions_data: List[Dict], total_value: Decimal) -> Dict:
        """Calculate asset allocation by instrument type"""
        allocation = {}
        
        if total_value == 0:
            return allocation
        
        for position_data in positions_data:
            position = position_data['position']
            position_value = position_data['current_value']
            
            instrument_type = position.instrument_type
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
            value = allocation[instrument_type]['value']
            percentage = self._calculate_percentage(total_value, value)
            allocation[instrument_type]['percentage'] = percentage
        
        return allocation
    
    def _calculate_percentage(self, total: Decimal, value: Decimal) -> Decimal:
        """Calculate percentage with safety check"""
        if total == 0:
            return Decimal('0.00')
        return (value / total) * 100
    
    def _calculate_percentage_change(self, original: Decimal, change: Decimal) -> Decimal:
        """Calculate percentage change with safety check"""
        if original == 0:
            return Decimal('0.00')
        return (change / original) * 100
    
    def _calculate_diversification_score(self, allocation_data: Dict) -> Decimal:
        """
        Calculate a simple diversification score (0-100)
        Higher score means better diversification
        """
        if not allocation_data:
            return Decimal('0.00')
        
        # Simple diversification: more instrument types = higher score
        num_types = len(allocation_data)
        max_types = 7  # Maximum expected instrument types
        
        # Base score from number of types
        type_score = min(num_types / max_types, 1.0) * 50
        
        # Additional score based on balance (penalize concentration)
        concentration_penalty = 0
        for type_data in allocation_data.values():
            percentage = float(type_data['percentage'])
            if percentage > 60:  # Heavy concentration penalty
                concentration_penalty += (percentage - 60) * 0.5
        
        balance_score = max(0, 50 - concentration_penalty)
        
        total_score = type_score + balance_score
        return Decimal(str(round(total_score, 2)))
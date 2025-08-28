"""
Position management API views
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from .base import BasePortfolioModelViewSet
from portfolio.models import Position
from portfolio.serializers import (
    PositionSerializer,
    PositionSummarySerializer,
    PositionCreateSerializer
)


class PositionViewSet(BasePortfolioModelViewSet):
    """Position CRUD operations"""
    
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    lookup_field = 'position_id'
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return PositionSummarySerializer
        elif self.action == 'create':
            return PositionCreateSerializer
        return PositionSerializer
    
    def list(self, request):
        """
        GET /api/portfolio/positions/
        List user's portfolio positions
        """
        try:
            queryset = self.get_queryset()
            
            # Filter by status if provided
            status_filter = request.query_params.get('status', 'active')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            # Filter by instrument type if provided
            instrument_type = request.query_params.get('instrument_type')
            if instrument_type:
                queryset = queryset.filter(instrument_type=instrument_type)
            
            # Order by creation date (newest first)
            queryset = queryset.order_by('-created_at')
            
            serializer = self.get_serializer(queryset, many=True)
            
            # Add summary statistics
            total_positions = queryset.count()
            total_value = sum(pos.get_current_value() for pos in queryset)
            total_cost_basis = sum(pos.get_cost_basis() for pos in queryset)
            total_gain_loss = total_value - total_cost_basis
            
            response_data = {
                'positions': serializer.data,
                'summary': {
                    'total_positions': total_positions,
                    'total_value': str(total_value),
                    'total_cost_basis': str(total_cost_basis),
                    'total_gain_loss': str(total_gain_loss),
                    'total_gain_loss_percent': str((total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0)
                }
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving positions: {str(e)}")
    
    def retrieve(self, request, position_id=None):
        """
        GET /api/portfolio/positions/{position_id}/
        Get detailed position information
        """
        try:
            position = self.get_queryset().get(position_id=position_id)
            serializer = PositionSerializer(position)
            return self.handle_success_response(serializer.data)
            
        except Position.DoesNotExist:
            return self.handle_error_response("Position not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error retrieving position: {str(e)}")
    
    @transaction.atomic
    def create(self, request):
        """
        POST /api/portfolio/positions/
        Create a new position
        """
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            
            if not serializer.is_valid():
                return Response({
                    "error": True,
                    "message": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if position already exists for this symbol
            existing_position = Position.objects.filter(
                user=request.user,
                symbol=serializer.validated_data['symbol'],
                status='active'
            ).first()
            
            if existing_position:
                return self.handle_error_response(
                    f"Active position for {serializer.validated_data['symbol']} already exists"
                )
            
            position = serializer.save()
            response_serializer = PositionSerializer(position)
            
            return self.handle_success_response(
                response_serializer.data,
                "Position created successfully",
                status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return self.handle_error_response(f"Error creating position: {str(e)}")
    
    @transaction.atomic
    def update(self, request, position_id=None):
        """
        PUT /api/portfolio/positions/{position_id}/
        Update position (mainly for adjusting cost basis, quantity)
        """
        try:
            position = self.get_queryset().get(position_id=position_id)
            serializer = PositionSerializer(position, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    "error": True,
                    "message": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            updated_position = serializer.save()
            
            return self.handle_success_response(
                PositionSerializer(updated_position).data,
                "Position updated successfully"
            )
            
        except Position.DoesNotExist:
            return self.handle_error_response("Position not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error updating position: {str(e)}")
    
    def destroy(self, request, position_id=None):
        """
        DELETE /api/portfolio/positions/{position_id}/
        Close/delete a position
        """
        try:
            position = self.get_queryset().get(position_id=position_id)
            
            # Instead of deleting, mark as closed
            position.status = 'closed'
            position.save()
            
            return Response({
                "error": False,
                "message": "Position closed successfully"
            }, status=status.HTTP_204_NO_CONTENT)
            
        except Position.DoesNotExist:
            return self.handle_error_response("Position not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error closing position: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def update_price(self, request, position_id=None):
        """
        POST /api/portfolio/positions/{position_id}/update_price/
        Update current market price for a position
        """
        try:
            position = self.get_queryset().get(position_id=position_id)
            
            new_price = request.data.get('current_price')
            if not new_price:
                return self.handle_error_response("current_price is required")
            
            try:
                from decimal import Decimal
                new_price = Decimal(str(new_price))
                if new_price <= 0:
                    raise ValueError("Price must be positive")
            except (ValueError, TypeError):
                return self.handle_error_response("Invalid price format")
            
            position.update_current_price(new_price)
            position.save()
            
            serializer = PositionSerializer(position)
            return self.handle_success_response(
                serializer.data,
                "Position price updated successfully"
            )
            
        except Position.DoesNotExist:
            return self.handle_error_response("Position not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error updating price: {str(e)}")
    
    @action(detail=True, methods=['get'])
    def performance(self, request, position_id=None):
        """
        GET /api/portfolio/positions/{position_id}/performance/
        Get individual position performance data
        """
        try:
            position = self.get_queryset().get(position_id=position_id)
            
            # TODO: In a real implementation, you'd get historical price data
            # For now, return current performance metrics
            
            performance_data = {
                'position_id': str(position.position_id),
                'symbol': position.symbol,
                'current_performance': {
                    'cost_basis': str(position.get_cost_basis()),
                    'current_value': str(position.get_current_value()),
                    'unrealized_gain_loss': str(position.get_unrealized_gain_loss()),
                    'unrealized_gain_loss_percent': str(position.get_unrealized_gain_loss_percent()),
                    'is_profitable': position.is_profitable(),
                },
                'historical_data': [],  # TODO: Implement historical price tracking
                'last_updated': position.last_price_update,
            }
            
            return self.handle_success_response(performance_data)
            
        except Position.DoesNotExist:
            return self.handle_error_response("Position not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_error_response(f"Error retrieving performance: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def allocation(self, request):
        """
        GET /api/portfolio/positions/allocation/
        Get portfolio allocation breakdown
        """
        try:
            positions = self.get_queryset().filter(status='active')
            
            allocation_data = {}
            total_value = sum(pos.get_current_value() for pos in positions)
            
            for position in positions:
                instrument_type = position.instrument_type
                position_value = position.get_current_value()
                
                if instrument_type not in allocation_data:
                    allocation_data[instrument_type] = {
                        'instrument_type': instrument_type,
                        'value': 0,
                        'percentage': 0,
                        'count': 0,
                        'positions': []
                    }
                
                allocation_data[instrument_type]['value'] += position_value
                allocation_data[instrument_type]['count'] += 1
                allocation_data[instrument_type]['positions'].append({
                    'position_id': str(position.position_id),
                    'symbol': position.symbol,
                    'value': str(position_value),
                    'percentage': str((position_value / total_value * 100) if total_value > 0 else 0)
                })
            
            # Calculate percentages
            for instrument_type in allocation_data:
                value = allocation_data[instrument_type]['value']
                allocation_data[instrument_type]['percentage'] = str((value / total_value * 100) if total_value > 0 else 0)
                allocation_data[instrument_type]['value'] = str(value)
            
            response_data = {
                'total_value': str(total_value),
                'allocation': list(allocation_data.values())
            }
            
            return self.handle_success_response(response_data)
            
        except Exception as e:
            return self.handle_error_response(f"Error retrieving allocation: {str(e)}")
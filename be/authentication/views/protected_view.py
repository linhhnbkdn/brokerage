"""
Protected endpoint example.
"""
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ..decorators import jwt_required


@extend_schema(
    summary="Protected endpoint",
    description="Example protected endpoint requiring JWT authentication",
    responses={
        200: {
            'application/json': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user_id': {'type': 'integer'},
                    'username': {'type': 'string'}
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
@jwt_required
def protected_endpoint(request) -> Response:
    """Example protected endpoint requiring JWT authentication."""
    user_id = request.user_id
    try:
        user = User.objects.get(id=user_id)
        return Response({
            'message': 'Access granted',
            'user_id': user_id,
            'username': user.username
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
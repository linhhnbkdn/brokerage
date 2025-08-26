"""
Protected endpoint example.
"""
from django.contrib.auth.models import User
from django.http import JsonResponse

from ..decorators import jwt_required


@jwt_required
def protected_endpoint(request) -> JsonResponse:
    """Example protected endpoint requiring JWT authentication."""
    user_id = request.user_id
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'message': 'Access granted',
            'user_id': user_id,
            'username': user.username
        })
    except User.DoesNotExist:
        return JsonResponse(
            {'error': 'User not found'},
            status=404
        )
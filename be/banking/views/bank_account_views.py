"""
Bank account management API views
"""

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator

from .base import BankingBaseView
from ..services import BankAccountService
from authentication.decorators import jwt_required


@method_decorator(jwt_required, name="post")
class LinkBankAccountView(BankingBaseView):
    """
    API endpoint for linking a new bank account
    POST /api/banking/link-account/
    """

    permission_classes = [AllowAny]  # JWT handled by decorator

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bank_account_service = BankAccountService()

    def post(self, request):
        """Link a new bank account to the user"""
        try:
            # Get user from JWT token
            from django.contrib.auth.models import User

            user = User.objects.get(id=request.user_id)

            account_data = request.data
            result = self.bank_account_service.create_bank_account(user, account_data)
            return Response(result, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"error": str(e.message) if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return self.handle_service_error(e)


@method_decorator(jwt_required, name="get")
class BankAccountListView(BankingBaseView):
    """
    API endpoint for retrieving user's bank accounts
    GET /api/banking/accounts/
    """

    permission_classes = [AllowAny]  # JWT handled by decorator

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bank_account_service = BankAccountService()

    def get(self, request):
        """Get all bank accounts for the authenticated user"""
        try:
            # Get user from JWT token
            from django.contrib.auth.models import User

            user = User.objects.get(id=request.user_id)

            accounts = self.bank_account_service.get_user_bank_accounts(user)
            return Response({"accounts": accounts}, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_service_error(e)

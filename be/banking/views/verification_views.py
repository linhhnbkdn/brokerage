"""
Account verification API views
"""

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator

from .base import BankingBaseView
from authentication.decorators import jwt_required


@method_decorator(jwt_required, name="post")
class VerifyBankAccountView(BankingBaseView):
    """
    API endpoint for verifying bank account with micro-deposits
    POST /api/banking/verify-account/
    """

    permission_classes = [AllowAny]  # JWT handled by decorator

    def post(self, request):
        """Verify bank account using micro-deposit amounts"""
        try:
            from decimal import Decimal, InvalidOperation
            from django.contrib.auth.models import User
            from ..services import BankAccountService

            # Get user from JWT token
            user = User.objects.get(id=request.user_id)
            bank_account_service = BankAccountService()

            # Extract data from request
            account_link_id = request.data.get("account_link_id")
            deposit_amounts = request.data.get("deposit_amounts", [])

            if not account_link_id or not deposit_amounts:
                return Response(
                    {"error": "account_link_id and deposit_amounts are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(deposit_amounts) != 2:
                return Response(
                    {"error": "deposit_amounts must contain exactly 2 amounts"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Convert amounts to Decimal
            try:
                amount1 = Decimal(str(deposit_amounts[0]))
                amount2 = Decimal(str(deposit_amounts[1]))
            except (InvalidOperation, TypeError, ValueError):
                return Response(
                    {"error": "Invalid deposit amounts format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the bank account
            try:
                bank_account = bank_account_service.get_account_by_link_id(
                    user, account_link_id
                )
            except Exception:
                return Response(
                    {"error": "Bank account not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check if account can attempt verification
            if not bank_account.can_attempt_verification():
                return Response(
                    {"error": "Maximum verification attempts exceeded"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify micro-deposits
            verification_successful = bank_account.verify_micro_deposits(amount1, amount2)

            if verification_successful:
                return Response(
                    {"status": "verified", "message": "Account verified successfully"},
                    status=status.HTTP_200_OK,
                )
            else:
                attempts_remaining = 3 - bank_account.verification_attempts
                return Response(
                    {
                        "error": "Incorrect deposit amounts",
                        "attempts_remaining": attempts_remaining,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return self.handle_service_error(e)

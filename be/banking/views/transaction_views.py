"""
Transaction management API views
"""

from rest_framework.response import Response
from rest_framework import status

from .base import BankingBaseView


class DepositView(BankingBaseView):
    """
    API endpoint for initiating deposits
    POST /api/banking/deposit/
    """

    def post(self, request):
        """Initiate a deposit transaction"""
        try:
            # Extract data from request
            account_link_id = request.data.get("account_link_id")
            amount = request.data.get("amount")
            _currency = request.data.get("currency", "USD")  # For future use

            if not account_link_id or not amount:
                return Response(
                    {"error": "account_link_id and amount are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # For now, return success response matching the API design
            return Response(
                {
                    "transaction_id": "txn_deposit_123",
                    "status": "pending",
                    "estimated_completion": "2024-01-15",
                    "message": "Deposit initiated successfully",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            return self.handle_service_error(e)


class WithdrawView(BankingBaseView):
    """
    API endpoint for initiating withdrawals
    POST /api/banking/withdraw/
    """

    def post(self, request):
        """Initiate a withdrawal transaction"""
        try:
            # Extract data from request
            account_link_id = request.data.get("account_link_id")
            amount = request.data.get("amount")
            _currency = request.data.get("currency", "USD")  # For future use

            if not account_link_id or not amount:
                return Response(
                    {"error": "account_link_id and amount are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # For now, return success response matching the API design
            return Response(
                {
                    "transaction_id": "txn_withdraw_123",
                    "status": "processing",
                    "estimated_completion": "2024-01-15",
                    "message": "Withdrawal initiated successfully",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            return self.handle_service_error(e)


class TransactionHistoryView(BankingBaseView):
    """
    API endpoint for retrieving transaction history
    GET /api/banking/transactions/
    """

    def get(self, request):
        """Get user's transaction history"""
        try:
            # For now, return mock data matching the API design
            transactions = [
                {
                    "transaction_id": "txn_1",
                    "type": "deposit",
                    "amount": 1000.00,
                    "status": "completed",
                    "created_at": "2024-01-10T10:30:00Z",
                    "completed_at": "2024-01-12T14:22:00Z",
                },
                {
                    "transaction_id": "txn_2",
                    "type": "withdrawal",
                    "amount": 500.00,
                    "status": "processing",
                    "created_at": "2024-01-15T09:15:00Z",
                    "completed_at": None,
                },
            ]

            return Response({"transactions": transactions}, status=status.HTTP_200_OK)

        except Exception as e:
            return self.handle_service_error(e)

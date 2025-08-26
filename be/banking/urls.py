"""
URL patterns for banking API endpoints
"""

from django.urls import path

from .views import (
    LinkBankAccountView,
    BankAccountListView,
    DepositView,
    WithdrawView,
    VerifyBankAccountView,
    TransactionHistoryView,
)

urlpatterns = [
    path("link-account/", LinkBankAccountView.as_view(), name="link-account"),
    path("accounts/", BankAccountListView.as_view(), name="bank-accounts"),
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("withdraw/", WithdrawView.as_view(), name="withdraw"),
    path("verify-account/", VerifyBankAccountView.as_view(), name="verify-account"),
    path("transactions/", TransactionHistoryView.as_view(), name="transactions"),
]

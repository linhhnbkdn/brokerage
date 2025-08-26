"""
Bank Account Service implementing business logic for bank account operations
Following Single Responsibility and Dependency Injection principles
"""

from typing import Dict, List
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import BankAccount
from .interfaces import BankAccountServiceInterface
from .validation_service import ValidationService


class BankAccountService(BankAccountServiceInterface):
    """
    Service for managing bank account operations
    Handles creation, validation, and management of bank accounts
    """

    def __init__(self, validation_service=None):
        """Initialize with optional validation service dependency"""
        self.validation_service = validation_service or ValidationService()

    def create_bank_account(self, user: User, account_data: Dict) -> Dict:
        """
        Create a new bank account link for the user

        Args:
            user: The user to link the account to
            account_data: Dictionary containing account details

        Returns:
            Dict containing account information and status

        Raises:
            ValidationError: If account data is invalid
        """
        # Validate required fields
        required_fields = [
            "bank_routing_number",
            "account_number",
            "account_type",
            "account_holder_name",
        ]

        for field in required_fields:
            if field not in account_data or not account_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Validate routing number
        routing_number = account_data["bank_routing_number"]
        if not self.validation_service.validate_routing_number(routing_number):
            raise ValidationError("Invalid routing number")

        # Validate account number
        account_number = account_data["account_number"]
        if not self.validation_service.validate_account_number(account_number):
            raise ValidationError("Invalid account number")

        # Validate account type
        if account_data["account_type"] not in ["checking", "savings"]:
            raise ValidationError("Invalid account type")

        # Check for duplicate accounts (same routing + account number)
        existing_account = BankAccount.objects.filter(
            user=user,
            bank_routing_number=routing_number,
            status__in=["pending_verification", "verified"],
        ).first()

        if existing_account:
            # Check if account numbers match (decrypt existing)
            if existing_account.get_account_number() == account_number:
                raise ValidationError("This bank account is already linked")

        # Create the bank account
        with transaction.atomic():
            bank_account = BankAccount(
                user=user,
                bank_name=self._get_bank_name_from_routing(routing_number),
                bank_routing_number=routing_number,
                account_type=account_data["account_type"],
                account_holder_name=account_data["account_holder_name"].strip(),
            )

            # Set encrypted account number
            bank_account.set_account_number(account_number)

            # Generate micro-deposits for verification
            bank_account.generate_micro_deposits()

            bank_account.save()

        return {
            "account_link_id": str(bank_account.account_link_id),
            "status": bank_account.status,
            "bank_name": bank_account.bank_name,
            "account_type": bank_account.account_type,
            "last_four_digits": bank_account.get_last_four_digits(),
            "micro_deposits_required": True,
            "verification_deadline": bank_account.micro_deposits_sent_at,
        }

    def get_user_bank_accounts(self, user: User) -> List[Dict]:
        """Get all active bank accounts for a user"""
        accounts = BankAccount.objects.filter(
            user=user, status__in=["pending_verification", "verified", "suspended"]
        ).order_by("-created_at")

        return [account.get_masked_account_info() for account in accounts]

    def get_verified_accounts(self, user: User) -> List[Dict]:
        """Get only verified bank accounts for a user"""
        accounts = BankAccount.objects.filter(user=user, status="verified").order_by(
            "-last_used_at", "-created_at"
        )

        return [account.get_masked_account_info() for account in accounts]

    def get_account_by_link_id(self, user: User, account_link_id: str) -> BankAccount:
        """Get bank account by link ID, ensuring user ownership"""
        try:
            return BankAccount.objects.get(account_link_id=account_link_id, user=user)
        except BankAccount.DoesNotExist:
            raise ValidationError("Bank account not found")

    def deactivate_account(self, user: User, account_link_id: str) -> bool:
        """Deactivate a bank account"""
        try:
            account = self.get_account_by_link_id(user, account_link_id)
            account.status = "closed"
            account.save(update_fields=["status"])
            return True
        except ValidationError:
            return False

    def _get_bank_name_from_routing(self, routing_number: str) -> str:
        """
        Get bank name from routing number
        In production, this would use a real bank database
        """
        bank_map = {
            "021000021": "JPMorgan Chase Bank",
            "026009593": "Bank of America",
            "121000358": "Bank of America",
            "122000247": "Wells Fargo Bank",
            "121042882": "Wells Fargo Bank",
            "111000025": "Federal Reserve Bank",
            "021000089": "Fleet National Bank",
        }

        return bank_map.get(routing_number, "Unknown Bank")

    def update_account_usage(self, account_link_id: str):
        """Update last used timestamp for an account"""
        try:
            account = BankAccount.objects.get(account_link_id=account_link_id)
            account.update_last_used()
        except BankAccount.DoesNotExist:
            pass  # Silently ignore if account not found

"""
Service interfaces defining contracts for banking operations
Following Interface Segregation Principle from SOLID
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from decimal import Decimal
from django.contrib.auth.models import User


class BankAccountServiceInterface(ABC):
    """Interface for bank account operations"""

    @abstractmethod
    def create_bank_account(self, user: User, account_data: Dict) -> Dict:
        """Create a new bank account link"""
        pass

    @abstractmethod
    def get_user_bank_accounts(self, user: User) -> List[Dict]:
        """Get all bank accounts for a user"""
        pass

    @abstractmethod
    def get_verified_accounts(self, user: User) -> List[Dict]:
        """Get only verified bank accounts for a user"""
        pass

    @abstractmethod
    def deactivate_account(self, user: User, account_link_id: str) -> bool:
        """Deactivate a bank account"""
        pass


class TransactionServiceInterface(ABC):
    """Interface for transaction operations"""

    @abstractmethod
    def initiate_deposit(
        self, user: User, account_link_id: str, amount: Decimal
    ) -> Dict:
        """Initiate a deposit transaction"""
        pass

    @abstractmethod
    def initiate_withdrawal(
        self, user: User, account_link_id: str, amount: Decimal
    ) -> Dict:
        """Initiate a withdrawal transaction"""
        pass

    @abstractmethod
    def get_transaction_history(
        self, user: User, filters: Dict = None, limit: int = 20
    ) -> List[Dict]:
        """Get user transaction history"""
        pass

    @abstractmethod
    def process_transaction(self, transaction_id: str) -> bool:
        """Process a pending transaction"""
        pass


class VerificationServiceInterface(ABC):
    """Interface for account verification operations"""

    @abstractmethod
    def send_micro_deposits(self, account_link_id: str) -> bool:
        """Send micro-deposits for account verification"""
        pass

    @abstractmethod
    def verify_micro_deposits(
        self, user: User, account_link_id: str, amounts: Tuple[Decimal, Decimal]
    ) -> Dict:
        """Verify micro-deposit amounts"""
        pass


class BalanceServiceInterface(ABC):
    """Interface for balance management operations"""

    @abstractmethod
    def get_user_balance(self, user: User) -> Dict:
        """Get user's current balance information"""
        pass

    @abstractmethod
    def can_withdraw(self, user: User, amount: Decimal) -> bool:
        """Check if user can withdraw specified amount"""
        pass

    @abstractmethod
    def update_balance_after_deposit(self, user: User, amount: Decimal) -> bool:
        """Update balance after successful deposit"""
        pass

    @abstractmethod
    def update_balance_after_withdrawal(self, user: User, amount: Decimal) -> bool:
        """Update balance after successful withdrawal"""
        pass


class ValidationServiceInterface(ABC):
    """Interface for validation operations"""

    @abstractmethod
    def validate_routing_number(self, routing_number: str) -> bool:
        """Validate bank routing number"""
        pass

    @abstractmethod
    def validate_account_number(self, account_number: str) -> bool:
        """Validate bank account number"""
        pass

    @abstractmethod
    def validate_deposit_amount(self, amount: Decimal) -> Tuple[bool, str]:
        """Validate deposit amount"""
        pass

    @abstractmethod
    def validate_withdrawal_amount(
        self, user: User, amount: Decimal
    ) -> Tuple[bool, str]:
        """Validate withdrawal amount"""
        pass

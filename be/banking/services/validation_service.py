"""
Validation Service for banking operations
Implements validation rules and business logic constraints
"""

import re
from typing import Tuple
from decimal import Decimal
from django.contrib.auth.models import User

from .interfaces import ValidationServiceInterface


class ValidationService(ValidationServiceInterface):
    """
    Service for validating banking-related data
    Implements various validation rules for security and compliance
    """

    # Validation constants
    MIN_DEPOSIT_AMOUNT = Decimal("1.00")
    MAX_DEPOSIT_AMOUNT = Decimal("50000.00")
    MIN_WITHDRAWAL_AMOUNT = Decimal("10.00")
    MAX_WITHDRAWAL_AMOUNT = Decimal("50000.00")

    # Routing number validation
    VALID_ROUTING_PREFIXES = [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
    ]

    def validate_routing_number(self, routing_number: str) -> bool:
        """
        Validate bank routing number using check digit algorithm

        Args:
            routing_number: 9-digit routing number string

        Returns:
            bool: True if valid, False otherwise
        """
        if not routing_number or not isinstance(routing_number, str):
            return False

        # Must be exactly 9 digits
        if not re.match(r"^\d{9}$", routing_number):
            return False

        # Check valid prefix
        prefix = routing_number[:2]
        if prefix not in self.VALID_ROUTING_PREFIXES:
            return False

        # Calculate check digit using ABA algorithm
        return self._validate_routing_check_digit(routing_number)

    def _validate_routing_check_digit(self, routing_number: str) -> bool:
        """Validate routing number using ABA check digit algorithm"""
        weights = [3, 7, 1, 3, 7, 1, 3, 7, 1]
        total = sum(
            int(digit) * weight for digit, weight in zip(routing_number, weights)
        )
        return total % 10 == 0

    def validate_account_number(self, account_number: str) -> bool:
        """
        Validate bank account number format

        Args:
            account_number: Account number string

        Returns:
            bool: True if valid, False otherwise
        """
        if not account_number or not isinstance(account_number, str):
            return False

        # Remove any spaces or dashes
        clean_number = re.sub(r"[\s-]", "", account_number)

        # Must be 4-17 digits (standard range for US bank accounts)
        if not re.match(r"^\d{4,17}$", clean_number):
            return False

        return True

    def validate_deposit_amount(self, amount: Decimal) -> Tuple[bool, str]:
        """
        Validate deposit amount against business rules

        Args:
            amount: Deposit amount

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not isinstance(amount, Decimal):
            return False, "Amount must be a decimal value"

        if amount <= 0:
            return False, "Deposit amount must be greater than zero"

        if amount < self.MIN_DEPOSIT_AMOUNT:
            return False, f"Minimum deposit amount is ${self.MIN_DEPOSIT_AMOUNT}"

        if amount > self.MAX_DEPOSIT_AMOUNT:
            return False, f"Maximum deposit amount is ${self.MAX_DEPOSIT_AMOUNT}"

        # Check for reasonable precision (max 2 decimal places)
        if amount.as_tuple().exponent < -2:
            return False, "Amount cannot have more than 2 decimal places"

        return True, ""

    def validate_withdrawal_amount(
        self, user: User, amount: Decimal
    ) -> Tuple[bool, str]:
        """
        Validate withdrawal amount against business rules and user balance

        Args:
            user: User requesting withdrawal
            amount: Withdrawal amount

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not isinstance(amount, Decimal):
            return False, "Amount must be a decimal value"

        if amount <= 0:
            return False, "Withdrawal amount must be greater than zero"

        if amount < self.MIN_WITHDRAWAL_AMOUNT:
            return (
                False,
                f"Minimum withdrawal amount is ${self.MIN_WITHDRAWAL_AMOUNT}",
            )

        if amount > self.MAX_WITHDRAWAL_AMOUNT:
            return (
                False,
                f"Maximum withdrawal amount is ${self.MAX_WITHDRAWAL_AMOUNT}",
            )

        # Check for reasonable precision (max 2 decimal places)
        if amount.as_tuple().exponent < -2:
            return False, "Amount cannot have more than 2 decimal places"

        # Check user balance (if balance exists)
        try:
            user_balance = user.account_balance
            if not user_balance.can_withdraw_today(amount):
                return False, "Insufficient balance or daily limit exceeded"
        except AttributeError:
            # User has no balance record, allow for now
            pass

        return True, ""

    def validate_account_holder_name(self, name: str) -> bool:
        """
        Validate account holder name format

        Args:
            name: Account holder name

        Returns:
            bool: True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False

        name = name.strip()

        # Must be at least 2 characters
        if len(name) < 2:
            return False

        # Must be at most 100 characters
        if len(name) > 100:
            return False

        # Should contain only letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            return False

        return True

    def validate_currency(self, currency: str) -> bool:
        """
        Validate currency code

        Args:
            currency: 3-letter currency code

        Returns:
            bool: True if valid, False otherwise
        """
        # For now, only support USD
        return currency == "USD"

    def validate_daily_limits(
        self, user: User, transaction_type: str, amount: Decimal
    ) -> Tuple[bool, str]:
        """
        Validate transaction against daily limits

        Args:
            user: User making the transaction
            transaction_type: 'deposit' or 'withdrawal'
            amount: Transaction amount

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            user_balance = user.account_balance
            user_balance.reset_daily_limits_if_needed()

            if transaction_type == "deposit":
                if not user_balance.can_deposit_today(amount):
                    remaining = user_balance.get_remaining_daily_deposit_limit()
                    return (
                        False,
                        f"Daily deposit limit exceeded. Remaining: ${remaining}",
                    )

            elif transaction_type == "withdrawal":
                if not user_balance.can_withdraw_today(amount):
                    remaining = user_balance.get_remaining_daily_withdrawal_limit()
                    return (
                        False,
                        f"Daily withdrawal limit exceeded. Remaining: ${remaining}",
                    )

        except AttributeError:
            # User has no balance record, allow for now
            pass

        return True, ""

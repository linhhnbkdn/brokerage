"""
Unit tests for ValidationService
Comprehensive test coverage for all validation functionality
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from banking.services.validation_service import ValidationService
from banking.models import UserBalance


class ValidationServiceTest(TestCase):
    """Test cases for ValidationService"""

    def setUp(self):
        """Set up test data"""
        self.validation_service = ValidationService()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_validate_routing_number_valid(self):
        """Test validation of valid routing numbers"""
        valid_routing_numbers = [
            "021000021",  # Chase
            "026009593",  # Bank of America
            "122000247",  # Wells Fargo
        ]

        for routing_number in valid_routing_numbers:
            with self.subTest(routing_number=routing_number):
                result = self.validation_service.validate_routing_number(routing_number)
                self.assertTrue(result)

    def test_validate_routing_number_invalid_format(self):
        """Test validation of invalid routing number formats"""
        invalid_routing_numbers = [
            "12345678",  # Too short
            "1234567890",  # Too long
            "abcdefghi",  # Non-numeric
            "021000020",  # Invalid check digit
            "",  # Empty
            None,  # None
        ]

        for routing_number in invalid_routing_numbers:
            with self.subTest(routing_number=routing_number):
                result = self.validation_service.validate_routing_number(routing_number)
                self.assertFalse(result)

    def test_validate_routing_number_invalid_prefix(self):
        """Test validation of routing numbers with invalid prefixes"""
        invalid_prefixes = ["00", "13", "33", "99"]

        for prefix in invalid_prefixes:
            routing_number = f"{prefix}1000021"
            with self.subTest(routing_number=routing_number):
                result = self.validation_service.validate_routing_number(routing_number)
                self.assertFalse(result)

    def test_validate_account_number_valid(self):
        """Test validation of valid account numbers"""
        valid_account_numbers = [
            "1234",  # Minimum length
            "12345678901234567",  # Maximum length
            "1234567890",  # Common length
            "123-456-7890",  # With dashes
            "123 456 7890",  # With spaces
        ]

        for account_number in valid_account_numbers:
            with self.subTest(account_number=account_number):
                result = self.validation_service.validate_account_number(account_number)
                self.assertTrue(result)

    def test_validate_account_number_invalid(self):
        """Test validation of invalid account numbers"""
        invalid_account_numbers = [
            "123",  # Too short
            "123456789012345678",  # Too long
            "abcd1234",  # Contains letters
            "",  # Empty
            None,  # None
            "12#34",  # Special characters
        ]

        for account_number in invalid_account_numbers:
            with self.subTest(account_number=account_number):
                result = self.validation_service.validate_account_number(account_number)
                self.assertFalse(result)

    def test_validate_deposit_amount_valid(self):
        """Test validation of valid deposit amounts"""
        valid_amounts = [
            Decimal("1.00"),  # Minimum
            Decimal("100.00"),  # Common amount
            Decimal("50000.00"),  # Maximum
            Decimal("1234.56"),  # With cents
        ]

        for amount in valid_amounts:
            with self.subTest(amount=amount):
                is_valid, error = self.validation_service.validate_deposit_amount(
                    amount
                )
                self.assertTrue(is_valid)
                self.assertEqual(error, "")

    def test_validate_deposit_amount_invalid(self):
        """Test validation of invalid deposit amounts"""
        test_cases = [
            (Decimal("0.00"), "Deposit amount must be greater than zero"),
            (Decimal("-10.00"), "Deposit amount must be greater than zero"),
            (Decimal("0.50"), "Minimum deposit amount is $1.00"),
            (Decimal("50001.00"), "Maximum deposit amount is $50000.00"),
            (Decimal("10.123"), "Amount cannot have more than 2 decimal places"),
        ]

        for amount, expected_error in test_cases:
            with self.subTest(amount=amount):
                is_valid, error = self.validation_service.validate_deposit_amount(
                    amount
                )
                self.assertFalse(is_valid)
                self.assertEqual(error, expected_error)

    def test_validate_deposit_amount_invalid_type(self):
        """Test deposit amount validation with invalid type"""
        is_valid, error = self.validation_service.validate_deposit_amount("100.00")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Amount must be a decimal value")

    def test_validate_withdrawal_amount_valid(self):
        """Test validation of valid withdrawal amounts"""
        # Create user balance with sufficient funds
        UserBalance.objects.create(
            user=self.user, available_balance=Decimal("10000.00")
        )

        valid_amounts = [
            Decimal("10.00"),  # Minimum
            Decimal("100.00"),  # Common amount
            Decimal("1000.00"),  # Larger amount
        ]

        for amount in valid_amounts:
            with self.subTest(amount=amount):
                is_valid, error = self.validation_service.validate_withdrawal_amount(
                    self.user, amount
                )
                self.assertTrue(is_valid)
                self.assertEqual(error, "")

    def test_validate_withdrawal_amount_invalid(self):
        """Test validation of invalid withdrawal amounts"""
        # Create user balance
        UserBalance.objects.create(user=self.user, available_balance=Decimal("100.00"))

        test_cases = [
            (Decimal("0.00"), "Withdrawal amount must be greater than zero"),
            (Decimal("-10.00"), "Withdrawal amount must be greater than zero"),
            (Decimal("5.00"), "Minimum withdrawal amount is $10.00"),
            (Decimal("50001.00"), "Maximum withdrawal amount is $50000.00"),
            (Decimal("10.123"), "Amount cannot have more than 2 decimal places"),
            (Decimal("200.00"), "Insufficient balance or daily limit exceeded"),
        ]

        for amount, expected_error in test_cases:
            with self.subTest(amount=amount):
                is_valid, error = self.validation_service.validate_withdrawal_amount(
                    self.user, amount
                )
                self.assertFalse(is_valid)
                self.assertEqual(error, expected_error)

    def test_validate_withdrawal_amount_no_balance(self):
        """Test withdrawal validation when user has no balance record"""
        user_no_balance = User.objects.create_user(
            username="nobalance", email="nobalance@example.com", password="testpass123"
        )

        is_valid, error = self.validation_service.validate_withdrawal_amount(
            user_no_balance, Decimal("100.00")
        )
        self.assertTrue(is_valid)  # Should allow when no balance record exists

    def test_validate_account_holder_name_valid(self):
        """Test validation of valid account holder names"""
        valid_names = [
            "John Doe",
            "Jane Smith-Jones",
            "Mary O'Connor",
            "Dr. Robert Johnson Jr.",
            "Anne-Marie",
        ]

        for name in valid_names:
            with self.subTest(name=name):
                result = self.validation_service.validate_account_holder_name(name)
                self.assertTrue(result)

    def test_validate_account_holder_name_invalid(self):
        """Test validation of invalid account holder names"""
        invalid_names = [
            "",  # Empty
            "A",  # Too short
            "A" * 101,  # Too long
            "John123",  # Contains numbers
            "John@Doe",  # Contains special characters
            None,  # None
            "   ",  # Only spaces
        ]

        for name in invalid_names:
            with self.subTest(name=name):
                result = self.validation_service.validate_account_holder_name(name)
                self.assertFalse(result)

    def test_validate_currency_valid(self):
        """Test validation of valid currency"""
        result = self.validation_service.validate_currency("USD")
        self.assertTrue(result)

    def test_validate_currency_invalid(self):
        """Test validation of invalid currencies"""
        invalid_currencies = ["EUR", "GBP", "CAD", "JPY", "", None]

        for currency in invalid_currencies:
            with self.subTest(currency=currency):
                result = self.validation_service.validate_currency(currency)
                self.assertFalse(result)

    def test_validate_daily_limits_deposit(self):
        """Test daily limit validation for deposits"""
        UserBalance.objects.create(
            user=self.user,
            available_balance=Decimal("1000.00"),
            daily_deposit_used=Decimal("40000.00"),
            max_daily_deposit=Decimal("50000.00"),
        )

        # Should allow within limits
        is_valid, error = self.validation_service.validate_daily_limits(
            self.user, "deposit", Decimal("5000.00")
        )
        self.assertTrue(is_valid)

        # Should reject over limits
        is_valid, error = self.validation_service.validate_daily_limits(
            self.user, "deposit", Decimal("15000.00")
        )
        self.assertFalse(is_valid)
        self.assertIn("Daily deposit limit exceeded", error)

    def test_validate_daily_limits_withdrawal(self):
        """Test daily limit validation for withdrawals"""
        UserBalance.objects.create(
            user=self.user,
            available_balance=Decimal("50000.00"),
            daily_withdrawal_used=Decimal("30000.00"),
            max_daily_withdrawal=Decimal("50000.00"),
        )

        # Should allow within limits
        is_valid, error = self.validation_service.validate_daily_limits(
            self.user, "withdrawal", Decimal("10000.00")
        )
        self.assertTrue(is_valid)

        # Should reject over limits
        is_valid, error = self.validation_service.validate_daily_limits(
            self.user, "withdrawal", Decimal("25000.00")
        )
        self.assertFalse(is_valid)
        self.assertIn("Daily withdrawal limit exceeded", error)

    def test_validate_daily_limits_no_balance_record(self):
        """Test daily limit validation when user has no balance record"""
        user_no_balance = User.objects.create_user(
            username="nobalance", email="nobalance@example.com", password="testpass123"
        )

        is_valid, error = self.validation_service.validate_daily_limits(
            user_no_balance, "deposit", Decimal("1000.00")
        )
        self.assertTrue(is_valid)  # Should allow when no balance record

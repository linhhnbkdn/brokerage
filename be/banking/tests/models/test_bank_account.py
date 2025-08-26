"""
Unit tests for BankAccount model
Comprehensive test coverage for all model functionality
"""

import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from banking.models import BankAccount


class BankAccountModelTest(TestCase):
    """Test cases for BankAccount model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.account_data = {
            "user": self.user,
            "bank_name": "Test Bank",
            "bank_routing_number": "021000021",
            "account_type": "checking",
            "account_holder_name": "Test User",
        }

    def test_create_bank_account(self):
        """Test creating a bank account"""
        account = BankAccount.objects.create(**self.account_data)
        account.set_account_number("1234567890")
        account.save()

        self.assertEqual(account.user, self.user)
        self.assertEqual(account.bank_name, "Test Bank")
        self.assertEqual(account.bank_routing_number, "021000021")
        self.assertEqual(account.account_type, "checking")
        self.assertEqual(account.account_holder_name, "Test User")
        self.assertEqual(account.status, "pending_verification")
        self.assertIsInstance(account.account_link_id, uuid.UUID)

    def test_account_number_encryption(self):
        """Test account number encryption and decryption"""
        account = BankAccount.objects.create(**self.account_data)
        test_number = "1234567890"

        account.set_account_number(test_number)
        self.assertIsNotNone(account.account_number_encrypted)

        # Verify decryption works
        decrypted = account.get_account_number()
        self.assertEqual(decrypted, test_number)

    def test_get_last_four_digits(self):
        """Test getting last four digits of account number"""
        account = BankAccount.objects.create(**self.account_data)
        account.set_account_number("1234567890")

        last_four = account.get_last_four_digits()
        self.assertEqual(last_four, "7890")

    def test_get_last_four_digits_short_number(self):
        """Test last four digits with short account number"""
        account = BankAccount.objects.create(**self.account_data)
        account.set_account_number("123")

        last_four = account.get_last_four_digits()
        self.assertEqual(last_four, "****")

    def test_is_verified(self):
        """Test account verification status"""
        account = BankAccount.objects.create(**self.account_data)

        self.assertFalse(account.is_verified())

        account.status = "verified"
        self.assertTrue(account.is_verified())

    def test_can_attempt_verification(self):
        """Test verification attempt limits"""
        account = BankAccount.objects.create(**self.account_data)

        self.assertTrue(account.can_attempt_verification())

        account.verification_attempts = 3
        self.assertFalse(account.can_attempt_verification())

    def test_is_active(self):
        """Test account active status"""
        account = BankAccount.objects.create(**self.account_data)

        self.assertFalse(account.is_active())

        account.status = "verified"
        self.assertTrue(account.is_active())

        account.status = "suspended"
        self.assertFalse(account.is_active())

    def test_generate_micro_deposits(self):
        """Test micro-deposit generation"""
        account = BankAccount.objects.create(**self.account_data)
        account.generate_micro_deposits()

        self.assertIsNotNone(account.micro_deposit_amount_1)
        self.assertIsNotNone(account.micro_deposit_amount_2)
        self.assertIsNotNone(account.micro_deposits_sent_at)

        # Amounts should be different
        self.assertNotEqual(
            account.micro_deposit_amount_1, account.micro_deposit_amount_2
        )

        # Amounts should be between 0.01 and 0.99
        self.assertTrue(
            Decimal("0.01") <= account.micro_deposit_amount_1 <= Decimal("0.99")
        )
        self.assertTrue(
            Decimal("0.01") <= account.micro_deposit_amount_2 <= Decimal("0.99")
        )

    def test_verify_micro_deposits_success(self):
        """Test successful micro-deposit verification"""
        account = BankAccount.objects.create(**self.account_data)
        account.micro_deposit_amount_1 = Decimal("0.12")
        account.micro_deposit_amount_2 = Decimal("0.34")
        account.save()

        # Test correct amounts
        result = account.verify_micro_deposits(Decimal("0.12"), Decimal("0.34"))
        self.assertTrue(result)
        self.assertEqual(account.status, "verified")

    def test_verify_micro_deposits_reverse_order(self):
        """Test micro-deposit verification with amounts in reverse order"""
        account = BankAccount.objects.create(**self.account_data)
        account.micro_deposit_amount_1 = Decimal("0.12")
        account.micro_deposit_amount_2 = Decimal("0.34")
        account.save()

        # Test reverse order
        result = account.verify_micro_deposits(Decimal("0.34"), Decimal("0.12"))
        self.assertTrue(result)
        self.assertEqual(account.status, "verified")

    def test_verify_micro_deposits_failure(self):
        """Test failed micro-deposit verification"""
        account = BankAccount.objects.create(**self.account_data)
        account.micro_deposit_amount_1 = Decimal("0.12")
        account.micro_deposit_amount_2 = Decimal("0.34")
        account.verification_attempts = 0
        account.save()

        # Test incorrect amounts
        result = account.verify_micro_deposits(Decimal("0.11"), Decimal("0.33"))
        self.assertFalse(result)
        self.assertEqual(account.verification_attempts, 1)
        self.assertNotEqual(account.status, "verified")

    def test_verify_micro_deposits_no_amounts_set(self):
        """Test verification when no micro-deposits were sent"""
        account = BankAccount.objects.create(**self.account_data)

        result = account.verify_micro_deposits(Decimal("0.12"), Decimal("0.34"))
        self.assertFalse(result)

    def test_get_masked_account_info(self):
        """Test getting masked account information"""
        account = BankAccount.objects.create(**self.account_data)
        account.set_account_number("1234567890")

        info = account.get_masked_account_info()

        expected_keys = {
            "account_link_id",
            "bank_name",
            "account_type",
            "last_four_digits",
            "status",
            "account_holder_name",
        }
        self.assertEqual(set(info.keys()), expected_keys)
        self.assertEqual(info["last_four_digits"], "7890")
        self.assertEqual(info["bank_name"], "Test Bank")

    def test_update_last_used(self):
        """Test updating last used timestamp"""
        account = BankAccount.objects.create(**self.account_data)

        self.assertIsNone(account.last_used_at)

        account.update_last_used()
        account.refresh_from_db()

        self.assertIsNotNone(account.last_used_at)

    def test_unique_account_link_id(self):
        """Test that account_link_id is unique"""
        account1 = BankAccount.objects.create(**self.account_data)

        # Create another account for different user
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        account_data2 = self.account_data.copy()
        account_data2["user"] = user2

        account2 = BankAccount.objects.create(**account_data2)

        # Verify they have different account_link_ids
        self.assertNotEqual(account1.account_link_id, account2.account_link_id)

    def test_string_representation(self):
        """Test string representation of bank account"""
        account = BankAccount.objects.create(**self.account_data)
        account.set_account_number("1234567890")

        expected = f"{self.user.email} - Test Bank ****7890"
        self.assertEqual(str(account), expected)

    def test_default_daily_limits(self):
        """Test default daily limits are set correctly"""
        account = BankAccount.objects.create(**self.account_data)

        self.assertEqual(account.daily_deposit_limit, Decimal("50000.00"))
        self.assertEqual(account.daily_withdrawal_limit, Decimal("50000.00"))

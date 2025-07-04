"""
Unit tests for input validation utilities
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Mock Flask before importing our modules
with patch.dict("sys.modules", {"flask": MagicMock()}):
    from src.utils.validation import InputValidator, validate_registration_data


class TestInputValidator(unittest.TestCase):
    """Test cases for InputValidator class"""

    def setUp(self):
        self.validator = InputValidator()

    def test_validate_email_valid(self):
        """Test valid email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "firstname.lastname@company.com",
        ]

        for email in valid_emails:
            is_valid, error = self.validator.validate_email(email)
            self.assertTrue(is_valid, f"Email {email} should be valid")
            self.assertIsNone(error)

    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@domain",
            "",
            None,
        ]

        for email in invalid_emails:
            is_valid, error = self.validator.validate_email(email)
            self.assertFalse(is_valid, f"Email {email} should be invalid")
            self.assertIsNotNone(error)

    def test_validate_password_valid(self):
        """Test valid password validation"""
        valid_passwords = [
            "Password123",
            "StrongPass1",
            "ComplexP@ss1",
            "MyPassword123",
        ]

        for password in valid_passwords:
            is_valid, error = self.validator.validate_password(password)
            self.assertTrue(is_valid, "Password should be valid")
            self.assertIsNone(error)

    def test_validate_password_invalid(self):
        """Test invalid password validation"""
        invalid_passwords = [
            "weak",  # Too short
            "password123",  # No uppercase
            "PASSWORD123",  # No lowercase
            "Password",  # No number
            "",  # Empty
            None,  # None
            "a" * 129,  # Too long
        ]

        for password in invalid_passwords:
            is_valid, error = self.validator.validate_password(password)
            self.assertFalse(is_valid, f"Password {password} should be invalid")
            self.assertIsNotNone(error)

    def test_validate_required_fields(self):
        """Test required fields validation"""
        # Valid data
        valid_data = {"field1": "value1", "field2": "value2", "field3": "value3"}
        required_fields = ["field1", "field2", "field3"]

        is_valid, error = self.validator.validate_required_fields(
            valid_data, required_fields
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Missing field
        invalid_data = {
            "field1": "value1",
            "field2": "value2",
            # field3 missing
        }

        is_valid, error = self.validator.validate_required_fields(
            invalid_data, required_fields
        )
        self.assertFalse(is_valid)
        self.assertIn("field3", error)

    def test_validate_string_length(self):
        """Test string length validation"""
        # Valid string
        is_valid, error = self.validator.validate_string_length(
            "Valid Name", "Name", 1, 50
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Too short
        is_valid, error = self.validator.validate_string_length("", "Name", 1, 50)
        self.assertFalse(is_valid)
        self.assertIn("at least 1", error)

        # Too long
        is_valid, error = self.validator.validate_string_length("x" * 51, "Name", 1, 50)
        self.assertFalse(is_valid)
        self.assertIn("no more than 50", error)

    def test_validate_user_type(self):
        """Test user type validation"""
        # Valid types
        for user_type in ["customer", "provider"]:
            is_valid, error = self.validator.validate_user_type(user_type)
            self.assertTrue(is_valid)
            self.assertIsNone(error)

        # Invalid type
        is_valid, error = self.validator.validate_user_type("invalid")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_sanitize_html(self):
        """Test HTML sanitization"""
        dangerous_html = '<script>alert("xss")</script>Hello'
        sanitized = self.validator.sanitize_html(dangerous_html)
        self.assertNotIn("<script", sanitized)
        self.assertIn("Hello", sanitized)

        # Test javascript: protocol removal
        dangerous_link = 'javascript:alert("xss")'
        sanitized = self.validator.sanitize_html(dangerous_link)
        self.assertNotIn("javascript:", sanitized)


class TestRegistrationValidation(unittest.TestCase):
    """Test cases for registration data validation"""

    def test_validate_registration_valid(self):
        """Test valid registration data"""
        valid_data = {
            "email": "test@example.com",
            "password": "Password123",
            "first_name": "John",
            "last_name": "Doe",
            "user_type": "customer",
        }

        is_valid, error = validate_registration_data(valid_data)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_registration_invalid(self):
        """Test invalid registration data"""
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "first_name": "",
            "last_name": "Doe",
            "user_type": "invalid",
        }

        is_valid, error = validate_registration_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()

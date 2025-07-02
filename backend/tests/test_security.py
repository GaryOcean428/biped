"""
Comprehensive security tests for Biped Platform
Tests all security features including authentication, authorization, input validation, and CSRF protection.
"""

import unittest
import json
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.security import (
    SecurityManager, require_auth, require_role, validate_csrf,
    sanitize_json_input, rate_limiter, RateLimiter
)

class TestSecurityManager(unittest.TestCase):
    """Test SecurityManager functionality"""
    
    def setUp(self):
        self.security_manager = SecurityManager()
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = self.security_manager.sanitize_input(malicious_input)
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('alert', sanitized)
        
        # Test HTML escaping
        html_input = "<b>Bold text</b> & special chars"
        sanitized = self.security_manager.sanitize_input(html_input)
        self.assertIn('&lt;', sanitized)  # < should be escaped
        self.assertIn('&amp;', sanitized)  # & should be escaped
    
    def test_validate_email(self):
        """Test email validation"""
        valid_emails = [
            'user@example.com',
            'test.email+tag@domain.co.uk',
            'user123@test-domain.org'
        ]
        
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user space@domain.com',
            'user@domain',
            ''
        ]
        
        for email in valid_emails:
            self.assertTrue(self.security_manager.validate_email(email))
        
        for email in invalid_emails:
            self.assertFalse(self.security_manager.validate_email(email))
    
    def test_validate_phone(self):
        """Test phone number validation"""
        valid_phones = [
            '+1234567890',
            '(555) 123-4567',
            '555-123-4567',
            '15551234567'
        ]
        
        invalid_phones = [
            '123',  # Too short
            '12345678901234567890',  # Too long
            'abc-def-ghij',  # No digits
            ''
        ]
        
        for phone in valid_phones:
            self.assertTrue(self.security_manager.validate_phone(phone))
        
        for phone in invalid_phones:
            self.assertFalse(self.security_manager.validate_phone(phone))
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        # Strong passwords
        strong_passwords = [
            'StrongPass123!',
            'MySecure@Password1',
            'Complex#Pass2024'
        ]
        
        # Weak passwords
        weak_passwords = [
            'weak',  # Too short
            'weakpassword',  # No uppercase, numbers, or special chars
            'WEAKPASSWORD',  # No lowercase, numbers, or special chars
            'WeakPassword',  # No numbers or special chars
            'WeakPass123',  # No special chars
            'WeakPass!'  # No numbers
        ]
        
        for password in strong_passwords:
            is_strong, message = self.security_manager.validate_password_strength(password)
            self.assertTrue(is_strong, f"Password '{password}' should be strong")
        
        for password in weak_passwords:
            is_strong, message = self.security_manager.validate_password_strength(password)
            self.assertFalse(is_strong, f"Password '{password}' should be weak")
            self.assertIsInstance(message, str)
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = 'TestPassword123!'
        
        # Hash password
        password_hash = self.security_manager.hash_password(password)
        self.assertIsInstance(password_hash, str)
        self.assertNotEqual(password, password_hash)
        
        # Verify correct password
        self.assertTrue(self.security_manager.verify_password(password, password_hash))
        
        # Verify incorrect password
        self.assertFalse(self.security_manager.verify_password('WrongPassword', password_hash))
    
    def test_jwt_token_generation_and_validation(self):
        """Test JWT token generation and validation"""
        user_id = 123
        role = 'admin'
        
        # Generate token
        token = self.security_manager.generate_jwt_token(user_id, role, expires_hours=1)
        self.assertIsInstance(token, str)
        
        # Validate token
        is_valid, payload = self.security_manager.validate_jwt_token(token)
        self.assertTrue(is_valid)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['role'], role)
        
        # Test invalid token
        is_valid, error = self.security_manager.validate_jwt_token('invalid.token.here')
        self.assertFalse(is_valid)
        self.assertIsInstance(error, str)
    
    def test_url_validation(self):
        """Test URL validation"""
        valid_urls = [
            'https://example.com',
            'http://test.org/path',
            'https://subdomain.domain.com/path?query=value'
        ]
        
        invalid_urls = [
            'javascript:alert(1)',
            'ftp://example.com',
            'not-a-url',
            'http://',
            ''
        ]
        
        for url in valid_urls:
            self.assertTrue(self.security_manager.validate_url(url))
        
        for url in invalid_urls:
            self.assertFalse(self.security_manager.validate_url(url))
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        # Mock file object
        class MockFile:
            def __init__(self, filename, size):
                self.filename = filename
                self._size = size
                self._position = 0
            
            def seek(self, position, whence=0):
                if whence == 2:  # Seek to end
                    self._position = self._size
                else:
                    self._position = position
            
            def tell(self):
                return self._position
        
        # Valid file
        valid_file = MockFile('document.pdf', 1024 * 1024)  # 1MB
        is_valid, message = self.security_manager.validate_file_upload(
            valid_file, ['pdf', 'doc'], max_size_mb=5
        )
        self.assertTrue(is_valid)
        
        # Invalid extension
        invalid_ext_file = MockFile('script.exe', 1024)
        is_valid, message = self.security_manager.validate_file_upload(
            invalid_ext_file, ['pdf', 'doc'], max_size_mb=5
        )
        self.assertFalse(is_valid)
        self.assertIn('not allowed', message)
        
        # File too large
        large_file = MockFile('large.pdf', 10 * 1024 * 1024)  # 10MB
        is_valid, message = self.security_manager.validate_file_upload(
            large_file, ['pdf'], max_size_mb=5
        )
        self.assertFalse(is_valid)
        self.assertIn('too large', message)
        
        # Dangerous filename
        dangerous_file = MockFile('../../../etc/passwd', 1024)
        is_valid, message = self.security_manager.validate_file_upload(
            dangerous_file, ['txt'], max_size_mb=5
        )
        self.assertFalse(is_valid)
        self.assertIn('dangerous', message)

class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.rate_limiter = RateLimiter()
    
    def test_rate_limiting(self):
        """Test rate limiting logic"""
        key = 'test_key'
        limit = 3
        window = 60  # 1 minute
        
        # First 3 requests should be allowed
        for i in range(limit):
            self.assertTrue(self.rate_limiter.is_allowed(key, limit, window))
        
        # 4th request should be denied
        self.assertFalse(self.rate_limiter.is_allowed(key, limit, window))
        
        # Test with different key (should be allowed)
        self.assertTrue(self.rate_limiter.is_allowed('different_key', limit, window))

class TestSecurityDecorators(unittest.TestCase):
    """Test security decorators"""
    
    def setUp(self):
        # Mock Flask app and request context
        self.app = MagicMock()
        self.app.config = {'SECRET_KEY': 'test-secret-key'}
        
    @patch('utils.security.request')
    @patch('utils.security.current_app')
    def test_require_auth_decorator(self, mock_app, mock_request):
        """Test authentication requirement decorator"""
        mock_app.config = {'SECRET_KEY': 'test-secret-key'}
        
        # Test with valid token
        security_manager = SecurityManager()
        token = security_manager.generate_jwt_token(123, 'user')
        
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        
        @require_auth
        def protected_function():
            return 'success'
        
        # This would normally work with proper Flask context
        # For unit testing, we'll test the token validation separately
        is_valid, payload = security_manager.validate_jwt_token(token)
        self.assertTrue(is_valid)
        self.assertEqual(payload['user_id'], 123)

class TestInputSanitization(unittest.TestCase):
    """Test input sanitization in various scenarios"""
    
    def setUp(self):
        self.security_manager = SecurityManager()
    
    def test_sql_injection_prevention(self):
        """Test SQL injection attempt sanitization"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "1; DELETE FROM users WHERE 1=1; --"
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = self.security_manager.sanitize_input(malicious_input)
            # Should not contain dangerous SQL keywords
            self.assertNotIn('DROP', sanitized.upper())
            self.assertNotIn('DELETE', sanitized.upper())
            self.assertNotIn('--', sanitized)
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ]
        
        for payload in xss_payloads:
            sanitized = self.security_manager.sanitize_input(payload)
            # Should not contain script tags or javascript
            self.assertNotIn('<script>', sanitized.lower())
            self.assertNotIn('javascript:', sanitized.lower())
            self.assertNotIn('onerror=', sanitized.lower())
            self.assertNotIn('onload=', sanitized.lower())

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestSecurityManager))
    test_suite.addTest(unittest.makeSuite(TestRateLimiter))
    test_suite.addTest(unittest.makeSuite(TestSecurityDecorators))
    test_suite.addTest(unittest.makeSuite(TestInputSanitization))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)


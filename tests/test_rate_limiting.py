"""
Unit tests for rate limiting utilities
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock Flask before importing our modules
mock_request = MagicMock()
mock_request.remote_addr = '127.0.0.1'

with patch.dict('sys.modules', {
    'flask': MagicMock(request=mock_request)
}):
    from src.utils.rate_limiting import RateLimiter


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter class"""

    def setUp(self):
        self.rate_limiter = RateLimiter()
        # Clear any existing request data
        self.rate_limiter.requests = {}

    @patch('src.utils.rate_limiting.request')
    def test_rate_limiter_allows_initial_requests(self, mock_request):
        """Test that rate limiter allows initial requests"""
        mock_request.remote_addr = '127.0.0.1'

        # Should allow first request
        allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
        self.assertTrue(allowed)

        # Should allow subsequent requests within limit
        for i in range(4):
            allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
            self.assertTrue(allowed)

    @patch('src.utils.rate_limiting.request')
    def test_rate_limiter_blocks_excess_requests(self, mock_request):
        """Test that rate limiter blocks requests exceeding limit"""
        mock_request.remote_addr = '127.0.0.1'

        # Use up all allowed requests
        for i in range(5):
            allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
            self.assertTrue(allowed)

        # Next request should be blocked
        allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
        self.assertFalse(allowed)

    @patch('src.utils.rate_limiting.request')
    def test_rate_limiter_cleans_old_requests(self, mock_request):
        """Test that rate limiter cleans old requests"""
        mock_request.remote_addr = '127.0.0.1'

        # Simulate old requests by manually adding them
        client_id = self.rate_limiter._get_client_id()
        old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        self.rate_limiter.requests[client_id] = [old_time] * 5

        # Should allow new request as old ones are cleaned up
        allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
        self.assertTrue(allowed)

    @patch('src.utils.rate_limiting.request')
    def test_get_remaining_requests(self, mock_request):
        """Test getting remaining requests count"""
        mock_request.remote_addr = '127.0.0.1'

        # Initially should have full limit
        remaining = self.rate_limiter.get_remaining_requests(max_requests=10, window_minutes=1)
        self.assertEqual(remaining, 10)

        # After some requests, should decrease
        for i in range(3):
            self.rate_limiter.is_allowed(max_requests=10, window_minutes=1)

        remaining = self.rate_limiter.get_remaining_requests(max_requests=10, window_minutes=1)
        self.assertEqual(remaining, 7)

    @patch('src.utils.rate_limiting.request')
    def test_different_clients_separate_limits(self, mock_request):
        """Test that different clients have separate rate limits"""
        # First client
        mock_request.remote_addr = '127.0.0.1'
        for i in range(5):
            allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
            self.assertTrue(allowed)

        # Should be blocked for first client
        allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
        self.assertFalse(allowed)

        # Second client should still be allowed
        mock_request.remote_addr = '192.168.1.1'
        allowed = self.rate_limiter.is_allowed(max_requests=5, window_minutes=1)
        self.assertTrue(allowed)


if __name__ == '__main__':
    unittest.main()

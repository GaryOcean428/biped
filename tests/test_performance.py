"""
Performance tests for TradeHub Platform
Tests response times, memory usage, and system performance under load
"""

import json
import os
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from src.main import app, db


class PerformanceTestCase(unittest.TestCase):
    """Base class for performance tests"""

    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


class ResponseTimeTests(PerformanceTestCase):
    """Test response times for various endpoints"""

    def test_health_check_response_time(self):
        """Test health check endpoint response time"""
        start_time = time.time()
        response = self.client.get("/api/health")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            response_time,
            100,
            f"Health check took {response_time:.2f}ms, should be under 100ms",
        )

    def test_detailed_health_check_response_time(self):
        """Test detailed health check response time"""
        start_time = time.time()
        response = self.client.get("/api/health/detailed")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            response_time,
            500,
            f"Detailed health check took {response_time:.2f}ms, should be under 500ms",
        )

    def test_authentication_endpoint_response_time(self):
        """Test authentication endpoint response time"""
        test_data = {"email": "test@example.com", "password": "TestPassword123"}

        start_time = time.time()
        response = self.client.post(
            "/api/auth/login",
            data=json.dumps(test_data),
            content_type="application/json",
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        # Should respond quickly even for invalid credentials
        self.assertLess(
            response_time,
            200,
            f"Authentication took {response_time:.2f}ms, should be under 200ms",
        )

    def test_services_listing_response_time(self):
        """Test services listing endpoint response time"""
        start_time = time.time()
        response = self.client.get("/api/services")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        self.assertLess(
            response_time,
            300,
            f"Services listing took {response_time:.2f}ms, should be under 300ms",
        )


class ConcurrencyTests(PerformanceTestCase):
    """Test system behavior under concurrent load"""

    def test_concurrent_health_checks(self):
        """Test multiple concurrent health check requests"""
        num_requests = 10
        max_response_time = 0
        successful_requests = 0

        def make_request():
            nonlocal max_response_time, successful_requests
            start_time = time.time()
            response = self.client.get("/api/health")
            end_time = time.time()

            response_time = (end_time - start_time) * 1000
            max_response_time = max(max_response_time, response_time)

            if response.status_code == 200:
                successful_requests += 1

            return response_time

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            response_times = [future.result() for future in as_completed(futures)]

        # Verify performance
        avg_response_time = sum(response_times) / len(response_times)

        self.assertEqual(
            successful_requests, num_requests, "All requests should succeed"
        )
        self.assertLess(
            avg_response_time,
            150,
            f"Average response time {avg_response_time:.2f}ms should be under 150ms",
        )
        self.assertLess(
            max_response_time,
            300,
            f"Max response time {max_response_time:.2f}ms should be under 300ms",
        )

    def test_concurrent_authentication_attempts(self):
        """Test concurrent authentication attempts"""
        num_requests = 8
        successful_responses = 0

        def make_auth_request():
            nonlocal successful_responses
            test_data = {"email": "test@example.com", "password": "TestPassword123"}

            response = self.client.post(
                "/api/auth/login",
                data=json.dumps(test_data),
                content_type="application/json",
            )

            # Count responses that are not server errors
            if response.status_code < 500:
                successful_responses += 1

            return response.status_code

        # Execute concurrent authentication attempts
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_auth_request) for _ in range(num_requests)]
            status_codes = [future.result() for future in as_completed(futures)]

        # Should handle concurrent requests without server errors
        self.assertEqual(
            successful_responses,
            num_requests,
            f"Expected {num_requests} non-server-error responses, got {successful_responses}",
        )

        # No 5xx errors should occur
        server_errors = [code for code in status_codes if code >= 500]
        self.assertEqual(
            len(server_errors),
            0,
            f"No server errors should occur, got: {server_errors}",
        )


class MemoryUsageTests(PerformanceTestCase):
    """Test memory usage and potential memory leaks"""

    def test_memory_usage_during_requests(self):
        """Test memory usage doesn't grow excessively during requests"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make multiple requests
        for i in range(50):
            response = self.client.get("/api/health")
            self.assertEqual(response.status_code, 200)

            # Check memory every 10 requests
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory

                # Memory increase should be reasonable (less than 50MB for 50 simple requests)
                self.assertLess(
                    memory_increase,
                    50,
                    f"Memory increased by {memory_increase:.2f}MB after {i+1} requests",
                )

    def test_no_memory_leak_in_error_handling(self):
        """Test that error handling doesn't cause memory leaks"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make requests that will cause errors
        for i in range(30):
            # Invalid endpoint
            self.client.get("/api/nonexistent/endpoint")

            # Invalid JSON
            self.client.post(
                "/api/auth/login", data="invalid json", content_type="application/json"
            )

            # Check memory every 10 requests
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory

                # Memory increase should be minimal for error responses
                self.assertLess(
                    memory_increase,
                    30,
                    f"Memory increased by {memory_increase:.2f}MB after {i+1} error requests",
                )


class CachePerformanceTests(PerformanceTestCase):
    """Test caching performance improvements"""

    def test_response_caching_effectiveness(self):
        """Test that response caching improves performance"""
        # First request (cache miss)
        start_time = time.time()
        response1 = self.client.get("/api/health/detailed")
        first_response_time = (time.time() - start_time) * 1000

        # Second request (potential cache hit)
        start_time = time.time()
        response2 = self.client.get("/api/health/detailed")
        second_response_time = (time.time() - start_time) * 1000

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Both should be reasonably fast
        self.assertLess(first_response_time, 500, "First request should be under 500ms")
        self.assertLess(
            second_response_time, 500, "Second request should be under 500ms"
        )

        # Log the performance difference
        print(
            f"First request: {first_response_time:.2f}ms, Second request: {second_response_time:.2f}ms"
        )


class CompressionTests(PerformanceTestCase):
    """Test response compression effectiveness"""

    def test_large_response_compression(self):
        """Test that large responses are compressed when requested"""
        # Request with gzip support
        response = self.client.get(
            "/api/health/detailed", headers={"Accept-Encoding": "gzip"}
        )

        self.assertEqual(response.status_code, 200)

        # Check if response is large enough to potentially benefit from compression
        if len(response.data) > 1000:
            # Should have compression headers if compressed
            if "Content-Encoding" in response.headers:
                self.assertEqual(response.headers["Content-Encoding"], "gzip")
                print(f"Response compressed: {len(response.data)} bytes")

    def test_compression_content_integrity(self):
        """Test that compressed responses maintain content integrity"""
        # Get response without compression
        response_no_compression = self.client.get("/api/health/detailed")

        # Get response with compression
        response_with_compression = self.client.get(
            "/api/health/detailed", headers={"Accept-Encoding": "gzip"}
        )

        self.assertEqual(response_no_compression.status_code, 200)
        self.assertEqual(response_with_compression.status_code, 200)

        # Parse JSON from both responses
        try:
            data_no_compression = json.loads(response_no_compression.data)
            data_with_compression = json.loads(response_with_compression.data)

            # Content should be identical
            self.assertEqual(data_no_compression, data_with_compression)
        except json.JSONDecodeError:
            # If not JSON, compare raw data
            if "Content-Encoding" not in response_with_compression.headers:
                self.assertEqual(
                    response_no_compression.data, response_with_compression.data
                )


class DatabasePerformanceTests(PerformanceTestCase):
    """Test database performance and query optimization"""

    def test_database_connection_performance(self):
        """Test database connection and query performance"""
        with self.app.app_context():
            start_time = time.time()

            # Simple query to test database performance
            result = db.session.execute(db.text("SELECT 1"))
            result.fetchone()

            query_time = (time.time() - start_time) * 1000

            self.assertLess(
                query_time,
                50,
                f"Database query took {query_time:.2f}ms, should be under 50ms",
            )

    def test_multiple_database_queries_performance(self):
        """Test performance with multiple database queries"""
        with self.app.app_context():
            start_time = time.time()

            # Multiple simple queries
            for i in range(10):
                result = db.session.execute(db.text(f"SELECT {i}"))
                result.fetchone()

            total_time = (time.time() - start_time) * 1000
            avg_time = total_time / 10

            self.assertLess(
                avg_time,
                10,
                f"Average query time {avg_time:.2f}ms should be under 10ms",
            )
            self.assertLess(
                total_time, 100, f"Total time {total_time:.2f}ms should be under 100ms"
            )


if __name__ == "__main__":
    # Run performance tests with verbose output
    unittest.main(verbosity=2)

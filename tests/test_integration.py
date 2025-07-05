"""
Integration tests for TradeHub Platform API endpoints
Tests the complete application flow including security, validation, and performance
"""

import json
import os
import sys
import time
import unittest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from src.main import app, db  # noqa: E402
from src.models.user import User  # noqa: E402


class APIIntegrationTestCase(unittest.TestCase):
    """Base class for API integration tests"""

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


class SecurityIntegrationTests(APIIntegrationTestCase):
    """Integration tests for security features"""

    def test_security_headers_applied(self):
        """Test that security headers are applied to responses"""
        response = self.client.get("/api/health")

        # Check for security headers
        self.assertIn("X-Content-Type-Options", response.headers)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

        self.assertIn("X-Frame-Options", response.headers)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

        self.assertIn("X-XSS-Protection", response.headers)
        self.assertEqual(response.headers["X-XSS-Protection"], "1; mode=block")

        self.assertIn("Content-Security-Policy", response.headers)
        self.assertIn("Referrer-Policy", response.headers)

    def test_xss_prevention_in_registration(self):
        """Test XSS prevention in user registration"""
        malicious_data = {
            "username": '<script>alert("xss")</script>',
            "email": "test@example.com",
            "password": "TestPass123",
            "user_type": "customer",
        }

        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(malicious_data),
            content_type="application/json",
        )

        # Should either reject or sanitize the input
        self.assertIn(
            response.status_code, [400, 201]
        )  # Either validation error or success with sanitization

        if response.status_code == 201:
            # Check that script tags were removed
            response_data = json.loads(response.data)
            self.assertNotIn("<script>", str(response_data))

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in search endpoints"""
        malicious_query = "'; DROP TABLE users; --"

        response = self.client.get(f"/api/services?search={malicious_query}")

        # Should not cause server error
        self.assertNotEqual(response.status_code, 500)

        # Database should still be intact
        with self.app.app_context():
            # This should not raise an exception
            db.session.execute(db.text("SELECT COUNT(*) FROM users"))

    def test_rate_limiting_enforcement(self):
        """Test that rate limiting is enforced"""
        # Make multiple rapid requests to trigger rate limiting
        responses = []
        for i in range(12):  # Exceed the default limit
            response = self.client.post(
                "/api/auth/login",
                data=json.dumps(
                    {"email": "test@example.com", "password": "wrongpassword"}
                ),
                content_type="application/json",
            )
            responses.append(response)
            time.sleep(0.1)  # Small delay between requests

        # At least one request should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        self.assertGreater(
            len(rate_limited_responses), 0, "Rate limiting should be enforced"
        )


class ValidationIntegrationTests(APIIntegrationTestCase):
    """Integration tests for input validation"""

    def test_email_validation_in_registration(self):
        """Test email validation in user registration endpoint"""
        invalid_emails = [
            "invalid-email",
            "user..name@domain.com",
            "@domain.com",
            "user@",
        ]

        for email in invalid_emails:
            response = self.client.post(
                "/api/auth/register",
                data=json.dumps(
                    {
                        "username": "testuser",
                        "email": email,
                        "password": "TestPass123",
                        "user_type": "customer",
                    }
                ),
                content_type="application/json",
            )

            self.assertEqual(
                response.status_code, 400, f"Email {email} should be rejected"
            )
            response_data = json.loads(response.data)
            self.assertIn("error", response_data)

    def test_password_strength_validation(self):
        """Test password strength validation"""
        weak_passwords = [
            "weak",
            "12345678",
            "onlylowercase",
            "ONLYUPPERCASE",
            "NoNumbers!",
        ]

        for password in weak_passwords:
            response = self.client.post(
                "/api/auth/register",
                data=json.dumps(
                    {
                        "username": "testuser",
                        "email": "test@example.com",
                        "password": password,
                        "user_type": "customer",
                    }
                ),
                content_type="application/json",
            )

            self.assertEqual(
                response.status_code, 400, f"Password {password} should be rejected"
            )

    def test_required_fields_validation(self):
        """Test required fields validation"""
        incomplete_data = [
            {
                "email": "test@example.com",
                "password": "TestPass123",
            },  # Missing username
            {"username": "testuser", "password": "TestPass123"},  # Missing email
            {"username": "testuser", "email": "test@example.com"},  # Missing password
        ]

        for data in incomplete_data:
            response = self.client.post(
                "/api/auth/register",
                data=json.dumps(data),
                content_type="application/json",
            )

            self.assertEqual(
                response.status_code, 400, f"Incomplete data should be rejected: {data}"
            )


class PerformanceIntegrationTests(APIIntegrationTestCase):
    """Integration tests for performance features"""

    def test_response_compression(self):
        """Test that large responses are compressed"""
        # Create a response that should be compressed
        response = self.client.get(
            "/api/health/detailed", headers={"Accept-Encoding": "gzip"}
        )

        if len(response.data) > 1000:
            # Check if compression was applied
            self.assertIn("Content-Encoding", response.headers)
            self.assertEqual(response.headers["Content-Encoding"], "gzip")

    def test_performance_monitoring(self):
        """Test that performance metrics are collected"""
        # Make some requests to generate metrics
        for i in range(5):
            self.client.get("/api/health")
            time.sleep(0.1)

        # Check metrics endpoint
        response = self.client.get("/api/health/metrics")
        self.assertEqual(response.status_code, 200)

        metrics = json.loads(response.data)
        self.assertIn("request_count", metrics)
        self.assertIn("average_response_time", metrics)
        self.assertIn("system_metrics", metrics)

    def test_static_asset_caching(self):
        """Test that static assets have proper cache headers"""
        # Try to access a static file
        response = self.client.get("/static/validation.js")

        if response.status_code == 200:
            # Check for cache headers
            self.assertIn("Cache-Control", response.headers)
            self.assertIn("ETag", response.headers)


class HealthCheckIntegrationTests(APIIntegrationTestCase):
    """Integration tests for health check endpoints"""

    def test_basic_health_check(self):
        """Test basic health check endpoint"""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")

    def test_detailed_health_check(self):
        """Test detailed health check with metrics"""
        response = self.client.get("/api/health/detailed")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn("database", data)
        self.assertIn("system", data)
        self.assertIn("application", data)

    def test_readiness_check(self):
        """Test readiness check for load balancers"""
        response = self.client.get("/api/health/ready")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "ready")

    def test_liveness_check(self):
        """Test liveness check for container orchestration"""
        response = self.client.get("/api/health/live")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "alive")


class APIEndpointIntegrationTests(APIIntegrationTestCase):
    """Integration tests for core API endpoints"""

    def test_service_listing_endpoint(self):
        """Test services listing endpoint"""
        response = self.client.get("/api/services")
        self.assertIn(
            response.status_code, [200, 404]
        )  # May be empty but should not error

    def test_user_registration_flow(self):
        """Test complete user registration flow"""
        registration_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "user_type": "customer",
        }

        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(registration_data),
            content_type="application/json",
        )

        # Should either succeed or fail with validation error
        self.assertIn(response.status_code, [201, 400])

        if response.status_code == 201:
            data = json.loads(response.data)
            self.assertIn("message", data)

    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        # Test login endpoint exists and handles invalid credentials properly
        response = self.client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "nonexistent@example.com", "password": "wrongpassword"}
            ),
            content_type="application/json",
        )

        self.assertIn(
            response.status_code, [400, 401, 404]
        )  # Should reject invalid credentials

    def test_error_handling_consistency(self):
        """Test that error responses are consistent across endpoints"""
        error_responses = []

        # Test various endpoints that should return errors
        endpoints = [
            ("/api/auth/login", "POST", {}),
            ("/api/auth/register", "POST", {}),
            ("/api/services/999999", "GET", None),
            ("/api/users/999999", "GET", None),
        ]

        for endpoint, method, data in endpoints:
            if method == "POST":
                response = self.client.post(
                    endpoint,
                    data=json.dumps(data) if data else "",
                    content_type="application/json",
                )
            else:
                response = self.client.get(endpoint)

            if response.status_code >= 400:
                try:
                    error_data = json.loads(response.data)
                    error_responses.append(error_data)
                except (json.JSONDecodeError, ValueError):
                    pass  # Skip non-JSON responses

        # Check that error responses have consistent structure
        for error_response in error_responses:
            self.assertIsInstance(
                error_response, dict, "Error responses should be JSON objects"
            )
            # Most should have an 'error' field
            if "error" not in error_response and "message" not in error_response:
                self.fail(
                    f"Error response missing error/message field: {error_response}"
                )


if __name__ == "__main__":
    unittest.main()

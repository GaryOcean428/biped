"""Test utilities and helper functions."""

import json
from typing import Any, Dict


class TestHelpers:
    """Helper methods for testing."""

    @staticmethod
    def assert_json_response(response, expected_status=200):
        """Assert that response is JSON with expected status."""
        assert response.status_code == expected_status
        assert response.content_type == "application/json"
        return json.loads(response.data)

    @staticmethod
    def assert_error_response(response, expected_status=400):
        """Assert that response is an error with expected status."""
        assert response.status_code == expected_status
        data = json.loads(response.data)
        assert "error" in data or "message" in data
        return data

    @staticmethod
    def create_headers(content_type="application/json", **kwargs):
        """Create HTTP headers for requests."""
        headers = {"Content-Type": content_type}
        headers.update(kwargs)
        return headers


def mock_external_service(service_name: str, return_value: Any = None):
    """Mock external service calls."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Mock implementation
            return return_value if return_value is not None else {"status": "mocked"}

        return wrapper

    return decorator

"""
Test configuration and fixtures for TradeHub Platform
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Mock external dependencies for testing
sys.modules["flask"] = MagicMock()
sys.modules["flask_cors"] = MagicMock()
sys.modules["flask_sqlalchemy"] = MagicMock()
sys.modules["psycopg2"] = MagicMock()
sys.modules["stripe"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["geopy"] = MagicMock()
sys.modules["psutil"] = MagicMock()


@pytest.fixture
def mock_db():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
        "first_name": "Test",
        "last_name": "User",
        "user_type": "customer",
    }


@pytest.fixture
def invalid_user_data():
    """Invalid user data for testing validation"""
    return {
        "email": "invalid-email",
        "password": "weak",
        "first_name": "",
        "last_name": "User",
        "user_type": "invalid",
    }

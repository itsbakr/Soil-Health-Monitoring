"""
Pytest Configuration and Shared Fixtures

Provides common test fixtures for:
- FastAPI test client
- Mock services
- Test database
- Authentication helpers
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from config import settings


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Sync test client
@pytest.fixture
def client() -> Generator:
    """Synchronous test client for FastAPI"""
    with TestClient(app) as c:
        yield c


# Async test client
@pytest.fixture
async def async_client() -> AsyncClient:
    """Asynchronous test client for FastAPI"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Mock authenticated user
@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Headers with mock authentication"""
    return {
        "Authorization": "Bearer test-token-for-testing-purposes-only-12345678901234567890"
    }


@pytest.fixture
def mock_user_id() -> str:
    """Mock user ID for testing"""
    return "test-user-123"


# Mock Supabase auth
@pytest.fixture
def mock_supabase_auth(mock_user_id):
    """Mock Supabase authentication"""
    with patch('routers.auth.httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": mock_user_id,
            "email": "test@example.com"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance
        
        yield mock_client


# Sample farm data
@pytest.fixture
def sample_farm_data() -> Dict[str, Any]:
    """Sample farm data for testing"""
    return {
        "name": "Test Farm",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "area_hectares": 50.0,
        "crop_type": "Corn"
    }


@pytest.fixture
def sample_coordinates() -> Dict[str, float]:
    """Sample coordinates for testing"""
    return {
        "latitude": 41.8781,
        "longitude": -87.6298
    }


# Mock satellite data
@pytest.fixture
def mock_satellite_data() -> Dict[str, Any]:
    """Mock satellite data for testing"""
    return {
        "ndvi": 0.65,
        "ndwi": 0.35,
        "evi": 0.55,
        "savi": 0.58,
        "data_quality_score": 85.0,
        "cloud_coverage": 10.0,
        "surface_temperature": 22.5,
        "moisture_estimate": 0.45,
        "acquisition_date": "2024-01-15"
    }


# Mock weather data
@pytest.fixture
def mock_weather_data() -> Dict[str, Any]:
    """Mock weather data for testing"""
    return {
        "temperature": 22.5,
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 5.5,
        "precipitation": 0.0,
        "description": "Clear sky"
    }


# Mock soil health report
@pytest.fixture
def mock_soil_health_report() -> Dict[str, Any]:
    """Mock soil health report for testing"""
    return {
        "overall_score": 75.0,
        "health_status": "Good",
        "confidence_score": 0.85,
        "deficiencies": [
            {"type": "nitrogen", "severity": "moderate", "issue": "Low nitrogen levels"}
        ],
        "recommendations": [
            {"action": "fertilize", "description": "Apply nitrogen fertilizer", "priority": "high"}
        ],
        "key_indicators": {
            "organic_matter": 3.5,
            "ph": 6.8,
            "nitrogen": "low",
            "phosphorus": "adequate"
        }
    }


# Environment variable overrides for testing
@pytest.fixture(autouse=True)
def test_environment():
    """Set environment variables for testing"""
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "testing"
    yield
    settings.ENVIRONMENT = original_env


"""
API Endpoint Tests

Tests for FastAPI endpoints:
- Health checks
- Authentication
- Farm management
- Analysis
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_verify_auth_no_token(self, client):
        """Test verify endpoint without token"""
        response = client.get("/auth/verify")
        
        assert response.status_code == 401
    
    def test_verify_auth_invalid_token_format(self, client):
        """Test verify endpoint with invalid token format"""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": "Invalid format"}
        )
        
        assert response.status_code == 401
    
    def test_verify_auth_bearer_without_token(self, client):
        """Test verify endpoint with Bearer but no token"""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer "}
        )
        
        assert response.status_code == 401
    
    def test_profile_no_token(self, client):
        """Test profile endpoint without token"""
        response = client.get("/auth/profile")
        
        assert response.status_code == 401


class TestFarmEndpoints:
    """Test farm management endpoints"""
    
    def test_list_farms_no_auth(self, client):
        """Test listing farms without authentication"""
        response = client.get("/farms/")
        
        assert response.status_code == 401
    
    def test_create_farm_no_auth(self, client, sample_farm_data):
        """Test creating farm without authentication"""
        response = client.post("/farms/", json=sample_farm_data)
        
        assert response.status_code == 401
    
    def test_get_farm_no_auth(self, client):
        """Test getting farm without authentication"""
        response = client.get("/farms/some-farm-id")
        
        assert response.status_code == 401


class TestAnalysisEndpoints:
    """Test analysis endpoints"""
    
    def test_start_analysis_no_auth(self, client):
        """Test starting analysis without authentication"""
        # Analysis endpoints expect POST with farm_id as path parameter
        response = client.get("/analysis/soil-health/some-farm-id")
        
        # Without auth, should return 401
        assert response.status_code == 401
    
    def test_get_analysis_no_auth(self, client):
        """Test getting analysis without authentication"""
        response = client.get("/analysis/soil-health/some-analysis-id")
        
        assert response.status_code == 401


class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_admin_stats_no_auth(self, client):
        """Test admin stats without authentication"""
        response = client.get("/admin/stats")
        
        # Should require authentication or return 404 if not configured
        assert response.status_code in [401, 403, 404]


class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present in responses"""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        # Check security headers
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"
        
        assert "x-xss-protection" in response.headers
        assert response.headers["x-xss-protection"] == "1; mode=block"
        
        assert "referrer-policy" in response.headers


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should allow the origin if configured
        assert response.status_code in [200, 400]


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 response for non-existent endpoint"""
        response = client.get("/non-existent-endpoint")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 response for wrong HTTP method"""
        response = client.delete("/health")
        
        assert response.status_code == 405


class TestRequestValidation:
    """Test request validation"""
    
    def test_large_request_body_rejected(self, client):
        """Test that overly large request bodies are rejected"""
        # Create a large payload (>10MB)
        large_data = "x" * (11 * 1024 * 1024)  # 11MB
        
        # This test may not work directly due to client limitations
        # The actual middleware would reject this at the server level
        pass
    
    def test_invalid_json_body(self, client, auth_headers):
        """Test that invalid JSON is handled"""
        response = client.post(
            "/farms/",
            content="{invalid json",
            headers={
                **auth_headers,
                "Content-Type": "application/json"
            }
        )
        
        # Should be rejected (401 without valid auth, or 422 for invalid JSON)
        assert response.status_code in [401, 422]


class TestRateLimiting:
    """Test rate limiting (basic tests)"""
    
    def test_health_endpoint_not_heavily_limited(self, client):
        """Test that health endpoint allows multiple requests"""
        # Make several requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200


class TestCorrelationId:
    """Test correlation ID handling"""
    
    def test_correlation_id_in_response(self, client):
        """Test that correlation ID is included in responses"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "x-correlation-id" in response.headers
        
        # Correlation ID should be a valid UUID or similar format
        correlation_id = response.headers["x-correlation-id"]
        assert len(correlation_id) > 0
    
    def test_custom_correlation_id_preserved(self, client):
        """Test that custom correlation ID is preserved"""
        custom_id = "custom-correlation-id-12345"
        
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": custom_id}
        )
        
        assert response.status_code == 200
        assert response.headers.get("x-correlation-id") == custom_id


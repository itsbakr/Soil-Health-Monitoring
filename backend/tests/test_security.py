"""
Unit Tests for Security Utilities

Tests:
- Input validation functions
- Sanitization
- Token handling
- Security middleware
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.security import (
    validate_latitude,
    validate_longitude,
    validate_coordinates,
    validate_farm_size,
    sanitize_string,
    validate_email,
    validate_farm_name,
    validate_uuid,
    hash_token,
    generate_secure_token,
    constant_time_compare,
    TokenBlacklist,
    mask_api_key,
    get_client_ip
)
from utils.exceptions import ValidationError


class TestInputValidation:
    """Test input validation functions"""
    
    def test_validate_latitude_valid(self):
        """Test valid latitudes"""
        assert validate_latitude(0) == 0
        assert validate_latitude(45.5) == 45.5
        assert validate_latitude(-45.5) == -45.5
        assert validate_latitude(90) == 90
        assert validate_latitude(-90) == -90
    
    def test_validate_latitude_invalid(self):
        """Test invalid latitudes"""
        with pytest.raises(ValidationError):
            validate_latitude(91)
        with pytest.raises(ValidationError):
            validate_latitude(-91)
        with pytest.raises(ValidationError):
            validate_latitude(180)
    
    def test_validate_longitude_valid(self):
        """Test valid longitudes"""
        assert validate_longitude(0) == 0
        assert validate_longitude(90) == 90
        assert validate_longitude(-90) == -90
        assert validate_longitude(180) == 180
        assert validate_longitude(-180) == -180
    
    def test_validate_longitude_invalid(self):
        """Test invalid longitudes"""
        with pytest.raises(ValidationError):
            validate_longitude(181)
        with pytest.raises(ValidationError):
            validate_longitude(-181)
        with pytest.raises(ValidationError):
            validate_longitude(360)
    
    def test_validate_coordinates_valid(self):
        """Test valid coordinate pairs"""
        lat, lng = validate_coordinates(41.8781, -87.6298)
        assert lat == 41.8781
        assert lng == -87.6298
    
    def test_validate_coordinates_invalid(self):
        """Test invalid coordinate pairs"""
        with pytest.raises(ValidationError):
            validate_coordinates(91, 0)
        with pytest.raises(ValidationError):
            validate_coordinates(0, 181)
    
    def test_validate_farm_size_valid(self):
        """Test valid farm sizes"""
        assert validate_farm_size(0.01) == 0.01
        assert validate_farm_size(50) == 50
        assert validate_farm_size(100000) == 100000
    
    def test_validate_farm_size_invalid(self):
        """Test invalid farm sizes"""
        with pytest.raises(ValidationError):
            validate_farm_size(0)
        with pytest.raises(ValidationError):
            validate_farm_size(-1)
        with pytest.raises(ValidationError):
            validate_farm_size(100001)


class TestSanitization:
    """Test string sanitization functions"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        assert sanitize_string("  hello world  ") == "hello world"
        assert sanitize_string("test") == "test"
        assert sanitize_string("") == ""
    
    def test_sanitize_string_control_chars(self):
        """Test removal of control characters"""
        # Control characters should be removed
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result and "world" in result
    
    def test_sanitize_string_max_length(self):
        """Test max length enforcement"""
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_validate_email_valid(self):
        """Test valid emails"""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("TEST@EXAMPLE.COM") == "test@example.com"
        assert validate_email("user.name@domain.org") == "user.name@domain.org"
    
    def test_validate_email_invalid(self):
        """Test invalid emails"""
        with pytest.raises(ValidationError):
            validate_email("notanemail")
        with pytest.raises(ValidationError):
            validate_email("missing@")
        with pytest.raises(ValidationError):
            validate_email("@nodomain.com")
    
    def test_validate_farm_name_valid(self):
        """Test valid farm names"""
        assert validate_farm_name("Green Acres Farm") == "Green Acres Farm"
        assert validate_farm_name("Farm123") == "Farm123"
    
    def test_validate_farm_name_empty(self):
        """Test empty farm name"""
        with pytest.raises(ValidationError):
            validate_farm_name("")
        with pytest.raises(ValidationError):
            validate_farm_name("   ")
    
    def test_validate_farm_name_malicious(self):
        """Test malicious farm names"""
        with pytest.raises(ValidationError):
            validate_farm_name("<script>alert('xss')</script>")
        with pytest.raises(ValidationError):
            validate_farm_name("javascript:alert('xss')")
    
    def test_validate_uuid_valid(self):
        """Test valid UUIDs"""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid(uuid) == uuid
        assert validate_uuid(uuid.upper()) == uuid  # Case insensitive
    
    def test_validate_uuid_invalid(self):
        """Test invalid UUIDs"""
        with pytest.raises(ValidationError):
            validate_uuid("not-a-uuid")
        with pytest.raises(ValidationError):
            validate_uuid("550e8400-e29b-41d4-a716")  # Too short
        with pytest.raises(ValidationError):
            validate_uuid("")


class TestTokenSecurity:
    """Test token security functions"""
    
    def test_hash_token(self):
        """Test token hashing"""
        token = "my-secret-token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Different input should produce different hash
        assert hash_token("different-token") != hash1
        
        # Hash should be hex string
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        # Tokens should be unique
        assert token1 != token2
        
        # Tokens should have sufficient length
        assert len(token1) >= 32
    
    def test_generate_secure_token_custom_length(self):
        """Test secure token with custom length"""
        token = generate_secure_token(64)
        assert len(token) >= 64
    
    def test_constant_time_compare_equal(self):
        """Test constant time comparison for equal strings"""
        assert constant_time_compare("secret", "secret") is True
    
    def test_constant_time_compare_not_equal(self):
        """Test constant time comparison for unequal strings"""
        assert constant_time_compare("secret", "different") is False
        assert constant_time_compare("", "something") is False


class TestTokenBlacklist:
    """Test token blacklist functionality"""
    
    def test_add_and_check_blacklist(self):
        """Test adding and checking blacklisted tokens"""
        from datetime import datetime, timedelta
        
        token_hash = "test-token-hash-123"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        TokenBlacklist.add(token_hash, expires_at)
        
        assert TokenBlacklist.is_blacklisted(token_hash) is True
        assert TokenBlacklist.is_blacklisted("different-hash") is False
    
    def test_blacklist_not_contains_unblacklisted(self):
        """Test that non-blacklisted tokens return False"""
        assert TokenBlacklist.is_blacklisted("never-blacklisted-token") is False


class TestUtilities:
    """Test utility functions"""
    
    def test_mask_api_key_long(self):
        """Test API key masking for long keys"""
        key = "sk-1234567890abcdef"
        masked = mask_api_key(key)
        
        assert masked.startswith("sk-1")
        assert masked.endswith("cdef")
        assert "..." in masked
    
    def test_mask_api_key_short(self):
        """Test API key masking for short keys"""
        key = "short"
        masked = mask_api_key(key)
        
        assert masked == "*****"


class TestGetClientIP:
    """Test client IP extraction"""
    
    def test_get_client_ip_from_forwarded_header(self):
        """Test getting IP from X-Forwarded-For header"""
        from unittest.mock import Mock
        
        request = Mock()
        request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        request.client = Mock(host="127.0.0.1")
        
        ip = get_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_from_real_ip_header(self):
        """Test getting IP from X-Real-IP header"""
        from unittest.mock import Mock
        
        request = Mock()
        request.headers = {"x-real-ip": "203.0.113.1"}
        request.client = Mock(host="127.0.0.1")
        
        ip = get_client_ip(request)
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_direct(self):
        """Test getting direct client IP"""
        from unittest.mock import Mock
        
        request = Mock()
        request.headers = {}
        request.client = Mock(host="192.168.1.100")
        
        ip = get_client_ip(request)
        assert ip == "192.168.1.100"


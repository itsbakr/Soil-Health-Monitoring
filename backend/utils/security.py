"""
Security Utilities for SoilGuard API

Provides:
- Security headers middleware
- JWT validation and hardening
- Request validation
- Input sanitization
- CSRF protection helpers
"""

import re
import hmac
import hashlib
import secrets
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


# ============================================================================
# Security Headers Middleware
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter (legacy browsers)
    - Strict-Transport-Security: Force HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """
    
    def __init__(self, app, environment: str = "production"):
        super().__init__(app)
        self.environment = environment
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Always add these headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy - restrict browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(self), "  # Allow for farm location
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Production-only headers
        if self.environment == "production":
            # HSTS - 1 year
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
            
            # CSP - restrictive but allows API usage
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://*.supabase.co; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        
        return response


# ============================================================================
# Input Validation & Sanitization
# ============================================================================

def validate_latitude(lat: float) -> float:
    """Validate latitude is within valid range"""
    if not -90 <= lat <= 90:
        raise ValidationError(
            "Invalid latitude",
            details={"value": lat, "valid_range": "-90 to 90"}
        )
    return lat


def validate_longitude(lng: float) -> float:
    """Validate longitude is within valid range"""
    if not -180 <= lng <= 180:
        raise ValidationError(
            "Invalid longitude",
            details={"value": lng, "valid_range": "-180 to 180"}
        )
    return lng


def validate_coordinates(lat: float, lng: float) -> tuple:
    """Validate both latitude and longitude"""
    return validate_latitude(lat), validate_longitude(lng)


def validate_farm_size(hectares: float) -> float:
    """Validate farm size is within reasonable range"""
    if not 0.01 <= hectares <= 100000:
        raise ValidationError(
            "Invalid farm size",
            details={"value": hectares, "valid_range": "0.01 to 100000 hectares"}
        )
    return hectares


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input:
    - Strip whitespace
    - Remove control characters
    - Limit length
    """
    if not value:
        return ""
    
    # Strip whitespace
    value = value.strip()
    
    # Remove control characters except newlines
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def validate_email(email: str) -> str:
    """Validate email format"""
    email = sanitize_string(email, max_length=254)
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError(
            "Invalid email format",
            details={"value": email}
        )
    
    return email.lower()


def validate_farm_name(name: str) -> str:
    """Validate and sanitize farm name"""
    name = sanitize_string(name, max_length=200)
    
    if len(name) < 1:
        raise ValidationError("Farm name is required")
    
    # Check for potentially malicious patterns
    if re.search(r'<script|javascript:|data:', name, re.IGNORECASE):
        raise ValidationError("Invalid characters in farm name")
    
    return name


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate UUID format"""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    if not re.match(pattern, value.lower()):
        raise ValidationError(
            f"Invalid {field_name} format",
            details={"expected": "UUID format"}
        )
    
    return value.lower()


# ============================================================================
# JWT & Token Security
# ============================================================================

class TokenBlacklist:
    """
    In-memory token blacklist for invalidated tokens.
    In production, use Redis or database.
    """
    
    _blacklist: Dict[str, datetime] = {}
    
    @classmethod
    def add(cls, token_hash: str, expires_at: datetime):
        """Add token to blacklist"""
        cls._blacklist[token_hash] = expires_at
        # Clean expired entries
        cls._cleanup()
    
    @classmethod
    def is_blacklisted(cls, token_hash: str) -> bool:
        """Check if token is blacklisted"""
        return token_hash in cls._blacklist
    
    @classmethod
    def _cleanup(cls):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired = [k for k, v in cls._blacklist.items() if v < now]
        for key in expired:
            del cls._blacklist[key]


def hash_token(token: str) -> str:
    """Create a hash of a token for storage/comparison"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks"""
    return hmac.compare_digest(a.encode(), b.encode())


# ============================================================================
# Request Validation Middleware
# ============================================================================

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate incoming requests for security issues:
    - Request size limits
    - Content type validation
    - Header validation
    """
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_CONTENT_TYPES = [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            logger.warning(f"Request too large: {content_length} bytes")
            raise HTTPException(
                status_code=413,
                detail="Request entity too large"
            )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type:
                # Extract base content type (without charset etc)
                base_type = content_type.split(";")[0].strip()
                if base_type and not any(
                    base_type.startswith(allowed) 
                    for allowed in self.ALLOWED_CONTENT_TYPES
                ):
                    logger.warning(f"Invalid content type: {content_type}")
                    raise HTTPException(
                        status_code=415,
                        detail="Unsupported media type"
                    )
        
        return await call_next(request)


# ============================================================================
# API Key Validation
# ============================================================================

def validate_api_key(api_key: str, valid_keys: List[str]) -> bool:
    """
    Validate API key against list of valid keys.
    Uses constant-time comparison to prevent timing attacks.
    """
    for valid_key in valid_keys:
        if constant_time_compare(api_key, valid_key):
            return True
    return False


def mask_api_key(api_key: str) -> str:
    """Mask API key for logging (show first 4 and last 4 chars)"""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"


# ============================================================================
# CSRF Protection
# ============================================================================

def generate_csrf_token() -> str:
    """Generate a CSRF token"""
    return generate_secure_token(32)


def validate_csrf_token(token: str, stored_token: str) -> bool:
    """Validate CSRF token"""
    if not token or not stored_token:
        return False
    return constant_time_compare(token, stored_token)


# ============================================================================
# IP Address Utilities
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Get the real client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    """
    # Check for forwarded header (from load balancer/proxy)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the first IP (original client)
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def is_private_ip(ip: str) -> bool:
    """Check if IP address is private/internal"""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private
    except ValueError:
        return False


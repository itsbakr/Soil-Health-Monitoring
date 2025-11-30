"""
Rate Limiting Configuration for SoilGuard API

Provides:
- Global rate limiting per IP
- Endpoint-specific rate limits
- User-based rate limiting (when authenticated)
- Custom rate limit responses
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def get_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request.
    Uses user ID if authenticated, otherwise falls back to IP address.
    """
    # Try to get user ID from request state (set by auth middleware)
    if hasattr(request.state, 'user_id') and request.state.user_id:
        return f"user:{request.state.user_id}"
    
    # Try to get user ID from auth header (JWT token)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use token hash as identifier for authenticated requests
        token = auth_header[7:]
        # Just use first 16 chars as identifier (not the full token for privacy)
        return f"token:{token[:16]}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter with custom key function
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute"],  # Default global limit
    storage_uri="memory://",  # In-memory storage (use Redis for production)
    strategy="fixed-window"
)


# Rate limit tiers
RATE_LIMITS = {
    # Public endpoints - more restrictive
    "public": "30/minute",
    
    # Authentication endpoints - prevent brute force
    "auth": "10/minute",
    "register": "5/minute",
    
    # Authenticated user endpoints
    "user": "60/minute",
    
    # Analysis endpoints - resource intensive
    "analysis": "10/minute",
    "analysis_heavy": "5/minute",
    
    # Admin endpoints
    "admin": "120/minute",
    
    # Health check - no limit
    "health": "1000/minute"
}


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors"""
    
    # Extract limit info from exception
    retry_after = getattr(exc, 'retry_after', 60)
    
    logger.warning(
        f"Rate limit exceeded for {get_identifier(request)} on {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "identifier": get_identifier(request),
            "limit": str(exc.detail)
        }
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "retry_after_seconds": retry_after,
            "detail": str(exc.detail)
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Remaining": "0"
        }
    )


# Decorator factory for common limits
def limit_public(func):
    """Apply public rate limit"""
    return limiter.limit(RATE_LIMITS["public"])(func)


def limit_auth(func):
    """Apply auth rate limit"""
    return limiter.limit(RATE_LIMITS["auth"])(func)


def limit_analysis(func):
    """Apply analysis rate limit"""
    return limiter.limit(RATE_LIMITS["analysis"])(func)


def limit_heavy_analysis(func):
    """Apply heavy analysis rate limit"""
    return limiter.limit(RATE_LIMITS["analysis_heavy"])(func)


def limit_admin(func):
    """Apply admin rate limit"""
    return limiter.limit(RATE_LIMITS["admin"])(func)


# Exempt paths from rate limiting
EXEMPT_PATHS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json"
]


def should_exempt(request: Request) -> bool:
    """Check if request should be exempt from rate limiting"""
    return request.url.path in EXEMPT_PATHS


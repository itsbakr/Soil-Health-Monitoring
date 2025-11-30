from fastapi import APIRouter, HTTPException, Depends, status, Header, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import httpx
import logging
from config import settings
from utils.security import hash_token, TokenBlacklist, get_client_ip
from utils.rate_limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for user data
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime


class AuthError(BaseModel):
    """Standardized auth error response"""
    error: str
    message: str
    detail: Optional[str] = None


# Supabase JWT verification with enhanced security
async def get_current_user_id(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> str:
    """
    Extract and verify user ID from Supabase JWT token in Authorization header.
    
    Security enhancements:
    - Token blacklist check
    - IP-based rate limiting
    - Secure logging (no token exposure)
    - Timeout handling
    """
    client_ip = get_client_ip(request)
    
    if not authorization:
        logger.warning(f"Missing auth header from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail={"error": "AUTH_REQUIRED", "message": "Authorization header required"}
        )
    
    # Extract bearer token
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid auth format from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_FORMAT", "message": "Invalid authorization format"}
        )
    
    token = authorization.split(" ", 1)[1]
    
    # Check token blacklist
    token_hash = hash_token(token)
    if TokenBlacklist.is_blacklisted(token_hash):
        logger.warning(f"Blacklisted token used from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail={"error": "TOKEN_REVOKED", "message": "Token has been revoked"}
        )
    
    # Validate token length (JWT should be reasonable size)
    if len(token) < 50 or len(token) > 4000:
        logger.warning(f"Suspicious token length ({len(token)}) from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_TOKEN", "message": "Invalid token format"}
        )
    
    try:
        # Development mode fallback
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            if settings.ENVIRONMENT == "production":
                logger.error("Supabase not configured in production!")
                raise HTTPException(
                    status_code=503,
                    detail={"error": "CONFIG_ERROR", "message": "Authentication service misconfigured"}
                )
            logger.warning("No Supabase config found, using development mode")
            return "dev-user-id"
        
        # Verify token with Supabase
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{settings.SUPABASE_URL}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": settings.SUPABASE_ANON_KEY
                    }
                )
            except httpx.TimeoutException:
                logger.error("Supabase auth request timed out")
                if settings.ENVIRONMENT == "production":
                    raise HTTPException(
                        status_code=503,
                        detail={"error": "AUTH_TIMEOUT", "message": "Authentication service unavailable"}
                    )
                return "timeout-user-id"
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("id")
                
                if not user_id:
                    logger.error("No user ID in Supabase response")
                    raise HTTPException(
                        status_code=401,
                        detail={"error": "INVALID_USER", "message": "Invalid user data"}
                    )
                
                # Store user info in request state for downstream use
                request.state.user_id = user_id
                request.state.user_email = user_data.get("email")
                
                logger.debug(f"Authenticated user: {user_id[:8]}...")
                return user_id
            
            elif response.status_code == 401:
                logger.info(f"Invalid/expired token from {client_ip}")
                raise HTTPException(
                    status_code=401,
                    detail={"error": "TOKEN_EXPIRED", "message": "Invalid or expired token"}
                )
            else:
                logger.error(f"Supabase auth error: {response.status_code}")
                raise HTTPException(
                    status_code=401,
                    detail={"error": "AUTH_FAILED", "message": "Authentication failed"}
                )
                
    except httpx.RequestError as e:
        logger.error(f"Supabase connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": "AUTH_UNAVAILABLE", "message": "Authentication service unavailable"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "AUTH_ERROR", "message": "Authentication error occurred"}
        )

@router.get("/profile", response_model=UserResponse)
@limiter.limit("30/minute")
async def get_user_profile(
    request: Request,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's profile information.
    
    Rate limited to 30 requests per minute.
    """
    # Get user email from request state (set during auth)
    user_email = getattr(request.state, 'user_email', 'user@example.com')
    
    # TODO: Fetch full user data from Supabase database using the user ID
    return {
        "id": current_user_id,
        "email": user_email,
        "full_name": None,  # Fetch from database
        "created_at": datetime.utcnow()
    }


@router.get("/verify")
@limiter.limit("60/minute")
async def verify_auth(
    request: Request,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Verify if user is authenticated.
    
    Returns user ID if token is valid.
    Rate limited to 60 requests per minute.
    """
    return {
        "user_id": current_user_id,
        "authenticated": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
    authorization: str = Header(...)
):
    """
    Logout user by blacklisting their token.
    
    The token will be invalidated and cannot be used again.
    """
    token = authorization.split(" ", 1)[1]
    token_hash = hash_token(token)
    
    # Add to blacklist with 24 hour expiry
    TokenBlacklist.add(
        token_hash,
        datetime.utcnow() + timedelta(hours=24)
    )
    
    logger.info(f"User {current_user_id[:8]}... logged out")
    
    return {
        "message": "Successfully logged out",
        "timestamp": datetime.utcnow().isoformat()
    } 
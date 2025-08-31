from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import httpx
from config import settings

router = APIRouter()

# Pydantic models for user data
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime

# Supabase JWT verification
async def get_current_user_id(authorization: Optional[str] = Header(None)):
    """
    Extract and verify user ID from Supabase JWT token in Authorization header
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    
    try:
        # For development/hackathon: Simple validation by calling Supabase auth API
        # In production, you would decode and verify the JWT locally with the public key
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            # If no Supabase config, allow for development
            print("⚠️ No Supabase config found, using development mode")
            return "dev-user-id"
        
        # Verify token with Supabase (with timeout and retry)
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
                print("⏰ Supabase auth request timed out, using fallback")
                # In development, allow the request to proceed
                return "timeout-user-id"
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("id")
                if user_id:
                    print(f"✅ Authenticated user: {user_id}")
                    return user_id
                else:
                    raise HTTPException(status_code=401, detail="Invalid user data in token")
            else:
                print(f"❌ Supabase auth validation failed: {response.status_code}")
                raise HTTPException(status_code=401, detail="Invalid or expired token")
                
    except httpx.RequestError:
        print("❌ Failed to connect to Supabase for token validation")
        raise HTTPException(status_code=401, detail="Authentication service unavailable")
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user_id: str = Depends(get_current_user_id)):
    """
    Get current user's profile information
    """
    # TODO: Fetch real user data from Supabase database using the user ID
    return {
        "id": current_user_id,
        "email": "user@example.com",
        "full_name": "John Doe", 
        "created_at": datetime.utcnow()
    }

@router.get("/verify")
async def verify_auth(current_user_id: str = Depends(get_current_user_id)):
    """
    Simple endpoint to verify if user is authenticated
    Returns user ID if token is valid
    """
    return {"user_id": current_user_id, "authenticated": True} 
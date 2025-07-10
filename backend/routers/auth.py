from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

# Pydantic models for user data
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime

# Simple auth verification for Supabase integration
async def get_current_user_id(authorization: Optional[str] = Header(None)):
    """
    Extract user ID from Supabase JWT token in Authorization header
    For hackathon simplicity, we'll do basic validation
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    
    # TODO: In production, verify the JWT token with Supabase
    # For hackathon, we'll do basic validation and extract user ID
    # This is where you would verify the token with Supabase's JWT verification
    
    # Placeholder: extract user ID from token (in real implementation, decode JWT)
    # For now, return a placeholder user ID
    return "user-placeholder-id"

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user_id: str = Depends(get_current_user_id)):
    """
    Get current user's profile information
    Note: With Supabase Auth, authentication is handled client-side
    This endpoint just returns user data for authenticated requests
    """
    # TODO: Fetch user data from Supabase database using the user ID
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
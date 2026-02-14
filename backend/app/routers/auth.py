"""
Authentication router - handles login, logout, and user session management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import get_db, get_supabase_client
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

# Request/Response models
class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login"""
    token: str  # Google OAuth token from frontend

class EmailPasswordRequest(BaseModel):
    """Request body for email/password login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """User data returned to frontend"""
    id: str
    email: str
    display_name: str
    avatar_url: Optional[str]
    clout_score: float
    clout_rank: str
    balance_virtual: float
    balance_cash: float
    total_bets_placed: int
    total_bets_won: int
    total_markets_created: int
    streak_current: int
    streak_best: int

    class Config:
        from_attributes = True
        # Allow UUID to be converted to string
        json_encoders = {
            'UUID': lambda v: str(v)
        }

    @classmethod
    def model_validate(cls, obj):
        """Override to convert UUID to string"""
        if hasattr(obj, 'id'):
            obj_dict = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            obj_dict['id'] = str(obj.id)
            return cls(**obj_dict)
        return super().model_validate(obj)

class LoginResponse(BaseModel):
    """Response from successful login"""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(
    auth_request: EmailPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.

    DEV MODE: For demo/testing, accepts demo@prophecy.com with any password.
    """
    try:
        # DEV MODE: Auto-create demo user for testing
        if auth_request.email == "demo@prophecy.com":
            email = auth_request.email
            display_name = "Demo User"
            avatar_url = None
            # Generate a simple token for dev mode
            access_token = f"dev-token-{email}"

            # Check if user exists in our database
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            # Create user if doesn't exist
            if not user:
                user = User(
                    email=email,
                    display_name=display_name,
                    avatar_url=avatar_url,
                    clout_score=1000.0,
                    clout_rank="silver",
                    balance_virtual=1000.0,
                    balance_cash=0.0
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)

            # Return user data and token
            return LoginResponse(
                user=UserResponse.model_validate(user),
                access_token=access_token,
                token_type="bearer"
            )

        # Production mode: Use Supabase (currently disabled due to timeout issues)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only demo@prophecy.com is supported in dev mode"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/google-login", response_model=LoginResponse)
async def google_login(
    auth_request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with Google OAuth via Supabase (alternative endpoint).

    Flow:
    1. Frontend gets Google OAuth token
    2. Send to this endpoint
    3. Validate with Supabase
    4. Create/get user in our database
    5. Return user data and session
    """
    try:
        # Verify token with Supabase
        supabase = get_supabase_client()

        # Exchange Google token for Supabase session
        auth_response = supabase.auth.get_user(auth_request.token)

        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google authentication token"
            )

        supabase_user = auth_response.user
        email = supabase_user.email
        display_name = supabase_user.user_metadata.get("full_name", email.split("@")[0])
        avatar_url = supabase_user.user_metadata.get("avatar_url")

        # Check if user exists in our database
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Create user if doesn't exist
        if not user:
            user = User(
                email=email,
                display_name=display_name,
                avatar_url=avatar_url,
                clout_score=1000.0,
                clout_rank="silver",
                balance_virtual=1000.0,
                balance_cash=0.0
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Return user data and session
        return LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=auth_request.token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    In a token-based system, this is handled client-side by removing the token.
    Server-side we can invalidate the session if needed.
    """
    # For Supabase, logout is typically handled client-side
    # Here we just confirm the user is authenticated
    return {
        "message": "Logged out successfully",
        "user_id": str(current_user.id)
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    This is the primary endpoint frontend uses to check auth status.
    """
    return UserResponse.model_validate(current_user)

@router.get("/health")
async def auth_health_check():
    """Check if auth system is working"""
    try:
        supabase = get_supabase_client()
        return {
            "status": "healthy",
            "supabase_connected": True,
            "supabase_url": supabase.supabase_url
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "supabase_connected": False,
            "error": str(e)
        }

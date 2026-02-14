"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta

from app.database import get_db, get_supabase_client
from app.models.user import User
from app.config import settings


router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.

    Dev mode: Accept demo@prophecy.com with any password
    Production: Use Supabase auth
    """
    # Dev mode: Auto-login for demo account
    if settings.debug and request.email == "demo@prophecy.com":
        # Get or create demo user
        result = await db.execute(
            select(User).where(User.email == "demo@prophecy.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email="demo@prophecy.com",
                display_name="Demo User",
                tokens=10000.0,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Return dev token
        return TokenResponse(
            access_token="dev-token",
            token_type="bearer",
            user=user.to_dict()
        )

    # Production: Use Supabase
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Get or create user in our database
        result = await db.execute(
            select(User).where(User.email == response.user.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=response.user.email,
                display_name=response.user.user_metadata.get("display_name", response.user.email.split("@")[0]),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return TokenResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            user=user.to_dict()
        )

    except Exception as e:
        # Fallback to simple JWT if Supabase not configured
        if not settings.supabase_url:
            # Simple auth for testing
            result = await db.execute(
                select(User).where(User.email == request.email)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Generate simple JWT
            token_data = {
                "sub": user.email,
                "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
            }
            token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)

            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=user.to_dict()
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up with email and password.

    Production: Use Supabase auth
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Production: Use Supabase
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "display_name": request.display_name
                }
            }
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed"
            )

        # Create user in our database
        user = User(
            email=response.user.email,
            display_name=request.display_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return TokenResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            user=user.to_dict()
        )

    except Exception as e:
        # Fallback to simple auth if Supabase not configured
        if not settings.supabase_url:
            # Create user with simple auth
            user = User(
                email=request.email,
                display_name=request.display_name,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Generate simple JWT
            token_data = {
                "sub": user.email,
                "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
            }
            token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)

            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=user.to_dict()
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout():
    """
    Logout (client should discard token).
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me():
    """
    Get current user info.
    (Use /api/users/me instead)
    """
    return {"message": "Use /api/users/me to get current user info"}

"""
FastAPI dependencies for auth, database, etc.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import jwt
from datetime import datetime, timedelta

from app.database import get_db, get_supabase_client
from app.models.user import User
from app.config import settings

# Security scheme for JWT Bearer tokens
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    DEV MODE: Accepts dev-token-{email} format for testing.
    """
    token = credentials.credentials

    try:
        # DEV MODE: Handle dev tokens
        if token.startswith("dev-token-"):
            email = token.replace("dev-token-", "")

            # Get user from database
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found in database"
                )

            return user

        # Production: Verify token with Supabase (currently disabled)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only dev tokens supported in dev mode"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns User if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and unauthenticated users.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    Note: For Supabase auth, we primarily use their tokens.
    This is a backup/supplementary token system.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

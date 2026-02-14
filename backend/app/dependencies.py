"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import jwt

from app.database import get_db, get_supabase_client
from app.models.user import User
from app.config import settings


# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Dev mode: Accept demo@prophecy.com with dev tokens
    Production: Verify Supabase JWT

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        Current User object

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Dev mode: Accept demo tokens
    if settings.debug and token == "dev-token":
        # Return demo user
        result = await db.execute(
            select(User).where(User.email == "demo@prophecy.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create demo user if doesn't exist
            user = User(
                email="demo@prophecy.com",
                display_name="Demo User",
                tokens=10000.0,  # Generous starting balance for testing
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    # Production mode: Verify Supabase JWT
    try:
        # For Supabase, we can verify the JWT or use Supabase client
        supabase = get_supabase_client()

        # Get user from Supabase
        response = supabase.auth.get_user(token)
        supabase_user = response.user

        if not supabase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        # Get or create user in our database
        result = await db.execute(
            select(User).where(User.email == supabase_user.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user from Supabase data
            user = User(
                email=supabase_user.email,
                display_name=supabase_user.user_metadata.get("display_name", supabase_user.email.split("@")[0]),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    except Exception as e:
        # If Supabase not configured, fall back to simple JWT
        if not settings.supabase_url:
            try:
                payload = jwt.decode(
                    token,
                    settings.secret_key,
                    algorithms=[settings.algorithm]
                )
                email = payload.get("sub")

                if not email:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token",
                    )

                result = await db.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()

                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                    )

                return user

            except jwt.InvalidTokenError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that have different behavior for authenticated users.

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_room_access(is_creator: bool = False):
    """
    Dependency factory for room access control.

    Args:
        is_creator: If True, require user to be room creator

    Returns:
        Dependency function
    """
    async def check_access(
        room_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        from app.models.room import Room

        # Get room
        result = await db.execute(
            select(Room).where(Room.id == room_id)
        )
        room = result.scalar_one_or_none()

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )

        # Check creator requirement
        if is_creator and room.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only room creator can perform this action"
            )

        # Check if room is public or user is member
        # TODO: Implement membership check

        return room

    return check_access

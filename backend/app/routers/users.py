"""
User routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user


router = APIRouter()


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user.to_dict()


@router.patch("/me")
async def update_profile(
    updates: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    if updates.display_name is not None:
        current_user.display_name = updates.display_name
    if updates.avatar_url is not None:
        current_user.avatar_url = updates.avatar_url
    if updates.bio is not None:
        current_user.bio = updates.bio

    await db.commit()
    await db.refresh(current_user)

    return current_user.to_dict()


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user profile by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user.to_dict()


@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Calculate additional stats
    # TODO: Get trading history, portfolio value, etc.

    return {
        "user_id": user.id,
        "display_name": user.display_name,
        "level": user.level,
        "experience": user.experience,
        "reputation": user.reputation,
        "total_trades": user.total_trades,
        "successful_predictions": user.successful_predictions,
        "tokens": user.tokens,
        "win_rate": (
            user.successful_predictions / user.total_trades
            if user.total_trades > 0 else 0.0
        ),
    }

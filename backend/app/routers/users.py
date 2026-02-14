"""
Users router - handles user profile operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

# Request/Response models
class UpdateProfileRequest(BaseModel):
    """Request to update user profile"""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserStatsResponse(BaseModel):
    """Detailed user statistics"""
    id: str
    display_name: str
    avatar_url: Optional[str]
    clout_score: float
    clout_rank: str
    total_bets_placed: int
    total_bets_won: int
    total_markets_created: int
    streak_current: int
    streak_best: int
    win_rate: float
    balance_virtual: float
    balance_cash: float

@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public profile of any user by ID"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user.to_dict()

@router.patch("/{user_id}")
async def update_user_profile(
    user_id: str,
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile (only own profile)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Check if user is updating their own profile
    if current_user.id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    # Update fields
    if update_data.display_name is not None:
        current_user.display_name = update_data.display_name
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return current_user.to_dict()

@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed statistics for a user"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserStatsResponse(
        id=str(user.id),
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        clout_score=user.clout_score,
        clout_rank=user.clout_rank,
        total_bets_placed=user.total_bets_placed,
        total_bets_won=user.total_bets_won,
        total_markets_created=user.total_markets_created,
        streak_current=user.streak_current,
        streak_best=user.streak_best,
        win_rate=user.win_rate,
        balance_virtual=user.balance_virtual,
        balance_cash=user.balance_cash
    )

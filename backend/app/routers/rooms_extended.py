"""
Extended room endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.room import Room
from app.models.user import User
from app.dependencies import get_current_user


router = APIRouter()


class JoinRoomRequest(BaseModel):
    join_code: Optional[str] = None
    role: str = "participant"


@router.post("/{room_id}/join")
async def join_room(
    room_id: str,
    request: JoinRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a room."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # TODO: Check if already a member
    # TODO: Create membership record
    # For now, just increment member count
    room.member_count += 1
    await db.commit()
    await db.refresh(room)

    return {"message": "Joined room successfully", "room": room.to_dict()}


@router.post("/{room_id}/leave")
async def leave_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a room."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # TODO: Delete membership record
    # For now, just decrement member count
    if room.member_count > 0:
        room.member_count -= 1
    await db.commit()

    return {"message": "Left room successfully"}


@router.get("/{room_id}/feed")
async def get_room_feed(
    room_id: str,
    cursor: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get room activity feed."""
    from app.models.market import Market

    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Get markets for this room
    result = await db.execute(
        select(Market).where(Market.room_id == room_id).order_by(desc(Market.created_at))
    )
    markets = result.scalars().all()

    # Return markets as feed items
    return {
        "items": [market.to_dict() for market in markets],
        "next_cursor": None,
        "has_more": False
    }


@router.get("/{room_id}/leaderboard")
async def get_room_leaderboard(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room leaderboard."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # TODO: Calculate actual leaderboard from trades
    # For now, return empty leaderboard
    return {
        "leaderboard": [],
        "user_rank": None
    }


@router.get("/{room_id}/vibe-check")
async def get_room_vibe_check(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room vibe check (sentiment analysis)."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # TODO: Calculate actual vibe from activity
    return {
        "vibe_score": 0.7,
        "sentiment": "positive",
        "trending_topics": []
    }


@router.get("/{room_id}/members")
async def get_room_members(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room members."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # TODO: Get actual members from membership table
    # For now, return empty list
    return {
        "members": [],
        "total": room.member_count
    }


@router.patch("/{room_id}/settings")
async def update_room_settings(
    room_id: str,
    settings: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update room settings."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    if room.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room creator can update settings"
        )

    # Update allowed settings
    for key, value in settings.items():
        if hasattr(room, key):
            setattr(room, key, value)

    room.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(room)

    return room.to_dict()

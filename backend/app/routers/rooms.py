"""
Room routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random
import string

from app.database import get_db
from app.models.room import Room, RoomStatus
from app.models.user import User
from app.dependencies import get_current_user


def generate_join_code(length=8):
    """Generate a random join code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


router = APIRouter()


class CreateRoomRequest(BaseModel):
    name: str
    description: Optional[str] = None
    slug: str
    is_public: bool = True
    theme_color: Optional[str] = None
    cover_image: Optional[str] = None
    max_members: int = 100


class UpdateRoomRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    theme_color: Optional[str] = None
    cover_image: Optional[str] = None
    max_members: Optional[int] = None
    status: Optional[RoomStatus] = None


@router.get("/")
async def list_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[RoomStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all public rooms."""
    query = select(Room).where(Room.is_public == True)

    if status:
        query = query.where(Room.status == status)

    query = query.order_by(Room.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    rooms = result.scalars().all()

    return [room.to_dict() for room in rooms]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_room(
    request: CreateRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new room."""
    # Check if slug is unique
    result = await db.execute(
        select(Room).where(Room.slug == request.slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already in use"
        )

    # Generate unique join code
    while True:
        join_code = generate_join_code()
        result = await db.execute(
            select(Room).where(Room.join_code == join_code)
        )
        if not result.scalar_one_or_none():
            break

    # Create room
    room = Room(
        name=request.name,
        description=request.description,
        slug=request.slug,
        join_code=join_code,
        creator_id=current_user.id,
        is_public=request.is_public,
        theme_color=request.theme_color,
        cover_image=request.cover_image,
        max_members=request.max_members,
        member_count=1,  # Creator is first member
    )

    db.add(room)
    await db.commit()
    await db.refresh(room)

    return room.to_dict()


@router.get("/{room_id}")
async def get_room(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room by ID."""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    return room.to_dict()


@router.get("/slug/{slug}")
async def get_room_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room by slug."""
    result = await db.execute(
        select(Room).where(Room.slug == slug)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    return room.to_dict()


@router.patch("/{room_id}")
async def update_room(
    room_id: str,
    updates: UpdateRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update room (creator only)."""
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

    # Check permission
    if room.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room creator can update room"
        )

    # Apply updates
    if updates.name is not None:
        room.name = updates.name
    if updates.description is not None:
        room.description = updates.description
    if updates.is_public is not None:
        room.is_public = updates.is_public
    if updates.theme_color is not None:
        room.theme_color = updates.theme_color
    if updates.cover_image is not None:
        room.cover_image = updates.cover_image
    if updates.max_members is not None:
        room.max_members = updates.max_members
    if updates.status is not None:
        room.status = updates.status

    room.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(room)

    return room.to_dict()


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete room (creator only)."""
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

    # Check permission
    if room.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room creator can delete room"
        )

    await db.delete(room)
    await db.commit()

    return None


@router.get("/{room_id}/stats")
async def get_room_stats(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room statistics."""
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

    # TODO: Calculate more detailed stats
    # - Active markets
    # - Top traders
    # - Recent activity

    return {
        "room_id": room.id,
        "member_count": room.member_count,
        "market_count": room.market_count,
        "total_volume": room.total_volume,
        "created_at": room.created_at.isoformat() if room.created_at else None,
    }

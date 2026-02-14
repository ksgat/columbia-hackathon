"""
Rooms router - handles room creation, joining, and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.database import get_db
from app.models.room import Room, Membership
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter()

# Request/Response models
class CreateRoomRequest(BaseModel):
    """Request to create a new room"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    currency_mode: str = Field(default="virtual", pattern="^(virtual|cash)$")
    min_bet: float = Field(default=10.0, gt=0)
    max_bet: float = Field(default=500.0, gt=0)
    max_members: int = Field(default=50, gt=0, le=100)

class JoinRoomRequest(BaseModel):
    """Request to join a room via join code"""
    join_code: str = Field(..., min_length=6, max_length=6)
    role: str = Field(default="participant", pattern="^(participant|spectator)$")

class RoomResponse(BaseModel):
    """Room data with member count"""
    id: str
    name: str
    description: Optional[str]
    join_code: str
    creator_id: str
    currency_mode: str
    min_bet: float
    max_bet: float
    member_count: int
    spectator_count: int
    max_members: int
    is_active: bool
    created_at: str

class MemberResponse(BaseModel):
    """Member info in a room"""
    user_id: str
    display_name: str
    avatar_url: Optional[str]
    role: str
    coins_virtual: float
    joined_at: str

class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    user_id: str
    display_name: str
    avatar_url: Optional[str]
    clout_score: float
    clout_rank: str
    coins_virtual: float
    total_bets_placed: int
    total_bets_won: int
    win_rate: float

@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: CreateRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new prediction market room.
    Creator automatically becomes admin.
    """
    # Generate unique join code
    max_attempts = 10
    join_code = None

    for _ in range(max_attempts):
        code = Room.generate_join_code()
        # Check if code already exists
        result = await db.execute(select(Room).where(Room.join_code == code))
        if result.scalar_one_or_none() is None:
            join_code = code
            break

    if not join_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique join code"
        )

    # Create room
    room = Room(
        name=room_data.name,
        description=room_data.description,
        join_code=join_code,
        creator_id=current_user.id,
        currency_mode=room_data.currency_mode,
        min_bet=room_data.min_bet,
        max_bet=room_data.max_bet,
        max_members=room_data.max_members
    )

    db.add(room)
    await db.flush()  # Get room.id

    # Create membership for creator as admin
    membership = Membership(
        user_id=current_user.id,
        room_id=room.id,
        role="admin",
        coins_virtual=500.0
    )

    db.add(membership)
    await db.commit()
    await db.refresh(room)

    # Return room with member count
    return RoomResponse(
        id=str(room.id),
        name=room.name,
        description=room.description,
        join_code=room.join_code,
        creator_id=str(room.creator_id),
        currency_mode=room.currency_mode,
        min_bet=room.min_bet,
        max_bet=room.max_bet,
        member_count=1,
        spectator_count=0,
        max_members=room.max_members,
        is_active=room.is_active,
        created_at=room.created_at.isoformat()
    )

@router.get("", response_model=List[RoomResponse])
async def list_user_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all rooms the current user is a member of"""
    # Get user's memberships
    result = await db.execute(
        select(Membership).where(Membership.user_id == current_user.id)
    )
    memberships = result.scalars().all()

    room_ids = [m.room_id for m in memberships]

    if not room_ids:
        return []

    # Get rooms
    result = await db.execute(
        select(Room).where(Room.id.in_(room_ids))
    )
    rooms = result.scalars().all()

    # Get member counts for each room
    room_responses = []
    for room in rooms:
        # Count participants and spectators
        result = await db.execute(
            select(func.count(Membership.id))
            .where(Membership.room_id == room.id)
            .where(Membership.role == "participant")
        )
        participant_count = result.scalar() or 0

        result = await db.execute(
            select(func.count(Membership.id))
            .where(Membership.room_id == room.id)
            .where(Membership.role == "spectator")
        )
        spectator_count = result.scalar() or 0

        room_responses.append(RoomResponse(
            id=str(room.id),
            name=room.name,
            description=room.description,
            join_code=room.join_code,
            creator_id=str(room.creator_id),
            currency_mode=room.currency_mode,
            min_bet=room.min_bet,
            max_bet=room.max_bet,
            member_count=participant_count,
            spectator_count=spectator_count,
            max_members=room.max_members,
            is_active=room.is_active,
            created_at=room.created_at.isoformat()
        ))

    return room_responses

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get room details by ID"""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    result = await db.execute(select(Room).where(Room.id == room_uuid))
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Get member counts
    result = await db.execute(
        select(func.count(Membership.id))
        .where(Membership.room_id == room.id)
        .where(Membership.role.in_(["participant", "admin"]))
    )
    member_count = result.scalar() or 0

    result = await db.execute(
        select(func.count(Membership.id))
        .where(Membership.room_id == room.id)
        .where(Membership.role == "spectator")
    )
    spectator_count = result.scalar() or 0

    return RoomResponse(
        id=str(room.id),
        name=room.name,
        description=room.description,
        join_code=room.join_code,
        creator_id=str(room.creator_id),
        currency_mode=room.currency_mode,
        min_bet=room.min_bet,
        max_bet=room.max_bet,
        member_count=member_count,
        spectator_count=spectator_count,
        max_members=room.max_members,
        is_active=room.is_active,
        created_at=room.created_at.isoformat()
    )

@router.post("/{room_id}/join")
async def join_room(
    room_id: str,
    join_data: JoinRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a room via join code"""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Get room by ID and verify join code
    result = await db.execute(
        select(Room).where(
            and_(Room.id == room_uuid, Room.join_code == join_data.join_code)
        )
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found or invalid join code"
        )

    # Check if user is already a member
    result = await db.execute(
        select(Membership).where(
            and_(Membership.user_id == current_user.id, Membership.room_id == room.id)
        )
    )
    existing_membership = result.scalar_one_or_none()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this room"
        )

    # Check room capacity
    result = await db.execute(
        select(func.count(Membership.id)).where(Membership.room_id == room.id)
    )
    member_count = result.scalar() or 0

    if member_count >= room.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is at maximum capacity"
        )

    # Create membership
    membership = Membership(
        user_id=current_user.id,
        room_id=room.id,
        role=join_data.role,
        coins_virtual=500.0  # Starting balance
    )

    db.add(membership)
    await db.commit()

    return {
        "message": "Successfully joined room",
        "room_id": str(room.id),
        "room_name": room.name,
        "role": join_data.role
    }

@router.post("/join")
async def join_room_by_code(
    join_data: JoinRoomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a room using only the join code (convenience endpoint)"""
    # Find room by join code
    result = await db.execute(
        select(Room).where(Room.join_code == join_data.join_code)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid join code"
        )

    # Check if user is already a member
    result = await db.execute(
        select(Membership).where(
            and_(Membership.user_id == current_user.id, Membership.room_id == room.id)
        )
    )
    existing_membership = result.scalar_one_or_none()

    if existing_membership:
        return {
            "message": "Already a member of this room",
            "room_id": str(room.id),
            "room_name": room.name,
            "role": existing_membership.role
        }

    # Check room capacity
    result = await db.execute(
        select(func.count(Membership.id)).where(Membership.room_id == room.id)
    )
    member_count = result.scalar() or 0

    if member_count >= room.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is at maximum capacity"
        )

    # Create membership
    membership = Membership(
        user_id=current_user.id,
        room_id=room.id,
        role=join_data.role,
        coins_virtual=500.0  # Starting balance
    )

    db.add(membership)
    await db.commit()

    return {
        "message": "Successfully joined room",
        "room_id": str(room.id),
        "room_name": room.name,
        "role": join_data.role
    }

@router.post("/{room_id}/leave")
async def leave_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a room"""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Get membership
    result = await db.execute(
        select(Membership).where(
            and_(Membership.user_id == current_user.id, Membership.room_id == room_uuid)
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this room"
        )

    # Delete membership
    await db.delete(membership)
    await db.commit()

    return {
        "message": "Successfully left room",
        "room_id": str(room_uuid)
    }

@router.get("/{room_id}/members", response_model=List[MemberResponse])
async def get_room_members(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all members of a room"""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Get memberships with user data
    result = await db.execute(
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.room_id == room_uuid)
        .order_by(Membership.joined_at)
    )

    members = []
    for membership, user in result.all():
        members.append(MemberResponse(
            user_id=str(user.id),
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=membership.role,
            coins_virtual=membership.coins_virtual,
            joined_at=membership.joined_at.isoformat()
        ))

    return members

@router.get("/{room_id}/leaderboard", response_model=List[LeaderboardEntry])
async def get_room_leaderboard(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get room leaderboard sorted by clout score.
    Includes Prophet as a participant.
    """
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Get members with user data, sorted by clout score
    result = await db.execute(
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.room_id == room_uuid)
        .where(Membership.role.in_(["participant", "admin"]))  # Exclude spectators
        .order_by(User.clout_score.desc())
    )

    leaderboard = []
    rank = 1
    for membership, user in result.all():
        leaderboard.append(LeaderboardEntry(
            rank=rank,
            user_id=str(user.id),
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            clout_score=user.clout_score,
            clout_rank=user.clout_rank,
            coins_virtual=membership.coins_virtual,
            total_bets_placed=user.total_bets_placed,
            total_bets_won=user.total_bets_won,
            win_rate=user.win_rate
        ))
        rank += 1

    return leaderboard

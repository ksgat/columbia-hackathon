"""
Votes router - handles market resolution voting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, Field
from typing import List
import uuid

from app.database import get_db
from app.models.market import Market
from app.models.vote import ResolutionVote
from app.models.room import Membership
from app.models.user import User
from app.dependencies import get_current_user
from app.services.resolution import tally_votes, resolve_market

router = APIRouter()

# Request/Response models
class CastVoteRequest(BaseModel):
    """Request to cast a vote"""
    vote: str = Field(..., pattern="^(yes|no)$")

class VoteSummaryResponse(BaseModel):
    """Summary of votes on a market"""
    market_id: str
    total_votes: int
    yes_votes: int
    no_votes: int
    has_voted: bool
    my_vote: str | None
    voting_deadline: str
    votes_needed_for_majority: int

class ResolveMarketRequest(BaseModel):
    """Request to manually resolve a market (admin only)"""
    result: str = Field(..., pattern="^(yes|no)$")

@router.post("/{market_id}/vote")
async def cast_vote(
    market_id: str,
    vote_data: CastVoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cast a vote on a market resolution.

    Requirements:
    - Market must be in 'voting' status
    - User must be a participant (not spectator) in the room
    - User can only vote once per market
    """
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    # Get market
    result = await db.execute(select(Market).where(Market.id == market_uuid))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Check market is in voting status
    if market.status != 'voting':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market is not in voting status (current: {market.status})"
        )

    # Check user is a participant in the room
    result = await db.execute(
        select(Membership).where(
            and_(
                Membership.user_id == current_user.id,
                Membership.room_id == market.room_id
            )
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )

    if membership.role == "spectator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Spectators cannot vote"
        )

    # Check if user already voted
    result = await db.execute(
        select(ResolutionVote).where(
            and_(
                ResolutionVote.market_id == market.id,
                ResolutionVote.user_id == current_user.id
            )
        )
    )
    existing_vote = result.scalar_one_or_none()

    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already voted on this market"
        )

    # Create vote
    vote = ResolutionVote(
        market_id=market.id,
        user_id=current_user.id,
        vote=vote_data.vote,
        bond_amount=0.0  # TODO: Implement bonds for cash rooms
    )

    db.add(vote)
    await db.commit()

    # Get updated vote tally
    yes_votes, no_votes, total_votes = await tally_votes(str(market.id), db)

    return {
        "message": "Vote cast successfully",
        "market_id": str(market.id),
        "your_vote": vote_data.vote,
        "vote_summary": {
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "total_votes": total_votes
        }
    }

@router.get("/{market_id}/votes", response_model=VoteSummaryResponse)
async def get_vote_summary(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get vote summary for a market.

    Individual votes are hidden until voting deadline.
    """
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    # Get market
    result = await db.execute(select(Market).where(Market.id == market_uuid))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Get vote tally
    yes_votes, no_votes, total_votes = await tally_votes(str(market.id), db)

    # Check if current user voted
    result = await db.execute(
        select(ResolutionVote).where(
            and_(
                ResolutionVote.market_id == market.id,
                ResolutionVote.user_id == current_user.id
            )
        )
    )
    my_vote_record = result.scalar_one_or_none()

    has_voted = my_vote_record is not None
    my_vote = my_vote_record.vote if my_vote_record else None

    # Calculate votes needed for 3/4 supermajority
    # Need 75% of total possible voters (room participants)
    result = await db.execute(
        select(func.count(Membership.id))
        .where(Membership.room_id == market.room_id)
        .where(Membership.role.in_(["participant", "admin"]))
    )
    total_participants = result.scalar() or 0

    votes_needed = max(0, int(total_participants * 0.75) - max(yes_votes, no_votes))

    return VoteSummaryResponse(
        market_id=str(market.id),
        total_votes=total_votes,
        yes_votes=yes_votes,
        no_votes=no_votes,
        has_voted=has_voted,
        my_vote=my_vote,
        voting_deadline=market.voting_deadline.isoformat() if market.voting_deadline else "",
        votes_needed_for_majority=votes_needed
    )

@router.post("/{market_id}/resolve")
async def manually_resolve_market(
    market_id: str,
    resolve_data: ResolveMarketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually resolve a market (admin only).

    For testing and emergency resolution.
    """
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    # Get market
    result = await db.execute(select(Market).where(Market.id == market_uuid))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Check user is admin of the room
    result = await db.execute(
        select(Membership).where(
            and_(
                Membership.user_id == current_user.id,
                Membership.room_id == market.room_id,
                Membership.role == "admin"
            )
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room admins can manually resolve markets"
        )

    # Check market can be resolved
    if market.status == 'resolved':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market is already resolved"
        )

    # Resolve market
    summary = await resolve_market(
        market=market,
        result=resolve_data.result,
        method='admin',
        db=db
    )

    return {
        "message": "Market resolved successfully",
        **summary
    }

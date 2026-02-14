"""
Voting routes for market resolution
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.market import Market, MarketStatus
from app.models.vote import Vote
from app.models.user import User
from app.dependencies import get_current_user
from app.services.resolution import get_resolution_service


router = APIRouter()


class CastVoteRequest(BaseModel):
    outcome: str
    reasoning: Optional[str] = None


class ResolveMarketRequest(BaseModel):
    outcome: str


@router.post("/{market_id}/vote")
async def cast_vote(
    market_id: str,
    request: CastVoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cast a resolution vote for a market."""
    # Get market
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    if market.status == MarketStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market already resolved"
        )

    # Validate outcome
    if request.outcome not in market.shares:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid outcome"
        )

    # Cast vote
    resolution_service = get_resolution_service()
    vote = await resolution_service.cast_vote(
        db=db,
        market_id=market_id,
        user_id=current_user.id,
        outcome=request.outcome,
        reasoning=request.reasoning
    )

    return vote.to_dict()


@router.get("/{market_id}/votes")
async def get_votes(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all votes for a market."""
    # Verify market exists
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Get votes
    result = await db.execute(
        select(Vote).where(Vote.market_id == market_id)
    )
    votes = result.scalars().all()

    return [vote.to_dict() for vote in votes]


@router.get("/{market_id}/tally")
async def get_vote_tally(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get vote tally for a market."""
    resolution_service = get_resolution_service()
    tally = await resolution_service.tally_votes(db, market_id)

    return tally


@router.post("/{market_id}/close")
async def close_market(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Close market for trading and start voting period."""
    # Get market
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Check permission (creator or admin)
    if market.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only market creator can close market"
        )

    if market.status != MarketStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market must be open to close"
        )

    # Close market
    resolution_service = get_resolution_service()
    result = await resolution_service.start_voting(db, market_id)

    return result


@router.post("/{market_id}/resolve")
async def resolve_market(
    market_id: str,
    request: ResolveMarketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a market and pay out winners."""
    # Get market
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Check permission (creator or admin)
    if market.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only market creator can resolve market"
        )

    if market.status == MarketStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market already resolved"
        )

    # Validate outcome
    if request.outcome not in market.shares:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid outcome"
        )

    # Resolve market
    resolution_service = get_resolution_service()
    result = await resolution_service.resolve_market(
        db=db,
        market_id=market_id,
        winning_outcome=request.outcome,
        resolved_by_id=current_user.id
    )

    return result

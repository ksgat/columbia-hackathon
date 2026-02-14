"""
Prophet router - trigger AI agent actions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.room import Room, Membership
from app.models.market import Market
from app.models.user import User
from app.dependencies import get_current_user
from app.services.prophet import (
    generate_markets,
    generate_trade_commentary,
    generate_resolution_commentary,
    resolve_dispute
)

router = APIRouter()

# Response models
class ProphetMarketResponse(BaseModel):
    """Prophet-generated market"""
    title: str
    description: Optional[str]
    category: Optional[str]
    initial_odds_yes: float

class GenerateMarketsResponse(BaseModel):
    """Response from market generation"""
    markets: List[ProphetMarketResponse]
    commentary: str

@router.post("/generate-markets/{room_id}")
async def trigger_market_generation(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger Prophet to generate new markets for a room.

    For now, only room admins can trigger this.
    Future: Run automatically on schedule.
    """
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Get room
    result = await db.execute(select(Room).where(Room.id == room_uuid))
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Check user is admin (for now)
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.room_id == room.id,
            Membership.role == "admin"
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room admins can trigger Prophet market generation"
        )

    # Get room members
    result = await db.execute(
        select(User).join(Membership).where(
            Membership.room_id == room.id,
            Membership.role.in_(["participant", "admin"])
        )
    )
    members = result.scalars().all()
    member_names = [m.display_name for m in members]

    # Get recent markets
    result = await db.execute(
        select(Market.title)
        .where(Market.room_id == room.id)
        .order_by(Market.created_at.desc())
        .limit(10)
    )
    recent_market_titles = [title for (title,) in result.all()]

    # Generate markets with Prophet
    try:
        markets = generate_markets(
            room_name=room.name,
            member_names=member_names,
            recent_markets=recent_market_titles
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prophet market generation failed: {str(e)}"
        )

    # Create markets in database
    created_markets = []
    for market_data in markets[:3]:  # Max 3 markets at a time
        expires_at = datetime.utcnow() + timedelta(hours=48)

        market = Market(
            room_id=room.id,
            creator_id=None,  # Prophet-generated
            title=market_data.get('title', 'Untitled Market'),
            description=market_data.get('description'),
            category=market_data.get('category', 'other'),
            market_type='standard',
            odds_yes=market_data.get('initial_odds_yes', 0.5),
            total_pool=0.0,
            total_yes_shares=0.0,
            total_no_shares=0.0,
            lmsr_b=100.0,
            currency_mode=room.currency_mode,
            status='active',
            expires_at=expires_at
        )

        db.add(market)
        created_markets.append(market_data)

    await db.commit()

    return {
        "message": f"Prophet generated {len(created_markets)} markets",
        "markets": created_markets,
        "commentary": f"🤖 Prophet has spoken! {len(created_markets)} new markets await your wisdom."
    }

@router.post("/resolve-dispute/{market_id}")
async def trigger_dispute_resolution(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger Prophet to resolve a disputed market.

    Called automatically when a market enters 'disputed' status.
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

    # Check market is disputed
    if market.status != 'disputed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market is not disputed (status: {market.status})"
        )

    # Get vote counts
    from app.services.resolution import tally_votes
    yes_votes, no_votes, total_votes = await tally_votes(str(market.id), db)

    # Get Prophet's ruling
    try:
        ruling_data = resolve_dispute(
            market_title=market.title,
            description=market.description,
            yes_votes=yes_votes,
            no_votes=no_votes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prophet dispute resolution failed: {str(e)}"
        )

    # Resolve market with Prophet's ruling
    from app.services.resolution import resolve_market

    summary = await resolve_market(
        market=market,
        result=ruling_data['ruling'],
        method='prophet',
        db=db
    )

    return {
        "message": "Prophet has resolved the dispute",
        "ruling": ruling_data['ruling'],
        "confidence": ruling_data.get('confidence', 0.5),
        "reasoning": ruling_data.get('reasoning', 'Prophet has spoken'),
        **summary
    }

@router.get("/status")
async def prophet_status():
    """Check if Prophet AI is available"""
    from app.config import settings

    return {
        "status": "online" if settings.openrouter_api_key else "offline",
        "model": settings.openrouter_model,
        "capabilities": [
            "market_generation",
            "trade_commentary",
            "dispute_resolution",
            "betting"
        ]
    }

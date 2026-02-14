"""
Market routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.room import Room
from app.models.user import User
from app.models.market import Market
from app.models.trade import Trade
from app.dependencies import get_current_user


router = APIRouter()


class CreateMarketRequest(BaseModel):
    room_id: str
    title: str  # Will map to 'question' in model
    description: Optional[str] = None
    expires_at: Optional[datetime] = None  # Will map to 'close_time' in model


class TradeRequest(BaseModel):
    side: str  # 'yes' or 'no'
    amount: float


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_market(
    request: CreateMarketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new market."""
    # Verify room exists
    result = await db.execute(
        select(Room).where(Room.id == request.room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Set default expiry if not provided (7 days from now)
    if request.expires_at:
        # Remove timezone info if present
        close_time = request.expires_at.replace(tzinfo=None) if request.expires_at.tzinfo else request.expires_at
    else:
        close_time = datetime.utcnow() + timedelta(days=7)

    # Create market
    market = Market(
        id=str(uuid.uuid4()),
        room_id=request.room_id,
        question=request.title,  # Map title to question
        description=request.description,
        creator_id=current_user.id,
        market_type='BINARY',
        status='OPEN',
        shares={"yes": 0, "no": 0},
        prices={"yes": 0.5, "no": 0.5},
        close_time=close_time,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(market)

    # Update room market count
    room.market_count += 1

    await db.commit()
    await db.refresh(market)

    return market.to_dict()


@router.get("/{market_id}")
async def get_market(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get market by ID."""
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    return market.to_dict()


@router.post("/{market_id}/trade")
async def trade(
    market_id: str,
    request: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Place a trade on a market."""
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

    if market.status.value != 'open':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market is not active"
        )

    # Validate side
    if request.side not in ['yes', 'no']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Side must be 'yes' or 'no'"
        )

    # Check user has enough balance
    if current_user.tokens < request.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )

    # Get current prices from market
    current_prices = market.prices or {"yes": 0.5, "no": 0.5}
    current_price = current_prices.get(request.side, 0.5)

    # Calculate shares bought
    shares_bought = request.amount / current_price if current_price > 0 else request.amount

    # Create trade
    from app.models.trade import TradeType
    trade = Trade(
        id=str(uuid.uuid4()),
        market_id=market_id,
        user_id=current_user.id,
        trade_type=TradeType.BUY,
        outcome=request.side,
        shares=shares_bought,
        price=current_price,
        cost=request.amount,
        created_at=datetime.utcnow()
    )

    db.add(trade)

    # Update market shares
    current_shares = market.shares or {"yes": 0, "no": 0}
    current_shares[request.side] = current_shares.get(request.side, 0) + shares_bought
    market.shares = current_shares

    # Simple price update (constant product formula)
    total_yes = current_shares.get("yes", 0)
    total_no = current_shares.get("no", 0)
    total = total_yes + total_no

    if total > 0:
        market.prices = {
            "yes": total_yes / total,
            "no": total_no / total
        }

    market.total_volume += request.amount
    market.updated_at = datetime.utcnow()

    # Update user balance and stats
    current_user.tokens -= request.amount
    current_user.total_trades += 1
    current_user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(trade)
    await db.refresh(market)
    await db.refresh(current_user)

    return {
        "trade": trade.to_dict(),
        "market": market.to_dict(),
        "user_balance": current_user.tokens
    }


@router.get("/{market_id}/trades")
async def get_market_trades(
    market_id: str,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get trades for a market."""
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Get trades
    offset = (page - 1) * limit
    result = await db.execute(
        select(Trade)
        .where(Trade.market_id == market_id)
        .order_by(desc(Trade.created_at))
        .offset(offset)
        .limit(limit)
    )
    trades = result.scalars().all()

    return {
        "trades": [trade.to_dict() for trade in trades],
        "page": page,
        "total": len(trades)
    }


@router.get("/{market_id}/chain")
async def get_market_chain(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get market chain (derivative markets)."""
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # TODO: Implement market chains
    return {
        "parent": None,
        "children": []
    }


@router.get("/{market_id}/derivatives")
async def get_market_derivatives(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get derivative markets."""
    # TODO: Implement derivatives
    return {"derivatives": []}


@router.get("/{market_id}/votes")
async def get_market_votes(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get resolution votes for a market."""
    # TODO: Implement voting
    return {
        "votes": [],
        "yes_votes": 0,
        "no_votes": 0,
        "total_votes": 0
    }


@router.post("/{market_id}/vote")
async def vote_on_market(
    market_id: str,
    vote: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Vote on market resolution."""
    # TODO: Implement voting
    return {"message": "Vote recorded"}


@router.post("/{market_id}/cancel")
async def cancel_market(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a market (creator only)."""
    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    if market.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only market creator can cancel"
        )

    from app.models.market import MarketStatus
    market.status = MarketStatus.CANCELLED
    market.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": "Market cancelled"}

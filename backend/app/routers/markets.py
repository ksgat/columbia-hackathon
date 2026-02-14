"""
Markets router - handles market creation and trading
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json

from app.database import get_db
from app.models.market import Market
from app.models.trade import Trade
from app.models.room import Room, Membership
from app.models.user import User
from app.dependencies import get_current_user
from app.services.lmsr import LMSRMarketMaker
from app.services.chains import (
    validate_chain_creation,
    get_chain_tree,
    get_pending_children,
    get_active_children
)
from app.services.derivatives import (
    validate_derivative_creation,
    generate_derivative_title,
    get_derivative_status,
    check_all_active_derivatives
)

router = APIRouter()

# Request/Response models
class CreateMarketRequest(BaseModel):
    """Request to create a new market"""
    room_id: str
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    expires_in_hours: int = Field(default=48, gt=0, le=168)  # Max 7 days
    initial_odds_yes: float = Field(default=0.5, ge=0.01, le=0.99)

class CreateChainedMarketRequest(BaseModel):
    """Request to create a chained market"""
    parent_market_id: str
    trigger_condition: str = Field(..., pattern="^(parent_resolves_yes|parent_resolves_no)$")
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    initial_odds_yes: float = Field(default=0.5, ge=0.01, le=0.99)

class CreateDerivativeRequest(BaseModel):
    """Request to create a derivative market"""
    reference_market_id: str
    threshold_type: str = Field(..., pattern="^(odds_threshold|volume_threshold|resolution_method)$")
    threshold_value: str  # Flexible: float for odds/volume, string for resolution_method
    threshold_deadline: Optional[datetime] = None  # Required for odds/volume, optional for resolution_method
    initial_odds_yes: float = Field(default=0.5, ge=0.01, le=0.99)
    auto_title: bool = Field(default=True)  # Auto-generate title or provide custom
    custom_title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "derivative"

class TradeRequest(BaseModel):
    """Request to place a trade"""
    side: str = Field(..., pattern="^(yes|no)$")
    amount: float = Field(..., gt=0)

class TradeResponse(BaseModel):
    """Response from placing a trade"""
    trade_id: str
    shares_received: float
    new_odds_yes: float
    new_odds_no: float
    new_balance: float

class MarketDetailResponse(BaseModel):
    """Detailed market information"""
    id: str
    room_id: str
    creator_id: Optional[str]
    title: str
    description: Optional[str]
    category: Optional[str]
    odds_yes: float
    odds_no: float
    total_pool: float
    status: str
    expires_at: str
    created_at: str
    trade_count: int
    my_position: Optional[dict]  # User's position if logged in

@router.get("")
async def get_markets(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all markets in a room"""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Verify user is a member
    result = await db.execute(
        select(Membership).where(
            and_(Membership.user_id == current_user.id, Membership.room_id == room_uuid)
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this room"
        )

    # Get markets
    result = await db.execute(
        select(Market)
        .where(Market.room_id == room_uuid)
        .order_by(Market.created_at.desc())
    )
    markets = result.scalars().all()

    # Convert to response format
    return [{
        "id": str(m.id),
        "room_id": str(m.room_id),
        "creator_id": str(m.creator_id) if m.creator_id else None,
        "title": m.title,
        "description": m.description,
        "category": m.category,
        "market_type": m.market_type,
        "odds_yes": m.odds_yes,
        "odds_no": m.odds_no,
        "total_pool": m.total_pool,
        "total_yes_shares": m.total_yes_shares,
        "total_no_shares": m.total_no_shares,
        "lmsr_b": m.lmsr_b,
        "currency_mode": m.currency_mode,
        "status": m.status,
        "resolution_result": m.resolution_result,
        "resolution_method": m.resolution_method,
        "expires_at": m.expires_at.isoformat(),
        "voting_deadline": m.voting_deadline.isoformat() if m.voting_deadline else None,
        "resolved_at": m.resolved_at.isoformat() if m.resolved_at else None,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat(),
        "parent_market_id": str(m.parent_market_id) if m.parent_market_id else None,
        "trigger_condition": m.trigger_condition,
        "chain_depth": m.chain_depth,
        "reference_market_id": str(m.reference_market_id) if m.reference_market_id else None,
        "threshold_condition": m.threshold_condition,
        "threshold_deadline": m.threshold_deadline.isoformat() if m.threshold_deadline else None,
    } for m in markets]

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_market(
    market_data: CreateMarketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new prediction market.
    User must be a participant in the room.
    """
    try:
        room_uuid = uuid.UUID(market_data.room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID format"
        )

    # Check room exists
    result = await db.execute(select(Room).where(Room.id == room_uuid))
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Check user is a participant in the room
    result = await db.execute(
        select(Membership).where(
            and_(
                Membership.user_id == current_user.id,
                Membership.room_id == room.id,
                Membership.role.in_(["participant", "admin"])
            )
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a participant in this room to create markets"
        )

    # Create market
    expires_at = datetime.utcnow() + timedelta(hours=market_data.expires_in_hours)

    market = Market(
        room_id=room.id,
        creator_id=current_user.id,
        title=market_data.title,
        description=market_data.description,
        category=market_data.category,
        market_type="standard",
        odds_yes=market_data.initial_odds_yes,
        total_pool=0.0,
        total_yes_shares=0.0,
        total_no_shares=0.0,
        lmsr_b=100.0,  # Default liquidity parameter
        currency_mode=room.currency_mode,
        status="active",
        expires_at=expires_at
    )

    db.add(market)

    # Update user stats
    current_user.total_markets_created += 1

    await db.commit()
    await db.refresh(market)

    return market.to_dict()

@router.get("/{market_id}", response_model=MarketDetailResponse)
async def get_market(
    market_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed market information"""
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    result = await db.execute(select(Market).where(Market.id == market_uuid))
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    # Get trade count
    result = await db.execute(
        select(func.count(Trade.id)).where(Trade.market_id == market.id)
    )
    trade_count = result.scalar() or 0

    # Get user's position if logged in
    my_position = None
    if current_user:
        result = await db.execute(
            select(Trade).where(
                and_(
                    Trade.market_id == market.id,
                    Trade.user_id == current_user.id
                )
            )
        )
        user_trades = result.scalars().all()

        if user_trades:
            yes_shares = sum(t.shares_received for t in user_trades if t.side == "yes")
            no_shares = sum(t.shares_received for t in user_trades if t.side == "no")
            total_spent = sum(t.amount for t in user_trades)

            my_position = {
                "yes_shares": yes_shares,
                "no_shares": no_shares,
                "total_spent": total_spent
            }

    return MarketDetailResponse(
        id=str(market.id),
        room_id=str(market.room_id),
        creator_id=str(market.creator_id) if market.creator_id else None,
        title=market.title,
        description=market.description,
        category=market.category,
        odds_yes=market.odds_yes,
        odds_no=market.odds_no,
        total_pool=market.total_pool,
        status=market.status,
        expires_at=market.expires_at.isoformat(),
        created_at=market.created_at.isoformat(),
        trade_count=trade_count,
        my_position=my_position
    )

@router.get("/{market_id}/trades", response_model=List[dict])
async def get_market_trades(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get trade history for a market"""
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    # Get trades with user info
    result = await db.execute(
        select(Trade, User)
        .outerjoin(User, Trade.user_id == User.id)
        .where(Trade.market_id == market_uuid)
        .order_by(Trade.created_at.desc())
    )

    trades = []
    for trade, user in result.all():
        trade_dict = trade.to_dict()
        if user:
            trade_dict["user_display_name"] = user.display_name
            trade_dict["user_avatar_url"] = user.avatar_url
        else:
            trade_dict["user_display_name"] = "Prophet"
            trade_dict["user_avatar_url"] = None

        trades.append(trade_dict)

    return trades

@router.post("/{market_id}/trade", response_model=TradeResponse)
async def place_trade(
    market_id: str,
    trade_data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    🎯 THE MOST CRITICAL ENDPOINT 🎯

    Place a trade on a market using LMSR.

    Flow:
    1. Validate market is active
    2. Check user has sufficient balance
    3. Execute LMSR trade
    4. Deduct balance
    5. Record trade
    6. Update market state
    7. Return new odds and balance
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

    # Validate market is active
    if market.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market is not active (status: {market.status})"
        )

    # Get user's membership in this room
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
            detail="Spectators cannot place trades"
        )

    # Check sufficient balance
    if membership.coins_virtual < trade_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. You have {membership.coins_virtual} coins, need {trade_data.amount}"
        )

    # Initialize LMSR with current market state
    lmsr = LMSRMarketMaker(
        b=market.lmsr_b,
        yes_shares=market.total_yes_shares,
        no_shares=market.total_no_shares
    )

    # Capture odds before trade
    odds_before = market.odds_yes

    # Execute trade
    try:
        shares_received, new_odds_yes, new_odds_no = lmsr.execute_trade(
            trade_data.side,
            trade_data.amount
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trade execution failed: {str(e)}"
        )

    # Deduct balance from membership
    membership.coins_virtual -= trade_data.amount

    # Create trade record
    trade = Trade(
        market_id=market.id,
        user_id=current_user.id,
        is_prophet_trade=False,
        side=trade_data.side,
        amount=trade_data.amount,
        shares_received=shares_received,
        odds_at_trade=odds_before,
        currency="virtual"
    )
    db.add(trade)

    # Update market state
    market.total_yes_shares = lmsr.yes_shares
    market.total_no_shares = lmsr.no_shares
    market.odds_yes = new_odds_yes
    market.total_pool += trade_data.amount

    # Update user stats
    current_user.total_bets_placed += 1

    await db.commit()
    await db.refresh(trade)
    await db.refresh(membership)

    return TradeResponse(
        trade_id=str(trade.id),
        shares_received=shares_received,
        new_odds_yes=new_odds_yes,
        new_odds_no=new_odds_no,
        new_balance=membership.coins_virtual
    )

# ============================================================================
# CHAINED MARKETS ENDPOINTS
# ============================================================================

@router.post("/chains/create")
async def create_chained_market(
    chain_data: CreateChainedMarketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a chained market that activates when parent resolves.

    Chained markets start in 'pending' status and activate when
    their parent resolves with the matching condition.

    Max chain depth: 2 levels (root → child only)
    """
    try:
        parent_uuid = uuid.UUID(chain_data.parent_market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parent market ID format"
        )

    # Validate chain creation
    is_valid, error_msg, new_depth = await validate_chain_creation(
        parent_market_id=parent_uuid,
        trigger_condition=chain_data.trigger_condition,
        db=db
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Get parent market to inherit room_id
    result = await db.execute(select(Market).where(Market.id == parent_uuid))
    parent_market = result.scalar_one()

    # Create the chained market in 'pending' status
    new_market = Market(
        room_id=parent_market.room_id,
        creator_id=current_user.id,
        title=chain_data.title,
        description=chain_data.description,
        category=chain_data.category,
        market_type='chained',
        parent_market_id=parent_uuid,
        trigger_condition=chain_data.trigger_condition,
        chain_depth=new_depth,
        odds_yes=chain_data.initial_odds_yes,
        total_pool=0.0,
        total_yes_shares=0.0,
        total_no_shares=0.0,
        lmsr_b=100.0,
        currency_mode=parent_market.currency_mode,
        status='pending',  # Starts pending, activates when parent resolves
        expires_at=datetime.utcnow() + timedelta(hours=48)  # Will be reset on activation
    )

    db.add(new_market)
    current_user.total_markets_created += 1

    await db.commit()
    await db.refresh(new_market)

    return {
        "message": "Chained market created successfully",
        "market": new_market.to_dict(),
        "parent_market_id": str(parent_uuid),
        "trigger_condition": chain_data.trigger_condition,
        "status": "pending",
        "activation_info": f"Will activate when '{parent_market.title}' resolves {chain_data.trigger_condition.replace('parent_resolves_', '').upper()}"
    }

@router.get("/{market_id}/chain-tree")
async def get_market_chain_tree(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the full chain tree for a market.

    Returns the root market and all children in a nested tree structure.
    """
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    tree = await get_chain_tree(market_uuid, db)

    if "error" in tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=tree["error"]
        )

    return tree

@router.get("/{market_id}/children")
async def get_market_children(
    market_id: str,
    status_filter: Optional[str] = None,  # 'pending', 'active', or None for all
    db: AsyncSession = Depends(get_db)
):
    """
    Get child markets for a parent market.

    Query params:
    - status_filter: 'pending' or 'active' to filter by status
    """
    try:
        market_uuid = uuid.UUID(market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid market ID format"
        )

    # Verify parent market exists
    result = await db.execute(select(Market).where(Market.id == market_uuid))
    parent_market = result.scalar_one_or_none()

    if not parent_market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent market not found"
        )

    if status_filter == 'pending':
        children = await get_pending_children(market_uuid, db)
    elif status_filter == 'active':
        children = await get_active_children(market_uuid, db)
    else:
        # Get all children
        result = await db.execute(
            select(Market)
            .where(Market.parent_market_id == market_uuid)
            .order_by(Market.created_at)
        )
        children = result.scalars().all()

    return {
        "parent_market_id": str(market_uuid),
        "parent_market_title": parent_market.title,
        "parent_status": parent_market.status,
        "children_count": len(children),
        "children": [child.to_dict() for child in children]
    }

# ============================================================================
# DERIVATIVE MARKETS ENDPOINTS
# ============================================================================

@router.post("/derivatives/create")
async def create_derivative_market(
    deriv_data: CreateDerivativeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a derivative market that bets on another market's behavior.

    Derivative types:
    - odds_threshold: Bet on market hitting X% odds by deadline
    - volume_threshold: Bet on market getting Y+ trades by deadline
    - resolution_method: Bet on how market will resolve (community/prophet/admin/automatic)

    Derivatives auto-resolve when conditions are checked (via background task).
    """
    try:
        reference_uuid = uuid.UUID(deriv_data.reference_market_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reference market ID format"
        )

    # Parse threshold_value based on type
    threshold_type = deriv_data.threshold_type
    try:
        if threshold_type in ['odds_threshold', 'volume_threshold']:
            threshold_value = float(deriv_data.threshold_value)
        else:  # resolution_method
            threshold_value = deriv_data.threshold_value
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid threshold_value for {threshold_type}"
        )

    # Validate derivative creation
    is_valid, error_msg = await validate_derivative_creation(
        reference_market_id=reference_uuid,
        threshold_type=threshold_type,
        threshold_value=threshold_value,
        threshold_deadline=deriv_data.threshold_deadline,
        db=db
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Get reference market
    result = await db.execute(select(Market).where(Market.id == reference_uuid))
    reference_market = result.scalar_one()

    # Generate title if auto_title
    if deriv_data.auto_title:
        title = await generate_derivative_title(
            reference_market_title=reference_market.title,
            threshold_type=threshold_type,
            threshold_value=threshold_value,
            threshold_deadline=deriv_data.threshold_deadline
        )
    else:
        if not deriv_data.custom_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="custom_title required when auto_title=False"
            )
        title = deriv_data.custom_title

    # Create threshold_condition JSON
    threshold_condition = json.dumps({
        "type": threshold_type,
        "value": threshold_value
    })

    # Determine expiration (slightly after deadline or when reference expires)
    if deriv_data.threshold_deadline:
        expires_at = deriv_data.threshold_deadline + timedelta(hours=1)
    else:
        # For resolution_method derivatives, expire when reference expires
        expires_at = reference_market.expires_at

    # Create the derivative market
    new_derivative = Market(
        room_id=reference_market.room_id,
        creator_id=current_user.id,
        title=title,
        description=deriv_data.description,
        category=deriv_data.category,
        market_type='derivative',
        reference_market_id=reference_uuid,
        threshold_condition=threshold_condition,
        threshold_deadline=deriv_data.threshold_deadline,
        odds_yes=deriv_data.initial_odds_yes,
        total_pool=0.0,
        total_yes_shares=0.0,
        total_no_shares=0.0,
        lmsr_b=100.0,
        currency_mode=reference_market.currency_mode,
        status='active',
        expires_at=expires_at
    )

    db.add(new_derivative)
    current_user.total_markets_created += 1

    await db.commit()
    await db.refresh(new_derivative)

    return {
        "message": "Derivative market created successfully",
        "market": new_derivative.to_dict(),
        "reference_market_id": str(reference_uuid),
        "threshold_type": threshold_type,
        "threshold_value": threshold_value,
        "deadline": deriv_data.threshold_deadline.isoformat() if deriv_data.threshold_deadline else None,
        "auto_resolves": True
    }

@router.get("/{market_id}/derivative-status")
async def get_market_derivative_status(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current status of a derivative market.

    Shows:
    - Current progress toward threshold
    - Reference market current state
    - Time remaining until deadline
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
    derivative = result.scalar_one_or_none()

    if not derivative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )

    if derivative.market_type != 'derivative':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market is not a derivative"
        )

    status_data = await get_derivative_status(derivative, db)

    if "error" in status_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_data["error"]
        )

    return status_data

@router.post("/derivatives/check-all")
async def check_all_derivatives(
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger derivative condition checking.

    This is normally done automatically via background task,
    but this endpoint allows manual triggering for testing.

    Admin-only in production.
    """
    resolved = await check_all_active_derivatives(db)

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "derivatives_resolved": len(resolved),
        "resolved_markets": resolved
    }

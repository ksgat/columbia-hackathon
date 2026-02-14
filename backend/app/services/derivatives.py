"""
Derivatives Service - Handle meta-markets that bet on market behavior

Derivatives are markets that bet on the behavior of other markets, not real-world outcomes.

Types:
- Odds Threshold: "Will market X hit Y% odds before date Z?"
- Volume Threshold: "Will market X get Y+ trades?"
- Resolution Method: "Will market X resolve via Prophet dispute?"
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
import json

from app.models.market import Market
from app.models.trade import Trade

async def validate_derivative_creation(
    reference_market_id: uuid.UUID,
    threshold_type: str,
    threshold_value: float,
    threshold_deadline: Optional[datetime],
    db: AsyncSession
) -> tuple[bool, Optional[str]]:
    """
    Validate that a derivative market can be created.

    Args:
        reference_market_id: UUID of reference market
        threshold_type: Type of derivative ('odds_threshold', 'volume_threshold', 'resolution_method')
        threshold_value: Threshold value to check
        threshold_deadline: Deadline for threshold (required for odds/volume)
        db: Database session

    Returns:
        (is_valid, error_message)
    """
    # Check threshold type is valid
    valid_types = ['odds_threshold', 'volume_threshold', 'resolution_method']
    if threshold_type not in valid_types:
        return False, f"Invalid threshold type. Must be one of: {valid_types}"

    # Get reference market
    result = await db.execute(select(Market).where(Market.id == reference_market_id))
    reference_market = result.scalar_one_or_none()

    if not reference_market:
        return False, "Reference market not found"

    # Check reference market is not itself a derivative
    if reference_market.market_type == 'derivative':
        return False, "Cannot create a derivative of a derivative"

    # Check reference market is not already resolved
    if reference_market.status == 'resolved':
        return False, "Cannot create derivative of an already-resolved market"

    # Validate threshold_value based on type
    if threshold_type == 'odds_threshold':
        if not (0 < threshold_value <= 1.0):
            return False, "Odds threshold must be between 0 and 1.0"
        if not threshold_deadline:
            return False, "Odds threshold requires a deadline"
        if threshold_deadline <= datetime.now(timezone.utc):
            return False, "Deadline must be in the future"

    elif threshold_type == 'volume_threshold':
        if threshold_value < 1:
            return False, "Volume threshold must be at least 1 trade"
        if not threshold_deadline:
            return False, "Volume threshold requires a deadline"
        if threshold_deadline <= datetime.now(timezone.utc):
            return False, "Deadline must be in the future"

    elif threshold_type == 'resolution_method':
        valid_methods = ['community', 'prophet', 'admin', 'automatic']
        if threshold_value not in valid_methods:
            return False, f"Resolution method must be one of: {valid_methods}"
        # No deadline needed for resolution_method type

    return True, None


async def check_derivative_condition(
    derivative_market: Market,
    db: AsyncSession
) -> Optional[str]:
    """
    Check if a derivative market's condition has been met.

    Args:
        derivative_market: The derivative market to check
        db: Database session

    Returns:
        'yes' if condition met, 'no' if deadline passed without meeting, None if still pending
    """
    if derivative_market.market_type != 'derivative':
        return None

    if derivative_market.status != 'active':
        return None

    # Parse threshold condition
    try:
        condition = json.loads(derivative_market.threshold_condition)
    except (json.JSONDecodeError, TypeError):
        return None

    threshold_type = condition.get('type')
    threshold_value = condition.get('value')

    # Get reference market
    result = await db.execute(
        select(Market).where(Market.id == derivative_market.reference_market_id)
    )
    reference_market = result.scalar_one_or_none()

    if not reference_market:
        return None

    # Check condition based on type
    if threshold_type == 'odds_threshold':
        # Check if reference market hit the odds threshold
        if reference_market.odds_yes >= threshold_value:
            return 'yes'
        # Check if deadline has passed
        elif derivative_market.threshold_deadline and datetime.now(timezone.utc) >= derivative_market.threshold_deadline:
            return 'no'

    elif threshold_type == 'volume_threshold':
        # Count trades on reference market
        result = await db.execute(
            select(func.count(Trade.id)).where(Trade.market_id == reference_market.id)
        )
        trade_count = result.scalar() or 0

        if trade_count >= threshold_value:
            return 'yes'
        # Check if deadline has passed
        elif derivative_market.threshold_deadline and datetime.now(timezone.utc) >= derivative_market.threshold_deadline:
            return 'no'

    elif threshold_type == 'resolution_method':
        # Check if reference market resolved with the specified method
        if reference_market.status == 'resolved':
            if reference_market.resolution_method == threshold_value:
                return 'yes'
            else:
                return 'no'

    # Still pending
    return None


async def check_all_active_derivatives(db: AsyncSession) -> List[Dict]:
    """
    Check all active derivative markets and auto-resolve if conditions are met.

    This should be called periodically (e.g., every 60 seconds via background task).

    Args:
        db: Database session

    Returns:
        List of resolved derivatives with their results
    """
    from app.services.resolution import resolve_market

    # Get all active derivatives
    result = await db.execute(
        select(Market).where(
            Market.market_type == 'derivative',
            Market.status == 'active'
        )
    )
    derivatives = result.scalars().all()

    resolved_list = []

    for deriv in derivatives:
        # Check condition
        result = await check_derivative_condition(deriv, db)

        if result:
            # Auto-resolve the derivative
            summary = await resolve_market(deriv, result, 'automatic', db)
            resolved_list.append({
                'derivative_id': str(deriv.id),
                'title': deriv.title,
                'result': result,
                **summary
            })

    return resolved_list


async def generate_derivative_title(
    reference_market_title: str,
    threshold_type: str,
    threshold_value: any,
    threshold_deadline: Optional[datetime]
) -> str:
    """
    Generate a descriptive title for a derivative market.

    Args:
        reference_market_title: Title of reference market
        threshold_type: Type of derivative
        threshold_value: Threshold value
        threshold_deadline: Deadline (if applicable)

    Returns:
        Generated title string
    """
    if threshold_type == 'odds_threshold':
        odds_pct = int(threshold_value * 100)
        deadline_str = threshold_deadline.strftime('%b %d') if threshold_deadline else "soon"
        return f"Will '{reference_market_title}' hit {odds_pct}% odds by {deadline_str}?"

    elif threshold_type == 'volume_threshold':
        deadline_str = threshold_deadline.strftime('%b %d') if threshold_deadline else "soon"
        return f"Will '{reference_market_title}' get {int(threshold_value)}+ trades by {deadline_str}?"

    elif threshold_type == 'resolution_method':
        method_name = threshold_value.capitalize()
        return f"Will '{reference_market_title}' resolve via {method_name}?"

    else:
        return f"Derivative: {reference_market_title}"


async def get_derivative_status(
    derivative_market: Market,
    db: AsyncSession
) -> Dict:
    """
    Get current status of a derivative market (how close to threshold, etc.).

    Args:
        derivative_market: The derivative market
        db: Database session

    Returns:
        Dict with status information
    """
    if derivative_market.market_type != 'derivative':
        return {"error": "Not a derivative market"}

    # Parse condition
    try:
        condition = json.loads(derivative_market.threshold_condition)
    except (json.JSONDecodeError, TypeError):
        return {"error": "Invalid threshold condition"}

    threshold_type = condition.get('type')
    threshold_value = condition.get('value')

    # Get reference market
    result = await db.execute(
        select(Market).where(Market.id == derivative_market.reference_market_id)
    )
    reference_market = result.scalar_one_or_none()

    if not reference_market:
        return {"error": "Reference market not found"}

    status_data = {
        "derivative_id": str(derivative_market.id),
        "reference_market_id": str(reference_market.id),
        "reference_market_title": reference_market.title,
        "threshold_type": threshold_type,
        "threshold_value": threshold_value,
        "deadline": derivative_market.threshold_deadline.isoformat() if derivative_market.threshold_deadline else None,
    }

    # Add type-specific current values
    if threshold_type == 'odds_threshold':
        status_data["current_odds"] = reference_market.odds_yes
        status_data["progress_percent"] = (reference_market.odds_yes / threshold_value) * 100 if threshold_value > 0 else 0

    elif threshold_type == 'volume_threshold':
        result = await db.execute(
            select(func.count(Trade.id)).where(Trade.market_id == reference_market.id)
        )
        trade_count = result.scalar() or 0
        status_data["current_volume"] = trade_count
        status_data["progress_percent"] = (trade_count / threshold_value) * 100 if threshold_value > 0 else 0

    elif threshold_type == 'resolution_method':
        status_data["reference_status"] = reference_market.status
        status_data["reference_resolution_method"] = reference_market.resolution_method

    return status_data

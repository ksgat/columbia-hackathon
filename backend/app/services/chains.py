"""
Chain Market Service - Handle conditional/chained markets

Chained markets are "if-then" markets where child markets activate
based on parent market resolution outcomes.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import uuid

from app.models.market import Market

MAX_CHAIN_DEPTH = 2  # Root → Child only (2 levels)

async def validate_chain_creation(
    parent_market_id: uuid.UUID,
    trigger_condition: str,
    db: AsyncSession
) -> tuple[bool, Optional[str], Optional[int]]:
    """
    Validate that a chained market can be created.

    Args:
        parent_market_id: UUID of parent market
        trigger_condition: Trigger condition ('parent_resolves_yes' or 'parent_resolves_no')
        db: Database session

    Returns:
        (is_valid, error_message, parent_depth)
    """
    # Check trigger condition is valid
    valid_conditions = ['parent_resolves_yes', 'parent_resolves_no']
    if trigger_condition not in valid_conditions:
        return False, f"Invalid trigger condition. Must be one of: {valid_conditions}", None

    # Get parent market
    result = await db.execute(select(Market).where(Market.id == parent_market_id))
    parent = result.scalar_one_or_none()

    if not parent:
        return False, "Parent market not found", None

    # Check parent is not already resolved
    if parent.status == 'resolved':
        return False, "Cannot chain to an already-resolved market", None

    # Check chain depth limit (max 2 levels: root → child)
    parent_depth = parent.chain_depth
    new_depth = parent_depth + 1

    if new_depth >= MAX_CHAIN_DEPTH:
        return False, f"Maximum chain depth is {MAX_CHAIN_DEPTH} levels (root → child only)", None

    return True, None, new_depth


async def get_chain_tree(
    market_id: uuid.UUID,
    db: AsyncSession
) -> Dict:
    """
    Get the full chain tree for a market (parent and children).

    Args:
        market_id: UUID of any market in the chain
        db: Database session

    Returns:
        Dict with chain tree structure
    """
    # Get the market
    result = await db.execute(select(Market).where(Market.id == market_id))
    market = result.scalar_one_or_none()

    if not market:
        return {"error": "Market not found"}

    # Find root of chain (traverse up)
    root = market
    while root.parent_market_id:
        result = await db.execute(select(Market).where(Market.id == root.parent_market_id))
        parent = result.scalar_one_or_none()
        if parent:
            root = parent
        else:
            break

    # Build tree from root
    async def build_tree_node(m: Market) -> Dict:
        # Get children
        result = await db.execute(
            select(Market).where(Market.parent_market_id == m.id).order_by(Market.created_at)
        )
        children = result.scalars().all()

        node = {
            "market": m.to_dict(),
            "children": []
        }

        for child in children:
            child_node = await build_tree_node(child)
            node["children"].append(child_node)

        return node

    tree = await build_tree_node(root)
    return tree


async def activate_child_markets(
    parent_market: Market,
    resolution_result: str,
    db: AsyncSession
) -> List[Market]:
    """
    Activate child markets when parent resolves.

    Args:
        parent_market: The resolved parent market
        resolution_result: 'yes' or 'no'
        db: Database session

    Returns:
        List of activated child markets
    """
    # Find children that match the resolution condition
    trigger_condition = f"parent_resolves_{resolution_result}"

    result = await db.execute(
        select(Market).where(
            Market.parent_market_id == parent_market.id,
            Market.trigger_condition == trigger_condition,
            Market.status == 'pending'
        )
    )
    children = result.scalars().all()

    activated = []
    for child in children:
        # Activate the market
        child.status = 'active'
        # Set expiration (48 hours from activation)
        child.expires_at = datetime.utcnow() + timedelta(hours=48)
        activated.append(child)

    if activated:
        await db.commit()

    return activated


async def get_pending_children(
    parent_market_id: uuid.UUID,
    db: AsyncSession
) -> List[Market]:
    """
    Get all pending child markets for a parent.

    Args:
        parent_market_id: UUID of parent market
        db: Database session

    Returns:
        List of pending child markets
    """
    result = await db.execute(
        select(Market).where(
            Market.parent_market_id == parent_market_id,
            Market.status == 'pending'
        ).order_by(Market.trigger_condition)
    )
    return result.scalars().all()


async def get_active_children(
    parent_market_id: uuid.UUID,
    db: AsyncSession
) -> List[Market]:
    """
    Get all active child markets for a parent.

    Args:
        parent_market_id: UUID of parent market
        db: Database session

    Returns:
        List of active child markets
    """
    result = await db.execute(
        select(Market).where(
            Market.parent_market_id == parent_market_id,
            Market.status == 'active'
        ).order_by(Market.created_at)
    )
    return result.scalars().all()

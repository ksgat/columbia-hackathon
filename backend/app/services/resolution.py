"""
Market Resolution Service

Handles:
- Vote tallying
- 3/4 supermajority checking
- Payout distribution
- Clout score updates
- User stat updates
"""
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional

from app.models.market import Market
from app.models.trade import Trade
from app.models.vote import ResolutionVote
from app.models.room import Membership
from app.models.user import User
from app.services.clout import calculate_clout_change, update_user_clout, update_user_streak
from app.services.chains import activate_child_markets

async def tally_votes(market_id: str, db: AsyncSession) -> Tuple[int, int, int]:
    """
    Tally votes for a market.

    Args:
        market_id: Market UUID
        db: Database session

    Returns:
        Tuple of (yes_votes, no_votes, total_votes)
    """
    result = await db.execute(
        select(ResolutionVote.vote, func.count(ResolutionVote.id))
        .where(ResolutionVote.market_id == market_id)
        .group_by(ResolutionVote.vote)
    )

    vote_counts = dict(result.all())
    yes_votes = vote_counts.get('yes', 0)
    no_votes = vote_counts.get('no', 0)
    total_votes = yes_votes + no_votes

    return yes_votes, no_votes, total_votes

async def check_supermajority(
    yes_votes: int,
    no_votes: int,
    total_votes: int
) -> Optional[str]:
    """
    Check if there's a 3/4 supermajority.

    Args:
        yes_votes: Number of YES votes
        no_votes: Number of NO votes
        total_votes: Total votes cast

    Returns:
        'yes' if YES has 3/4+, 'no' if NO has 3/4+, None if disputed
    """
    if total_votes == 0:
        return None

    yes_ratio = yes_votes / total_votes
    no_ratio = no_votes / total_votes

    if yes_ratio >= 0.75:
        return 'yes'
    elif no_ratio >= 0.75:
        return 'no'
    else:
        return None  # Disputed - no supermajority

async def resolve_market(
    market: Market,
    result: str,
    method: str,
    db: AsyncSession
) -> dict:
    """
    Resolve a market and distribute payouts.

    Args:
        market: Market to resolve
        result: 'yes' or 'no'
        method: 'community', 'prophet', or 'admin'
        db: Database session

    Returns:
        Dictionary with resolution summary
    """
    if result not in ['yes', 'no']:
        raise ValueError("Result must be 'yes' or 'no'")

    # Update market status
    market.status = 'resolved'
    market.resolution_result = result
    market.resolution_method = method
    market.resolved_at = func.now()

    # Get all trades on this market
    result_query = await db.execute(
        select(Trade).where(Trade.market_id == market.id)
    )
    trades = result_query.scalars().all()

    # Distribute payouts and update clout
    total_payout = 0
    winners_count = 0
    losers_count = 0

    for trade in trades:
        # Skip Prophet trades for now (Prophet handled separately)
        if trade.is_prophet_trade:
            continue

        # Get user
        user_result = await db.execute(
            select(User).where(User.id == trade.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            continue

        # Get user's membership in this room
        membership_result = await db.execute(
            select(Membership).where(
                and_(
                    Membership.user_id == user.id,
                    Membership.room_id == market.room_id
                )
            )
        )
        membership = membership_result.scalar_one_or_none()

        if not membership:
            continue

        # Check if user won
        user_won = (trade.side == result)

        # Calculate payout (winning shares pay 1:1)
        if user_won:
            payout = trade.shares_received * 1.0  # Each share pays 1 coin
            membership.coins_virtual += payout
            membership.coins_earned_total += payout
            total_payout += payout
            winners_count += 1

            # Update user stats
            user.total_bets_won += 1
            update_user_streak(user, won=True)
        else:
            losers_count += 1
            update_user_streak(user, won=False)

        # Update clout score (win or lose)
        clout_change = calculate_clout_change(
            user_won=user_won,
            odds_at_trade=trade.odds_at_trade,
            user_side=trade.side
        )
        update_user_clout(user, clout_change)

    await db.commit()

    # Activate child markets if this is a parent
    activated_children = await activate_child_markets(market, result, db)
    activated_count = len(activated_children)

    return {
        "market_id": str(market.id),
        "result": result,
        "method": method,
        "total_payout": total_payout,
        "winners_count": winners_count,
        "losers_count": losers_count,
        "total_trades": len(trades),
        "children_activated": activated_count,
        "activated_markets": [str(child.id) for child in activated_children] if activated_children else []
    }

async def process_voting_deadline(market: Market, db: AsyncSession) -> dict:
    """
    Process a market when voting deadline is reached.

    Args:
        market: Market to process
        db: Database session

    Returns:
        Resolution summary
    """
    # Tally votes
    yes_votes, no_votes, total_votes = await tally_votes(str(market.id), db)

    # Check for supermajority
    result = await check_supermajority(yes_votes, no_votes, total_votes)

    if result:
        # Community reached consensus
        summary = await resolve_market(market, result, 'community', db)
        summary['vote_summary'] = {
            'yes_votes': yes_votes,
            'no_votes': no_votes,
            'total_votes': total_votes,
            'supermajority': True
        }
        return summary
    else:
        # Disputed - needs Prophet intervention
        market.status = 'disputed'
        await db.commit()

        return {
            "market_id": str(market.id),
            "status": "disputed",
            "vote_summary": {
                'yes_votes': yes_votes,
                'no_votes': no_votes,
                'total_votes': total_votes,
                'supermajority': False
            },
            "message": "No supermajority reached. Prophet will resolve."
        }

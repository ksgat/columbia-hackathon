"""
Market resolution service
Handles resolving markets and paying out winners
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict
from datetime import datetime

from app.models.market import Market, MarketStatus
from app.models.trade import Trade
from app.models.vote import Vote
from app.models.user import User


class ResolutionService:
    """Service for resolving prediction markets."""

    async def resolve_market(
        self,
        db: AsyncSession,
        market_id: str,
        winning_outcome: str,
        resolved_by_id: str
    ) -> Dict:
        """
        Resolve a market and pay out winners.

        Args:
            db: Database session
            market_id: Market to resolve
            winning_outcome: The outcome that occurred
            resolved_by_id: User ID of resolver

        Returns:
            Dictionary with resolution details
        """
        # Get market
        result = await db.execute(
            select(Market).where(Market.id == market_id)
        )
        market = result.scalar_one_or_none()

        if not market:
            raise ValueError(f"Market {market_id} not found")

        if market.status == MarketStatus.RESOLVED:
            raise ValueError("Market already resolved")

        # Update market
        market.status = MarketStatus.RESOLVED
        market.resolution = winning_outcome
        market.resolved_at = datetime.utcnow()
        market.resolved_by = resolved_by_id

        # Get all trades for this market
        result = await db.execute(
            select(Trade)
            .where(Trade.market_id == market_id)
            .order_by(Trade.created_at)
        )
        trades = result.scalars().all()

        # Calculate positions for each user
        positions = self._calculate_positions(trades)

        # Pay out winners
        payout_total = 0.0
        winners = []

        for user_id, position in positions.items():
            # Get shares in winning outcome
            winning_shares = position.get(winning_outcome, 0.0)

            if winning_shares > 0:
                # Each winning share pays out 1 token
                payout = winning_shares

                # Update user balance
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(tokens=User.tokens + payout)
                )

                payout_total += payout
                winners.append({
                    "user_id": user_id,
                    "shares": winning_shares,
                    "payout": payout
                })

        await db.commit()

        return {
            "market_id": market_id,
            "winning_outcome": winning_outcome,
            "total_payout": payout_total,
            "winner_count": len(winners),
            "winners": winners,
        }

    async def start_voting(
        self,
        db: AsyncSession,
        market_id: str
    ) -> Dict:
        """
        Start resolution voting period for a market.

        Args:
            db: Database session
            market_id: Market to start voting on

        Returns:
            Dictionary with voting details
        """
        # Get market
        result = await db.execute(
            select(Market).where(Market.id == market_id)
        )
        market = result.scalar_one_or_none()

        if not market:
            raise ValueError(f"Market {market_id} not found")

        if market.status != MarketStatus.OPEN:
            raise ValueError("Market must be open to start voting")

        # Close market for trading
        market.status = MarketStatus.CLOSED

        await db.commit()

        return {
            "market_id": market_id,
            "status": "voting_open",
            "message": "Market closed, voting period started"
        }

    async def cast_vote(
        self,
        db: AsyncSession,
        market_id: str,
        user_id: str,
        outcome: str,
        reasoning: Optional[str] = None
    ) -> Vote:
        """
        Cast a resolution vote.

        Args:
            db: Database session
            market_id: Market to vote on
            user_id: User casting vote
            outcome: Which outcome to vote for
            reasoning: Optional explanation

        Returns:
            The created vote
        """
        # Check if user already voted
        result = await db.execute(
            select(Vote).where(
                Vote.market_id == market_id,
                Vote.user_id == user_id
            )
        )
        existing_vote = result.scalar_one_or_none()

        if existing_vote:
            # Update existing vote
            existing_vote.outcome = outcome
            existing_vote.reasoning = reasoning
            existing_vote.updated_at = datetime.utcnow()
            vote = existing_vote
        else:
            # Create new vote
            vote = Vote(
                market_id=market_id,
                user_id=user_id,
                outcome=outcome,
                reasoning=reasoning,
                weight=1.0  # TODO: Calculate based on reputation, shares held, etc.
            )
            db.add(vote)

        await db.commit()
        await db.refresh(vote)

        return vote

    async def tally_votes(
        self,
        db: AsyncSession,
        market_id: str
    ) -> Dict:
        """
        Tally votes for a market.

        Args:
            db: Database session
            market_id: Market to tally

        Returns:
            Dictionary with vote tallies
        """
        # Get all votes
        result = await db.execute(
            select(Vote).where(Vote.market_id == market_id)
        )
        votes = result.scalars().all()

        # Count weighted votes
        tallies = {}
        for vote in votes:
            tallies[vote.outcome] = tallies.get(vote.outcome, 0.0) + vote.weight

        # Sort by vote count
        sorted_results = sorted(
            tallies.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "market_id": market_id,
            "total_votes": len(votes),
            "tallies": tallies,
            "ranked_outcomes": [outcome for outcome, _ in sorted_results],
            "leader": sorted_results[0][0] if sorted_results else None,
        }

    def _calculate_positions(self, trades: list) -> Dict[str, Dict[str, float]]:
        """
        Calculate current positions from trade history.

        Args:
            trades: List of Trade objects

        Returns:
            Dictionary of user_id -> {outcome: shares}
        """
        positions = {}

        for trade in trades:
            if trade.user_id not in positions:
                positions[trade.user_id] = {}

            outcome = trade.outcome
            if outcome not in positions[trade.user_id]:
                positions[trade.user_id][outcome] = 0.0

            # Add shares for buy, subtract for sell
            if trade.trade_type.value == "buy":
                positions[trade.user_id][outcome] += trade.shares
            else:  # sell
                positions[trade.user_id][outcome] -= trade.shares

        return positions


# Singleton
_resolution_service: Optional[ResolutionService] = None


def get_resolution_service() -> ResolutionService:
    """Get the resolution service singleton."""
    global _resolution_service
    if _resolution_service is None:
        _resolution_service = ResolutionService()
    return _resolution_service

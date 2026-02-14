"""
NPC Service - Simulates player trading for demonstration
"""
import random
import asyncio
from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.market import Market, MarketStatus
from app.models.trade import Trade, TradeType
from app.services.lmsr import LMSR

# NPC Personas with different trading strategies
NPC_PERSONAS = [
    {
        "display_name": "Optimistic Oliver",
        "email": "oliver@npc.prophecy",
        "strategy": "bullish",  # Prefers YES bets
        "aggression": 0.7,  # High bet amounts
    },
    {
        "display_name": "Pessimistic Penny",
        "email": "penny@npc.prophecy",
        "strategy": "bearish",  # Prefers NO bets
        "aggression": 0.5,
    },
    {
        "display_name": "Cautious Charlie",
        "email": "charlie@npc.prophecy",
        "strategy": "neutral",  # Balanced
        "aggression": 0.3,  # Low bet amounts
    },
    {
        "display_name": "Random Rita",
        "email": "rita@npc.prophecy",
        "strategy": "random",  # Completely random
        "aggression": 0.6,
    },
    {
        "display_name": "Trendy Trevor",
        "email": "trevor@npc.prophecy",
        "strategy": "momentum",  # Follows market trends
        "aggression": 0.8,
    },
]


async def ensure_npcs_exist(db: AsyncSession) -> List[User]:
    """Create NPC users if they don't exist"""
    npcs = []

    for persona in NPC_PERSONAS:
        result = await db.execute(
            select(User).where(User.email == persona["email"])
        )
        npc = result.scalar_one_or_none()

        if not npc:
            npc = User(
                email=persona["email"],
                display_name=persona["display_name"],
                tokens=10000.0,  # NPCs start with more funds
            )
            db.add(npc)

        npcs.append(npc)

    await db.commit()
    for npc in npcs:
        await db.refresh(npc)

    return npcs


async def add_npcs_to_room(room_id: str, db: AsyncSession):
    """Ensure all NPCs exist (simplified - no membership system)"""
    await ensure_npcs_exist(db)


async def simulate_npc_trades(market: Market, db: AsyncSession):
    """
    Simulate NPC trading on a market
    Each NPC places 1-2 trades based on their strategy
    """
    if market.status != MarketStatus.OPEN:
        return

    npcs = await ensure_npcs_exist(db)
    lmsr = LMSR(liquidity=market.liquidity)

    for i, npc in enumerate(npcs):
        persona = NPC_PERSONAS[i]
        num_trades = random.randint(1, 2)

        for _ in range(num_trades):
            # Determine trade outcome based on strategy
            outcome = determine_trade_outcome(persona, market)

            # Determine share amount (5-50 based on aggression)
            shares = random.uniform(
                5.0,
                5.0 + 45.0 * persona["aggression"]
            )

            # Place trade
            try:
                # Calculate trade cost
                cost = lmsr.calculate_trade_cost(
                    market.shares,
                    outcome,
                    shares
                )

                # Check NPC has enough tokens
                if npc.tokens < cost:
                    continue

                # Execute trade via LMSR
                new_shares, actual_cost, new_prices = lmsr.execute_trade(
                    market.shares,
                    outcome,
                    shares
                )

                # Create trade record
                trade = Trade(
                    user_id=npc.id,
                    market_id=market.id,
                    trade_type=TradeType.BUY,
                    outcome=outcome,
                    shares=shares,
                    price=new_prices[outcome],
                    cost=actual_cost,
                    previous_shares=0.0,
                )
                db.add(trade)

                # Update market state
                market.shares = new_shares
                market.prices = new_prices
                market.total_volume += abs(actual_cost)
                market.updated_at = datetime.utcnow()

                # Update NPC tokens
                npc.tokens -= actual_cost
                npc.total_trades += 1

                # Small delay between trades
                await asyncio.sleep(0.05)

            except Exception as e:
                print(f"NPC trade failed for {npc.display_name}: {e}")
                continue

    await db.commit()


def determine_trade_outcome(persona: dict, market: Market) -> str:
    """Determine which outcome NPC should bet on based on strategy"""
    strategy = persona["strategy"]
    outcomes = list(market.shares.keys())

    # For binary markets
    if "yes" in outcomes and "no" in outcomes:
        if strategy == "bullish":
            return "yes" if random.random() < 0.8 else "no"
        elif strategy == "bearish":
            return "no" if random.random() < 0.8 else "yes"
        elif strategy == "neutral":
            return random.choice(["yes", "no"])
        elif strategy == "random":
            return random.choice(["yes", "no"])
        elif strategy == "momentum":
            # Follow the current trend
            yes_price = market.prices.get("yes", 0.5)
            if yes_price > 0.55:
                return "yes" if random.random() < 0.7 else "no"
            elif yes_price < 0.45:
                return "no" if random.random() < 0.7 else "yes"
            else:
                return random.choice(["yes", "no"])

    # For multiple choice markets, just pick random
    return random.choice(outcomes)

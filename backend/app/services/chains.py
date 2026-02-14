"""
Chain trading and derivatives logic
Allows users to create synthetic positions across markets
"""
from typing import List, Dict, Tuple
from app.services.lmsr import LMSR


class ChainService:
    """
    Service for chain trading - creating synthetic positions across multiple markets.

    Example: If you think YES on Market A implies YES on Market B,
    you can create a chain trade that profits if both resolve YES.
    """

    def calculate_chain_value(
        self,
        markets: List[Dict],
        positions: List[Dict],
        outcomes: List[str]
    ) -> float:
        """
        Calculate the value of a chain position given specific outcomes.

        Args:
            markets: List of market data dictionaries
            positions: List of position dictionaries (shares in each market)
            outcomes: List of outcomes (one per market)

        Returns:
            Total payout value
        """
        if len(markets) != len(positions) or len(markets) != len(outcomes):
            raise ValueError("Markets, positions, and outcomes must have same length")

        total_value = 0.0

        for market, position, outcome in zip(markets, positions, outcomes):
            # Get shares for this outcome
            shares = position.get(outcome, 0.0)
            # Each winning share pays 1 token
            total_value += shares

        return total_value

    def calculate_chain_cost(
        self,
        markets: List[Dict],
        shares_to_buy: List[Dict]
    ) -> float:
        """
        Calculate the total cost to establish a chain position.

        Args:
            markets: List of market data (with current shares and liquidity)
            shares_to_buy: List of {outcome: shares} dicts for each market

        Returns:
            Total cost across all markets
        """
        total_cost = 0.0

        for market, shares_dict in zip(markets, shares_to_buy):
            lmsr = LMSR(liquidity=market["liquidity"])

            for outcome, shares in shares_dict.items():
                cost = lmsr.calculate_trade_cost(
                    market["shares"],
                    outcome,
                    shares
                )
                total_cost += cost

        return total_cost

    def suggest_hedge(
        self,
        position: Dict[str, float],
        current_prices: Dict[str, float],
        liquidity: float
    ) -> Dict:
        """
        Suggest a hedge trade to reduce risk.

        Args:
            position: Current position {outcome: shares}
            current_prices: Current market prices
            liquidity: Market liquidity parameter

        Returns:
            Dictionary with hedge recommendation
        """
        # Calculate current exposure
        exposures = {}
        total_exposure = 0.0

        for outcome, shares in position.items():
            price = current_prices.get(outcome, 0.5)
            exposure = shares * (1.0 - price)  # Risk if outcome doesn't win
            exposures[outcome] = exposure
            total_exposure += abs(exposure)

        # Find outcome with most exposure
        max_exposure_outcome = max(exposures.items(), key=lambda x: abs(x[1]))
        outcome, exposure = max_exposure_outcome

        # Suggest buying the opposite
        if exposure > 0:
            # Exposed to this outcome losing, buy shares to hedge
            hedge_shares = exposure / current_prices.get(outcome, 0.5)
            recommendation = {
                "action": "buy",
                "outcome": outcome,
                "shares": hedge_shares,
                "reasoning": f"Reduce exposure by buying {outcome}"
            }
        else:
            # Overexposed to this outcome, sell some
            recommendation = {
                "action": "sell",
                "outcome": outcome,
                "shares": abs(exposure),
                "reasoning": f"Reduce exposure by selling {outcome}"
            }

        return recommendation


class DerivativeService:
    """
    Service for creating derivative positions.

    Derivatives allow betting on relationships between markets:
    - Spreads: Difference between two market prices
    - Correlations: Both markets resolve the same way
    - Conditionals: Market A resolves X given Market B resolves Y
    """

    def calculate_spread_value(
        self,
        market_a_price: float,
        market_b_price: float,
        spread_position: str  # "long" or "short"
    ) -> float:
        """
        Calculate value of a spread position.

        Long spread: Profit if A > B (price_a - price_b increases)
        Short spread: Profit if B > A (price_a - price_b decreases)

        Args:
            market_a_price: Current price in market A
            market_b_price: Current price in market B
            spread_position: "long" or "short"

        Returns:
            Current spread value
        """
        spread = market_a_price - market_b_price

        if spread_position == "long":
            return spread
        else:  # short
            return -spread

    def create_correlation_position(
        self,
        market_a: Dict,
        market_b: Dict,
        correlation_type: str  # "positive" or "negative"
    ) -> Dict:
        """
        Create a position that profits from correlation.

        Positive correlation: Both YES or both NO
        Negative correlation: One YES, one NO

        Args:
            market_a: Market A data
            market_b: Market B data
            correlation_type: "positive" or "negative"

        Returns:
            Dictionary with recommended trades
        """
        if correlation_type == "positive":
            # Profit if both YES or both NO
            # Strategy: Buy YES in both, or buy NO in both
            yes_a = market_a["prices"].get("yes", 0.5)
            yes_b = market_b["prices"].get("yes", 0.5)

            if yes_a + yes_b < 1.0:
                # Both YES is underpriced
                return {
                    "strategy": "both_yes",
                    "trades": [
                        {"market": "a", "outcome": "yes", "shares": 10},
                        {"market": "b", "outcome": "yes", "shares": 10},
                    ],
                    "reasoning": "Both YES outcomes are underpriced for positive correlation"
                }
            else:
                # Both NO is underpriced
                return {
                    "strategy": "both_no",
                    "trades": [
                        {"market": "a", "outcome": "no", "shares": 10},
                        {"market": "b", "outcome": "no", "shares": 10},
                    ],
                    "reasoning": "Both NO outcomes are underpriced for positive correlation"
                }
        else:  # negative correlation
            # Profit if one YES, one NO
            return {
                "strategy": "opposite",
                "trades": [
                    {"market": "a", "outcome": "yes", "shares": 10},
                    {"market": "b", "outcome": "no", "shares": 10},
                ],
                "reasoning": "Markets should move in opposite directions"
            }


# Singleton instances
_chain_service = None
_derivative_service = None


def get_chain_service() -> ChainService:
    """Get chain service singleton."""
    global _chain_service
    if _chain_service is None:
        _chain_service = ChainService()
    return _chain_service


def get_derivative_service() -> DerivativeService:
    """Get derivative service singleton."""
    global _derivative_service
    if _derivative_service is None:
        _derivative_service = DerivativeService()
    return _derivative_service

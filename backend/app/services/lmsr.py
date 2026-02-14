"""
LMSR (Logarithmic Market Scoring Rule) implementation
Provides automated market making with constant liquidity
"""
import math
from typing import Dict, Tuple


class LMSR:
    """
    Logarithmic Market Scoring Rule market maker.

    The LMSR provides automated liquidity and price discovery.
    Prices are calculated based on the cost function:
    C(q) = b * log(sum(e^(q_i/b)))

    Where:
    - b is the liquidity parameter (higher = less price movement)
    - q_i is the quantity of shares outstanding for outcome i
    """

    def __init__(self, liquidity: float = 100.0):
        """
        Initialize LMSR market maker.

        Args:
            liquidity: The b parameter, controls liquidity depth
                      Higher values = less price impact per trade
        """
        self.liquidity = liquidity

    def calculate_cost(self, shares: Dict[str, float]) -> float:
        """
        Calculate the cost function C(q) for current share distribution.

        Args:
            shares: Dictionary of outcome -> quantity
                   e.g., {"yes": 50, "no": 50}

        Returns:
            The cost function value
        """
        if not shares:
            return 0.0

        # C(q) = b * log(sum(e^(q_i/b)))
        exp_sum = sum(math.exp(q / self.liquidity) for q in shares.values())
        return self.liquidity * math.log(exp_sum)

    def calculate_prices(self, shares: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate current market prices for all outcomes.

        Price is the derivative of the cost function:
        p_i = e^(q_i/b) / sum(e^(q_j/b))

        Args:
            shares: Current share distribution

        Returns:
            Dictionary of outcome -> price (0 to 1)
        """
        if not shares:
            return {}

        # Calculate denominator: sum(e^(q_j/b))
        exp_values = {
            outcome: math.exp(q / self.liquidity)
            for outcome, q in shares.items()
        }
        exp_sum = sum(exp_values.values())

        # Calculate prices: p_i = e^(q_i/b) / sum
        prices = {
            outcome: exp_val / exp_sum
            for outcome, exp_val in exp_values.items()
        }

        return prices

    def calculate_trade_cost(
        self,
        current_shares: Dict[str, float],
        outcome: str,
        quantity: float
    ) -> float:
        """
        Calculate the cost of buying `quantity` shares of `outcome`.

        Cost = C(q + delta) - C(q)
        Where delta is the change vector (quantity for outcome, 0 for others)

        Args:
            current_shares: Current share distribution
            outcome: Which outcome to buy
            quantity: Number of shares to buy (positive) or sell (negative)

        Returns:
            Cost in tokens (positive = pay, negative = receive)
        """
        # Calculate cost before trade
        cost_before = self.calculate_cost(current_shares)

        # Calculate shares after trade
        new_shares = current_shares.copy()
        new_shares[outcome] = new_shares.get(outcome, 0) + quantity

        # Calculate cost after trade
        cost_after = self.calculate_cost(new_shares)

        # Trade cost is the difference
        return cost_after - cost_before

    def execute_trade(
        self,
        current_shares: Dict[str, float],
        outcome: str,
        quantity: float
    ) -> Tuple[Dict[str, float], float, Dict[str, float]]:
        """
        Execute a trade and return updated state.

        Args:
            current_shares: Current share distribution
            outcome: Which outcome to trade
            quantity: Number of shares (positive = buy, negative = sell)

        Returns:
            Tuple of:
            - Updated shares dictionary
            - Cost of the trade
            - Updated prices dictionary
        """
        # Calculate cost
        cost = self.calculate_trade_cost(current_shares, outcome, quantity)

        # Update shares
        new_shares = current_shares.copy()
        new_shares[outcome] = new_shares.get(outcome, 0) + quantity

        # Calculate new prices
        new_prices = self.calculate_prices(new_shares)

        return new_shares, cost, new_prices

    def initialize_market(self, outcomes: list[str], initial_shares: float = 0.0) -> Dict[str, float]:
        """
        Initialize a market with equal starting shares for all outcomes.

        Args:
            outcomes: List of outcome names (e.g., ["yes", "no"])
            initial_shares: Starting quantity for each outcome

        Returns:
            Initial shares dictionary
        """
        return {outcome: initial_shares for outcome in outcomes}


# Convenience functions

def get_binary_market_prices(yes_shares: float, no_shares: float, liquidity: float = 100.0) -> Tuple[float, float]:
    """
    Quick function to get prices for a binary market.

    Args:
        yes_shares: Quantity of YES shares
        no_shares: Quantity of NO shares
        liquidity: LMSR liquidity parameter

    Returns:
        Tuple of (yes_price, no_price)
    """
    lmsr = LMSR(liquidity)
    prices = lmsr.calculate_prices({"yes": yes_shares, "no": no_shares})
    return prices["yes"], prices["no"]


def calculate_buy_cost(
    shares: Dict[str, float],
    outcome: str,
    quantity: float,
    liquidity: float = 100.0
) -> float:
    """
    Calculate cost to buy shares.

    Args:
        shares: Current share distribution
        outcome: Which outcome to buy
        quantity: How many shares to buy
        liquidity: LMSR liquidity parameter

    Returns:
        Cost in tokens
    """
    lmsr = LMSR(liquidity)
    return lmsr.calculate_trade_cost(shares, outcome, quantity)

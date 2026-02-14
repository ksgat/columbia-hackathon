"""
LMSR (Logarithmic Market Scoring Rule) Market Maker

This is the automated market maker that provides infinite liquidity
and deterministic pricing for prediction markets.

Based on the same algorithm used by Polymarket and prediction market research.
"""
import math
from typing import Tuple

class LMSRMarketMaker:
    """
    Logarithmic Market Scoring Rule market maker.

    The LMSR provides:
    - Infinite liquidity (users can always trade)
    - Deterministic pricing based on share quantities
    - Automatic market making without human liquidity providers

    Parameters:
    - b: liquidity parameter (higher = more liquidity = less price impact)
    - yes_shares: total YES shares outstanding
    - no_shares: total NO shares outstanding
    """

    def __init__(self, b: float = 100.0, yes_shares: float = 0.0, no_shares: float = 0.0):
        """
        Initialize LMSR market maker.

        Args:
            b: Liquidity parameter. For small rooms (5-20 people), b=100 works well.
               For larger rooms, scale up proportionally.
            yes_shares: Initial YES shares outstanding
            no_shares: Initial NO shares outstanding
        """
        if b <= 0:
            raise ValueError("Liquidity parameter b must be positive")

        self.b = b
        self.yes_shares = yes_shares
        self.no_shares = no_shares

    def cost(self, yes_shares: float, no_shares: float) -> float:
        """
        Total cost function C(q_yes, q_no).

        This is the core LMSR formula:
        C(q) = b * ln(e^(q_yes/b) + e^(q_no/b))

        Args:
            yes_shares: Total YES shares
            no_shares: Total NO shares

        Returns:
            Total cost in coins
        """
        try:
            exp_yes = math.exp(yes_shares / self.b)
            exp_no = math.exp(no_shares / self.b)
            return self.b * math.log(exp_yes + exp_no)
        except (OverflowError, ValueError) as e:
            # Handle extreme values
            raise ValueError(f"LMSR calculation overflow: {e}")

    def current_price_yes(self) -> float:
        """
        Current price (probability) of YES shares.

        Price is the derivative of the cost function:
        p_yes = e^(q_yes/b) / (e^(q_yes/b) + e^(q_no/b))

        Returns:
            Price of YES (probability between 0.0 and 1.0)
        """
        try:
            exp_yes = math.exp(self.yes_shares / self.b)
            exp_no = math.exp(self.no_shares / self.b)
            return exp_yes / (exp_yes + exp_no)
        except (OverflowError, ValueError):
            # If overflow, return extreme value
            if self.yes_shares > self.no_shares:
                return 0.999
            else:
                return 0.001

    def current_price_no(self) -> float:
        """
        Current price (probability) of NO shares.

        Returns:
            Price of NO (probability between 0.0 and 1.0)
        """
        return 1.0 - self.current_price_yes()

    def cost_to_buy(self, side: str, num_shares: float) -> float:
        """
        Calculate the cost to buy a specific number of shares.

        Cost = C(q_new) - C(q_old)

        Args:
            side: 'yes' or 'no'
            num_shares: Number of shares to buy

        Returns:
            Amount of coins/USD the user must pay
        """
        if num_shares <= 0:
            raise ValueError("Number of shares must be positive")

        old_cost = self.cost(self.yes_shares, self.no_shares)

        if side == 'yes':
            new_cost = self.cost(self.yes_shares + num_shares, self.no_shares)
        elif side == 'no':
            new_cost = self.cost(self.yes_shares, self.no_shares + num_shares)
        else:
            raise ValueError("Side must be 'yes' or 'no'")

        return new_cost - old_cost

    def shares_for_amount(self, side: str, amount: float, max_iterations: int = 100) -> float:
        """
        Calculate how many shares can be bought with a given amount of coins.

        Uses binary search to find the number of shares where:
        cost_to_buy(shares) ≈ amount

        Args:
            side: 'yes' or 'no'
            amount: Amount of coins to spend
            max_iterations: Maximum binary search iterations

        Returns:
            Number of shares that can be purchased
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Binary search bounds
        low = 0.0
        high = amount * 10  # Upper bound estimate

        # Binary search for shares
        for _ in range(max_iterations):
            mid = (low + high) / 2
            cost = self.cost_to_buy(side, mid)

            if abs(cost - amount) < 0.001:  # Close enough
                return mid

            if cost < amount:
                low = mid
            else:
                high = mid

        # Return best approximation
        return (low + high) / 2

    def execute_trade(self, side: str, amount: float) -> Tuple[float, float, float]:
        """
        Execute a trade: spend amount, receive shares, update state.

        Args:
            side: 'yes' or 'no'
            amount: Amount of coins/USD to spend

        Returns:
            Tuple of (shares_received, new_odds_yes, new_odds_no)
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Calculate shares received
        shares = self.shares_for_amount(side, amount)

        # Update state
        if side == 'yes':
            self.yes_shares += shares
        elif side == 'no':
            self.no_shares += shares
        else:
            raise ValueError("Side must be 'yes' or 'no'")

        # Get new odds
        new_odds_yes = self.current_price_yes()
        new_odds_no = self.current_price_no()

        return shares, new_odds_yes, new_odds_no

    def payout_per_share(self) -> float:
        """
        Each winning share pays out 1.0 coin/dollar.
        Losing shares pay out 0.0.

        Returns:
            Payout per winning share (always 1.0)
        """
        return 1.0

    def calculate_payout(self, shares: float, winning_side: str, user_side: str) -> float:
        """
        Calculate payout for a user's position.

        Args:
            shares: Number of shares held
            winning_side: The side that won ('yes' or 'no')
            user_side: The side the user bet on

        Returns:
            Payout amount in coins
        """
        if user_side == winning_side:
            return shares * self.payout_per_share()
        else:
            return 0.0

    def get_state(self) -> dict:
        """
        Get current market maker state.

        Returns:
            Dictionary with current state
        """
        return {
            "b": self.b,
            "yes_shares": self.yes_shares,
            "no_shares": self.no_shares,
            "odds_yes": self.current_price_yes(),
            "odds_no": self.current_price_no()
        }


def test_lmsr():
    """Quick test to verify LMSR math is correct"""
    print("Testing LMSR Market Maker...")

    # Test 1: Initial state should be 50/50
    mm = LMSRMarketMaker(b=100, yes_shares=0, no_shares=0)
    assert abs(mm.current_price_yes() - 0.5) < 0.001, "Initial odds should be 50/50"
    print("✓ Test 1: Initial odds = 50/50")

    # Test 2: Buying YES should increase YES odds
    initial_odds = mm.current_price_yes()
    shares, new_odds_yes, new_odds_no = mm.execute_trade('yes', 50)
    assert new_odds_yes > initial_odds, "Buying YES should increase YES odds"
    assert abs(new_odds_yes + new_odds_no - 1.0) < 0.001, "Odds should sum to 1"
    print(f"✓ Test 2: After buying YES, odds: {new_odds_yes:.2%} YES / {new_odds_no:.2%} NO")

    # Test 3: Buying NO should decrease YES odds
    mm2 = LMSRMarketMaker(b=100, yes_shares=0, no_shares=0)
    shares, new_odds_yes, new_odds_no = mm2.execute_trade('no', 50)
    assert new_odds_yes < 0.5, "Buying NO should decrease YES odds"
    print(f"✓ Test 3: After buying NO, odds: {new_odds_yes:.2%} YES / {new_odds_no:.2%} NO")

    # Test 4: Payout calculation
    payout = mm.calculate_payout(10, 'yes', 'yes')
    assert payout == 10.0, "Winning shares should pay 1:1"
    payout = mm.calculate_payout(10, 'yes', 'no')
    assert payout == 0.0, "Losing shares should pay nothing"
    print("✓ Test 4: Payout calculation correct")

    print("\n✅ All LMSR tests passed!")


if __name__ == "__main__":
    test_lmsr()

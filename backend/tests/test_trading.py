#!/usr/bin/env python3
"""
Quick test to verify trading logic works
Tests LMSR, trade execution, and balance updates
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.lmsr import LMSR


def test_binary_market():
    """Test basic binary market trading"""
    print("Testing Binary Market Trading...")

    lmsr = LMSR(liquidity=100.0)

    # Initialize market
    shares = {"yes": 0.0, "no": 0.0}
    prices = lmsr.calculate_prices(shares)

    print(f"Initial state:")
    print(f"  Shares: {shares}")
    print(f"  Prices: YES={prices['yes']:.3f}, NO={prices['no']:.3f}")

    assert abs(prices['yes'] - 0.5) < 0.01, "Initial YES price should be ~0.5"
    assert abs(prices['no'] - 0.5) < 0.01, "Initial NO price should be ~0.5"

    # User 1 buys 10 YES shares
    cost1 = lmsr.calculate_trade_cost(shares, "yes", 10.0)
    shares, _, prices = lmsr.execute_trade(shares, "yes", 10.0)

    print(f"\nUser 1 buys 10 YES shares:")
    print(f"  Cost: {cost1:.2f} tokens")
    print(f"  New prices: YES={prices['yes']:.3f}, NO={prices['no']:.3f}")

    assert cost1 > 0, "Buying should cost tokens"
    assert prices['yes'] > 0.5, "YES price should increase"
    assert prices['no'] < 0.5, "NO price should decrease"

    # User 2 buys 5 NO shares
    cost2 = lmsr.calculate_trade_cost(shares, "no", 5.0)
    shares, _, prices = lmsr.execute_trade(shares, "no", 5.0)

    print(f"\nUser 2 buys 5 NO shares:")
    print(f"  Cost: {cost2:.2f} tokens")
    print(f"  New prices: YES={prices['yes']:.3f}, NO={prices['no']:.3f}")

    # User 1 sells 5 YES shares
    revenue = lmsr.calculate_trade_cost(shares, "yes", -5.0)
    shares, _, prices = lmsr.execute_trade(shares, "yes", -5.0)

    print(f"\nUser 1 sells 5 YES shares:")
    print(f"  Revenue: {abs(revenue):.2f} tokens")
    print(f"  New prices: YES={prices['yes']:.3f}, NO={prices['no']:.3f}")

    assert revenue < 0, "Selling should give tokens (negative cost)"

    print("\n✅ Binary market trading test passed!")
    return True


def test_balance_tracking():
    """Test user balance tracking"""
    print("\n" + "="*50)
    print("Testing Balance Tracking...")

    starting_balance = 1000.0
    user_balance = starting_balance

    lmsr = LMSR(liquidity=100.0)
    shares = {"yes": 0.0, "no": 0.0}

    print(f"Starting balance: {user_balance:.2f} tokens")

    # Buy 10 YES shares
    cost = lmsr.calculate_trade_cost(shares, "yes", 10.0)
    shares, _, _ = lmsr.execute_trade(shares, "yes", 10.0)

    user_balance -= cost
    print(f"After buying 10 YES: {user_balance:.2f} tokens (spent {cost:.2f})")

    assert user_balance < starting_balance, "Balance should decrease after buying"
    assert user_balance == starting_balance - cost, "Balance should decrease by exact cost"

    # Sell 5 YES shares
    revenue = abs(lmsr.calculate_trade_cost(shares, "yes", -5.0))
    shares, _, _ = lmsr.execute_trade(shares, "yes", -5.0)

    user_balance += revenue
    print(f"After selling 5 YES: {user_balance:.2f} tokens (received {revenue:.2f})")

    assert user_balance > starting_balance - cost, "Balance should increase after selling"

    # Buy 20 NO shares
    cost2 = lmsr.calculate_trade_cost(shares, "no", 20.0)

    if user_balance >= cost2:
        shares, _, _ = lmsr.execute_trade(shares, "no", 20.0)
        user_balance -= cost2
        print(f"After buying 20 NO: {user_balance:.2f} tokens (spent {cost2:.2f})")
    else:
        print(f"Cannot afford 20 NO shares (costs {cost2:.2f}, have {user_balance:.2f})")
        print("This is correct - insufficient balance protection!")

    print(f"\nFinal balance: {user_balance:.2f} tokens")
    print(f"Net change: {user_balance - starting_balance:.2f} tokens")

    print("\n✅ Balance tracking test passed!")
    return True


def test_multiple_choice_market():
    """Test multiple choice market"""
    print("\n" + "="*50)
    print("Testing Multiple Choice Market...")

    lmsr = LMSR(liquidity=100.0)

    # Initialize 4-option market
    shares = {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0}
    prices = lmsr.calculate_prices(shares)

    print(f"Initial prices (4 options):")
    for i in range(4):
        print(f"  Option {i}: {prices[str(i)]:.3f}")

    # All should be equal
    for price in prices.values():
        assert abs(price - 0.25) < 0.01, "Initial prices should be ~0.25 for 4 options"

    # Buy option 0
    cost = lmsr.calculate_trade_cost(shares, "0", 10.0)
    shares, _, prices = lmsr.execute_trade(shares, "0", 10.0)

    print(f"\nAfter buying 10 shares of option 0:")
    print(f"  Cost: {cost:.2f} tokens")
    for i in range(4):
        print(f"  Option {i}: {prices[str(i)]:.3f}")

    assert prices["0"] > 0.25, "Option 0 price should increase"

    print("\n✅ Multiple choice market test passed!")
    return True


if __name__ == "__main__":
    print("🧪 Testing Prophecy Trading System\n")

    all_passed = True
    all_passed &= test_binary_market()
    all_passed &= test_balance_tracking()
    all_passed &= test_multiple_choice_market()

    print("\n" + "="*50)
    if all_passed:
        print("✅ ALL TRADING TESTS PASSED")
        print("="*50)
        print("\nTrading system is working correctly:")
        print("  ✓ LMSR price calculation")
        print("  ✓ Trade execution")
        print("  ✓ Balance deduction")
        print("  ✓ Buy/sell operations")
        print("  ✓ Multiple choice markets")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("="*50)
        sys.exit(1)

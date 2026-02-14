"""
Clout Score System (ELO-based ranking)

Users gain/lose clout based on prediction accuracy.
Better predictions against the odds earn more clout.
"""

# ELO K-factor (how much each market moves your score)
K_FACTOR = 32

# Rank thresholds
RANK_LABELS = [
    (0, "Bronze"),
    (800, "Silver"),
    (1000, "Gold"),
    (1200, "Platinum"),
    (1400, "Diamond"),
    (1600, "Prophet's Rival"),
]

def get_rank_label(clout_score: float) -> str:
    """
    Get rank label based on clout score.

    Args:
        clout_score: User's current clout score

    Returns:
        Rank label string
    """
    for threshold, label in reversed(RANK_LABELS):
        if clout_score >= threshold:
            return label
    return "Bronze"

def calculate_clout_change(
    user_won: bool,
    odds_at_trade: float,
    user_side: str
) -> float:
    """
    Calculate clout score change for a user based on ELO formula.

    The ELO system rewards:
    - Correct predictions against the odds (bigger gains)
    - Punishes incorrect predictions with the odds (bigger losses)

    Formula:
    - Expected score = probability that user's side would win (based on odds)
    - Actual score = 1.0 if won, 0.0 if lost
    - Change = K * (actual - expected)

    Args:
        user_won: True if user's position won
        odds_at_trade: Odds of YES when user placed trade
        user_side: 'yes' or 'no'

    Returns:
        Clout score change (positive or negative)

    Examples:
        - Bet YES at 30% odds and win: +22.4 clout (big gain for underdog bet)
        - Bet YES at 70% odds and win: +9.6 clout (small gain for favorite)
        - Bet YES at 70% odds and lose: -22.4 clout (big loss for losing favorite)
    """
    # Calculate expected score (probability user's side would win)
    if user_side == 'yes':
        expected = odds_at_trade
    else:
        expected = 1.0 - odds_at_trade

    # Actual score
    actual = 1.0 if user_won else 0.0

    # ELO change
    change = K_FACTOR * (actual - expected)

    return change

def update_user_clout(user, clout_change: float) -> None:
    """
    Update user's clout score and rank.

    Args:
        user: User model instance
        clout_change: Amount to change clout by
    """
    # Update score
    user.clout_score += clout_change

    # Clamp to minimum 0
    user.clout_score = max(0, user.clout_score)

    # Update rank label
    user.clout_rank = get_rank_label(user.clout_score)

def update_user_streak(user, won: bool) -> None:
    """
    Update user's win streak.

    Args:
        user: User model instance
        won: True if user won this market
    """
    if won:
        user.streak_current += 1
        user.streak_best = max(user.streak_best, user.streak_current)
    else:
        user.streak_current = 0


# Example calculations for documentation
if __name__ == "__main__":
    print("Clout Score Calculation Examples:\n")

    scenarios = [
        ("Underdog bet wins", True, 0.3, "yes"),
        ("Favorite bet wins", True, 0.7, "yes"),
        ("Favorite bet loses", False, 0.7, "yes"),
        ("Underdog bet loses", False, 0.3, "yes"),
        ("Bet NO at 30% YES wins", True, 0.3, "no"),
    ]

    for desc, won, odds, side in scenarios:
        change = calculate_clout_change(won, odds, side)
        print(f"{desc:30} → {change:+.1f} clout")

    print("\nRank Thresholds:")
    for threshold, label in RANK_LABELS:
        print(f"  {threshold:4} - {label}")

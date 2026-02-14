"""
Live test of Prophet AI with OpenRouter API
Tests real API calls to verify integration
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_config():
    """Test configuration is loaded correctly"""
    from app.config import settings

    print("🔧 Configuration Check:")
    print(f"   OpenRouter Model: {settings.openrouter_model}")
    print(f"   API Key Present: {'✅' if settings.openrouter_api_key else '❌'}")
    print(f"   API Key: {settings.openrouter_api_key[:20]}..." if settings.openrouter_api_key else "   API Key: Not set")
    print()

    if not settings.openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not found in environment!")
        return False

    if settings.openrouter_model != "anthropic/claude-opus-4.6":
        print(f"⚠️  Model is {settings.openrouter_model}, expected anthropic/claude-opus-4.6")
        return False

    return True

def test_market_generation():
    """Test Prophet's market generation with real API"""
    from app.services.prophet import generate_markets

    print("🎲 Testing Market Generation:")
    print("   Calling Prophet AI to generate markets...")

    try:
        markets = generate_markets(
            room_name="Columbia Hackathon Room",
            member_names=["Alice", "Bob", "Charlie"],
            recent_markets=["Will it snow tomorrow?"]
        )

        print(f"   ✅ Generated {len(markets)} markets")
        for i, market in enumerate(markets, 1):
            print(f"\n   Market {i}:")
            print(f"      Title: {market.get('title', 'N/A')}")
            print(f"      Category: {market.get('category', 'N/A')}")
            print(f"      Initial Odds: {market.get('initial_odds_yes', 0.5):.0%}")
            if market.get('description'):
                print(f"      Description: {market.get('description')[:80]}...")

        return True
    except Exception as e:
        print(f"   ❌ Market generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trade_commentary():
    """Test Prophet's trade commentary"""
    from app.services.prophet import generate_trade_commentary

    print("\n💬 Testing Trade Commentary:")
    print("   Asking Prophet to comment on a trade...")

    try:
        commentary = generate_trade_commentary(
            market_title="Will GPT-5 be released in 2026?",
            user_name="Alice",
            side="yes",
            amount=100,
            new_odds_yes=0.65
        )

        print(f"   ✅ Prophet says: \"{commentary}\"")
        return True
    except Exception as e:
        print(f"   ❌ Commentary generation failed: {e}")
        return False

def test_dispute_resolution():
    """Test Prophet's dispute resolution"""
    from app.services.prophet import resolve_dispute

    print("\n⚖️  Testing Dispute Resolution:")
    print("   Asking Prophet to resolve a disputed market...")

    try:
        ruling = resolve_dispute(
            market_title="Will it rain on Saturday?",
            description="Resolves YES if any rain falls in NYC on Saturday",
            yes_votes=6,
            no_votes=4
        )

        print(f"   ✅ Prophet's ruling: {ruling['ruling'].upper()}")
        print(f"   Confidence: {ruling.get('confidence', 0.5):.0%}")
        print(f"   Reasoning: \"{ruling.get('reasoning', 'N/A')}\"")
        return True
    except Exception as e:
        print(f"   ❌ Dispute resolution failed: {e}")
        return False

def test_bet_decision():
    """Test Prophet's betting decision"""
    from app.services.prophet import decide_prophet_bet

    print("\n🎰 Testing Prophet's Bet Decision:")
    print("   Asking Prophet if it wants to bet...")

    try:
        decision = decide_prophet_bet(
            market_title="Will Bitcoin reach $100k in 2026?",
            description="Resolves YES if BTC hits $100,000 at any point in 2026",
            initial_odds=0.5
        )

        if decision.get('should_bet'):
            print(f"   ✅ Prophet wants to bet {decision.get('side', 'N/A').upper()}")
            print(f"   Amount: {decision.get('amount', 0)} coins")
            print(f"   Confidence: {decision.get('confidence', 0.5):.0%}")
            print(f"   Reasoning: \"{decision.get('reasoning', 'N/A')}\"")
        else:
            print(f"   🤔 Prophet decided not to bet")
            print(f"   Reasoning: \"{decision.get('reasoning', 'N/A')}\"")

        return True
    except Exception as e:
        print(f"   ❌ Bet decision failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🔮 PROPHET AI LIVE TEST")
    print("="*60 + "\n")

    all_passed = True

    # Test 1: Configuration
    if not test_config():
        print("\n❌ Configuration test failed. Cannot proceed.")
        return

    # Test 2: Market Generation
    all_passed &= test_market_generation()

    # Test 3: Trade Commentary
    all_passed &= test_trade_commentary()

    # Test 4: Dispute Resolution
    all_passed &= test_dispute_resolution()

    # Test 5: Bet Decision
    all_passed &= test_bet_decision()

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL PROPHET AI TESTS PASSED")
        print("="*60)
        print("\n🎉 Prophet is online and ready to serve!")
        print(f"   Model: anthropic/claude-opus-4.6")
        print(f"   All AI capabilities verified and working")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("="*60)
        print("\nCheck the errors above for details.")
    print()

if __name__ == "__main__":
    main()

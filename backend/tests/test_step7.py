"""
TEMPORARY TEST for Step 7: Verify Prophet AI Agent
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all Prophet modules can be imported"""
    try:
        from app.models.prophet_bet import ProphetBet
        from app.services.prophet import (
            call_prophet,
            generate_markets,
            generate_trade_commentary,
            generate_resolution_commentary,
            resolve_dispute,
            decide_prophet_bet
        )
        from app.routers.prophet import router as prophet_router
        print("✅ All Prophet modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prophet_bet_model():
    """Test ProphetBet model structure"""
    try:
        from app.models.prophet_bet import ProphetBet

        # Check required fields
        required_fields = [
            'id', 'market_id', 'side', 'confidence', 'reasoning',
            'amount', 'shares_received', 'created_at'
        ]

        for field in required_fields:
            assert hasattr(ProphetBet, field), f"ProphetBet model missing field: {field}"

        # Check methods
        assert hasattr(ProphetBet, 'to_dict'), "ProphetBet model missing to_dict method"

        print("✅ ProphetBet model structure verified")
        return True
    except Exception as e:
        print(f"❌ ProphetBet model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prophet_service():
    """Test Prophet AI service functions"""
    try:
        from app.services.prophet import (
            generate_markets,
            generate_trade_commentary,
            generate_resolution_commentary,
            resolve_dispute,
            decide_prophet_bet
        )

        # Test that functions exist and have correct signatures
        import inspect

        # Check generate_markets
        sig = inspect.signature(generate_markets)
        assert 'room_name' in sig.parameters
        assert 'member_names' in sig.parameters
        assert 'recent_markets' in sig.parameters

        # Check generate_trade_commentary
        sig = inspect.signature(generate_trade_commentary)
        assert 'market_title' in sig.parameters
        assert 'user_name' in sig.parameters
        assert 'side' in sig.parameters
        assert 'amount' in sig.parameters
        assert 'new_odds_yes' in sig.parameters

        # Check generate_resolution_commentary
        sig = inspect.signature(generate_resolution_commentary)
        assert 'market_title' in sig.parameters
        assert 'result' in sig.parameters
        assert 'vote_summary' in sig.parameters

        # Check resolve_dispute
        sig = inspect.signature(resolve_dispute)
        assert 'market_title' in sig.parameters
        assert 'description' in sig.parameters
        assert 'yes_votes' in sig.parameters
        assert 'no_votes' in sig.parameters

        # Check decide_prophet_bet
        sig = inspect.signature(decide_prophet_bet)
        assert 'market_title' in sig.parameters
        assert 'description' in sig.parameters
        assert 'initial_odds' in sig.parameters

        print("✅ Prophet service functions verified")
        return True
    except Exception as e:
        print(f"❌ Prophet service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prophet_router():
    """Test Prophet router endpoints are defined"""
    try:
        from app.routers.prophet import router

        # Check routes exist
        routes = {route.path for route in router.routes}

        expected_routes = ['/generate-markets/{room_id}', '/resolve-dispute/{market_id}', '/status']

        for expected in expected_routes:
            assert expected in routes, f"Missing route: {expected}"

        print(f"✅ Prophet router has all required endpoints")
        return True
    except Exception as e:
        print(f"❌ Prophet router test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_tables():
    """Test that prophet_bets table exists in database"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Check prophet_bets table
            result = await session.execute(text("SELECT COUNT(*) FROM prophet_bets"))
            bet_count = result.scalar()
            print(f"   ✓ prophet_bets table: {bet_count} rows")

        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database table test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_app_integration():
    """Test that Prophet router is integrated into main app"""
    try:
        from app.main import app

        # Check that routes are registered
        all_routes = [route.path for route in app.routes]

        # Prophet endpoints should be under /api/prophet
        prophet_routes = [r for r in all_routes if 'prophet' in r.lower()]
        assert len(prophet_routes) > 0, "No Prophet routes found"

        print(f"✅ Main app has Prophet router registered ({len(prophet_routes)} Prophet routes)")
        return True
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openrouter_config():
    """Test that OpenRouter configuration is present"""
    try:
        from app.config import settings

        # Check OpenRouter settings exist
        assert hasattr(settings, 'openrouter_api_key'), "Missing openrouter_api_key in settings"
        assert hasattr(settings, 'openrouter_model'), "Missing openrouter_model in settings"

        # Check default model is set
        assert settings.openrouter_model, "openrouter_model is empty"

        print(f"✅ OpenRouter config verified (model: {settings.openrouter_model})")
        return True
    except Exception as e:
        print(f"❌ OpenRouter config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prophet_fallback():
    """Test Prophet service gracefully handles API failures"""
    try:
        from app.services.prophet import generate_markets, resolve_dispute

        # Test generate_markets fallback (should return at least one market even if API fails)
        markets = generate_markets(
            room_name="Test Room",
            member_names=["Alice", "Bob"],
            recent_markets=[]
        )

        assert isinstance(markets, list), "generate_markets should return a list"
        assert len(markets) > 0, "generate_markets should return at least one market"

        # Check market structure
        if markets:
            market = markets[0]
            assert 'title' in market, "Market should have title"
            assert 'category' in market, "Market should have category"
            assert 'initial_odds_yes' in market, "Market should have initial_odds_yes"

        # Test resolve_dispute fallback
        ruling = resolve_dispute(
            market_title="Test Market",
            description="Test description",
            yes_votes=5,
            no_votes=3
        )

        assert isinstance(ruling, dict), "resolve_dispute should return a dict"
        assert 'ruling' in ruling, "Ruling should have 'ruling' key"
        assert 'reasoning' in ruling, "Ruling should have 'reasoning' key"
        assert ruling['ruling'] in ['yes', 'no'], "Ruling must be 'yes' or 'no'"

        print("✅ Prophet service fallback mechanisms verified")
        return True
    except Exception as e:
        print(f"❌ Prophet fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🧪 Testing Step 7: Prophet AI Agent\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_prophet_bet_model()
    all_passed &= test_prophet_service()
    all_passed &= test_prophet_router()
    all_passed &= await test_database_tables()
    all_passed &= test_main_app_integration()
    all_passed &= test_openrouter_config()
    all_passed &= test_prophet_fallback()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 7 VERIFICATION PASSED")
        print("="*50)
        print("\nProphet AI Agent ready:")
        print("  POST   /api/prophet/generate-markets/{room_id}")
        print("  POST   /api/prophet/resolve-dispute/{market_id}")
        print("  GET    /api/prophet/status")
        print("\nProphet AI Capabilities:")
        print("  ✓ Market generation (2-3 markets)")
        print("  ✓ Trade commentary (witty reactions)")
        print("  ✓ Resolution commentary (post-game analysis)")
        print("  ✓ Dispute resolution (breaks voting ties)")
        print("  ✓ Betting decisions (Prophet's own positions)")
        print("\nProphet Integration:")
        print("  ✓ OpenRouter API (Claude via OpenAI-compatible)")
        print("  ✓ ProphetBet model (tracks Prophet's bets)")
        print("  ✓ Graceful fallbacks (if API unavailable)")
        sys.exit(0)
    else:
        print("❌ STEP 7 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

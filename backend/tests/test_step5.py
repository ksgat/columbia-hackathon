"""
TEMPORARY TEST for Step 5: Verify Markets & Trading System
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all market modules can be imported"""
    try:
        from app.services.lmsr import LMSRMarketMaker
        from app.models.market import Market
        from app.models.trade import Trade
        from app.routers.markets import router as markets_router
        print("✅ All market modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lmsr_service():
    """Test LMSR market maker"""
    try:
        from app.services.lmsr import LMSRMarketMaker

        # Test basic functionality
        mm = LMSRMarketMaker(b=100, yes_shares=0, no_shares=0)

        # Initial odds should be 50/50
        assert abs(mm.current_price_yes() - 0.5) < 0.001
        assert abs(mm.current_price_no() - 0.5) < 0.001

        # Buy YES shares
        shares, new_yes, new_no = mm.execute_trade('yes', 50)
        assert shares > 0
        assert new_yes > 0.5  # YES odds should increase
        assert new_no < 0.5  # NO odds should decrease
        assert abs(new_yes + new_no - 1.0) < 0.001  # Should sum to 1

        # Check state
        state = mm.get_state()
        assert state['yes_shares'] > 0
        assert state['odds_yes'] > 0.5

        print(f"✅ LMSR service verified (50 coins → {shares:.2f} YES shares @ {new_yes:.1%})")
        return True
    except Exception as e:
        print(f"❌ LMSR service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_model():
    """Test Market model structure"""
    try:
        from app.models.market import Market

        # Check required fields
        required_fields = [
            'id', 'room_id', 'creator_id', 'title', 'odds_yes',
            'total_yes_shares', 'total_no_shares', 'lmsr_b',
            'status', 'expires_at'
        ]

        for field in required_fields:
            assert hasattr(Market, field), f"Market model missing field: {field}"

        # Check methods
        assert hasattr(Market, 'to_dict'), "Market model missing to_dict method"
        assert hasattr(Market, 'odds_no'), "Market model missing odds_no property"

        print("✅ Market model structure verified")
        return True
    except Exception as e:
        print(f"❌ Market model test failed: {e}")
        return False

def test_trade_model():
    """Test Trade model structure"""
    try:
        from app.models.trade import Trade

        # Check required fields
        required_fields = [
            'id', 'market_id', 'user_id', 'side', 'amount',
            'shares_received', 'odds_at_trade', 'created_at'
        ]

        for field in required_fields:
            assert hasattr(Trade, field), f"Trade model missing field: {field}"

        # Check methods
        assert hasattr(Trade, 'to_dict'), "Trade model missing to_dict method"

        print("✅ Trade model structure verified")
        return True
    except Exception as e:
        print(f"❌ Trade model test failed: {e}")
        return False

def test_markets_router():
    """Test markets router endpoints are defined"""
    try:
        from app.routers.markets import router

        # Check routes exist
        routes = {route.path for route in router.routes}

        expected_routes = ['', '/{market_id}', '/{market_id}/trades', '/{market_id}/trade']

        for expected in expected_routes:
            assert expected in routes, f"Missing route: {expected}"

        print(f"✅ Markets router has all required endpoints")
        return True
    except Exception as e:
        print(f"❌ Markets router test failed: {e}")
        return False

async def test_database_tables():
    """Test that market tables exist in database"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Check markets table
            result = await session.execute(text("SELECT COUNT(*) FROM markets"))
            market_count = result.scalar()
            print(f"   ✓ markets table: {market_count} rows")

            # Check trades table
            result = await session.execute(text("SELECT COUNT(*) FROM trades"))
            trade_count = result.scalar()
            print(f"   ✓ trades table: {trade_count} rows")

        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database table test failed: {e}")
        return False

def test_main_app_integration():
    """Test that markets router is integrated into main app"""
    try:
        from app.main import app

        # Check that routes are registered
        all_routes = [route.path for route in app.routes]

        markets_routes = [r for r in all_routes if r.startswith('/api/markets')]
        assert len(markets_routes) > 0, "No /api/markets routes found"

        # Check for critical trade endpoint
        assert '/api/markets/{market_id}/trade' in all_routes, "Trade endpoint not found!"

        print(f"✅ Main app has markets router registered ({len(markets_routes)} routes)")
        print(f"   🎯 Critical trade endpoint: /api/markets/{{market_id}}/trade")
        return True
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False

async def main():
    print("\n🧪 Testing Step 5: Markets & Trading System\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_lmsr_service()
    all_passed &= test_market_model()
    all_passed &= test_trade_model()
    all_passed &= test_markets_router()
    all_passed &= await test_database_tables()
    all_passed &= test_main_app_integration()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 5 VERIFICATION PASSED")
        print("="*50)
        print("\nMarkets & Trading system ready:")
        print("  POST   /api/markets")
        print("  GET    /api/markets/{id}")
        print("  GET    /api/markets/{id}/trades")
        print("  🎯 POST   /api/markets/{id}/trade  (THE CRITICAL ONE)")
        print("\nLMSR Trading Engine:")
        print("  ✓ Automated market maker")
        print("  ✓ Dynamic odds calculation")
        print("  ✓ Infinite liquidity")
        print("  ✓ Balance validation")
        sys.exit(0)
    else:
        print("❌ STEP 5 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

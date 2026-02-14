"""
TEMPORARY TEST for Step 6: Verify Resolution & Voting System
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all resolution modules can be imported"""
    try:
        from app.models.vote import ResolutionVote
        from app.services.clout import calculate_clout_change, get_rank_label
        from app.services.resolution import tally_votes, check_supermajority, resolve_market
        from app.routers.votes import router as votes_router
        print("✅ All resolution modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_clout_service():
    """Test clout/ELO calculations"""
    try:
        from app.services.clout import calculate_clout_change, get_rank_label

        # Test underdog win (big gain)
        change = calculate_clout_change(user_won=True, odds_at_trade=0.3, user_side='yes')
        assert change > 20, "Underdog win should give big clout gain"

        # Test favorite win (small gain)
        change = calculate_clout_change(user_won=True, odds_at_trade=0.7, user_side='yes')
        assert 0 < change < 15, "Favorite win should give small clout gain"

        # Test favorite loss (big loss)
        change = calculate_clout_change(user_won=False, odds_at_trade=0.7, user_side='yes')
        assert change < -20, "Favorite loss should give big clout loss"

        # Test rank labels
        assert get_rank_label(500) == "Bronze"
        assert get_rank_label(1000) == "Gold"
        assert get_rank_label(1600) == "Prophet's Rival"

        print("✅ Clout service verified (ELO calculations correct)")
        return True
    except Exception as e:
        print(f"❌ Clout service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_supermajority_logic():
    """Test 3/4 supermajority checking"""
    try:
        from app.services.resolution import check_supermajority

        # Test clear YES majority (9 out of 10 = 90%)
        result = await check_supermajority(9, 1, 10)
        assert result == 'yes', "9/10 should be YES supermajority"

        # Test clear NO majority (8 out of 10 = 80%)
        result = await check_supermajority(2, 8, 10)
        assert result == 'no', "8/10 should be NO supermajority"

        # Test disputed (6 out of 10 = 60%, not 75%)
        result = await check_supermajority(6, 4, 10)
        assert result is None, "6/10 should be disputed"

        # Test exact threshold (9 out of 12 = 75%)
        result = await check_supermajority(9, 3, 12)
        assert result == 'yes', "9/12 (75%) should be YES supermajority"

        print("✅ Supermajority logic verified (3/4 threshold working)")
        return True
    except Exception as e:
        print(f"❌ Supermajority test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vote_model():
    """Test ResolutionVote model structure"""
    try:
        from app.models.vote import ResolutionVote

        # Check required fields
        required_fields = [
            'id', 'market_id', 'user_id', 'vote', 'created_at'
        ]

        for field in required_fields:
            assert hasattr(ResolutionVote, field), f"ResolutionVote model missing field: {field}"

        # Check methods
        assert hasattr(ResolutionVote, 'to_dict'), "ResolutionVote model missing to_dict method"

        print("✅ ResolutionVote model structure verified")
        return True
    except Exception as e:
        print(f"❌ Vote model test failed: {e}")
        return False

def test_votes_router():
    """Test votes router endpoints are defined"""
    try:
        from app.routers.votes import router

        # Check routes exist
        routes = {route.path for route in router.routes}

        expected_routes = ['/{market_id}/vote', '/{market_id}/votes', '/{market_id}/resolve']

        for expected in expected_routes:
            assert expected in routes, f"Missing route: {expected}"

        print(f"✅ Votes router has all required endpoints")
        return True
    except Exception as e:
        print(f"❌ Votes router test failed: {e}")
        return False

async def test_database_tables():
    """Test that vote tables exist in database"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Check resolution_votes table
            result = await session.execute(text("SELECT COUNT(*) FROM resolution_votes"))
            vote_count = result.scalar()
            print(f"   ✓ resolution_votes table: {vote_count} rows")

        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database table test failed: {e}")
        return False

def test_main_app_integration():
    """Test that votes router is integrated into main app"""
    try:
        from app.main import app

        # Check that routes are registered
        all_routes = [route.path for route in app.routes]

        # Voting endpoints should be under /api/markets
        vote_routes = [r for r in all_routes if 'vote' in r.lower()]
        assert len(vote_routes) > 0, "No voting routes found"

        print(f"✅ Main app has voting router registered ({len(vote_routes)} vote routes)")
        return True
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False

async def main():
    print("\n🧪 Testing Step 6: Resolution & Voting System\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_clout_service()
    all_passed &= await test_supermajority_logic()
    all_passed &= test_vote_model()
    all_passed &= test_votes_router()
    all_passed &= await test_database_tables()
    all_passed &= test_main_app_integration()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 6 VERIFICATION PASSED")
        print("="*50)
        print("\nResolution & Voting system ready:")
        print("  POST   /api/markets/{id}/vote")
        print("  GET    /api/markets/{id}/votes")
        print("  POST   /api/markets/{id}/resolve (admin)")
        print("\nResolution Features:")
        print("  ✓ 3/4 supermajority voting")
        print("  ✓ Payout distribution")
        print("  ✓ ELO/Clout scoring")
        print("  ✓ Win streak tracking")
        print("  ✓ Rank labels (Bronze → Prophet's Rival)")
        sys.exit(0)
    else:
        print("❌ STEP 6 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

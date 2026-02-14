"""
TEMPORARY TEST for Step 8: Verify Chained Markets
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all chain modules can be imported"""
    try:
        from app.services.chains import (
            validate_chain_creation,
            get_chain_tree,
            activate_child_markets,
            get_pending_children,
            get_active_children,
            MAX_CHAIN_DEPTH
        )
        from app.routers.markets import CreateChainedMarketRequest
        print("✅ All chain modules imported successfully")
        print(f"   Max chain depth: {MAX_CHAIN_DEPTH} levels (root → child)")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chain_depth_limit():
    """Test that chain depth is set correctly"""
    try:
        from app.services.chains import MAX_CHAIN_DEPTH

        assert MAX_CHAIN_DEPTH == 2, f"Expected MAX_CHAIN_DEPTH to be 2, got {MAX_CHAIN_DEPTH}"
        print("✅ Chain depth limit verified (2 levels: root → child)")
        return True
    except Exception as e:
        print(f"❌ Chain depth test failed: {e}")
        return False

async def test_chain_validation_logic():
    """Test chain validation logic"""
    try:
        from app.services.chains import validate_chain_creation
        from app.database import AsyncSessionLocal
        from app.models.market import Market
        from app.models.room import Room
        from app.models.user import User
        from datetime import datetime, timedelta
        import uuid
        import random
        import string

        async with AsyncSessionLocal() as session:
            # Create a test root market with unique join code
            unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            test_room = Room(
                name="Test Chain Room",
                join_code=unique_code,
                currency_mode="virtual"
            )
            session.add(test_room)
            await session.commit()
            await session.refresh(test_room)

            root_market = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Test Root Market",
                description="Root market for chain testing",
                category="test",
                market_type="standard",
                chain_depth=0,
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.utcnow() + timedelta(hours=48)
            )
            session.add(root_market)
            await session.commit()
            await session.refresh(root_market)

            # Test valid chain creation
            is_valid, error, depth = await validate_chain_creation(
                parent_market_id=root_market.id,
                trigger_condition="parent_resolves_yes",
                db=session
            )
            assert is_valid, f"Valid chain creation failed: {error}"
            assert depth == 1, f"Expected depth 1, got {depth}"
            print("   ✓ Valid chain creation accepted")

            # Test invalid trigger condition
            is_valid, error, depth = await validate_chain_creation(
                parent_market_id=root_market.id,
                trigger_condition="invalid_condition",
                db=session
            )
            assert not is_valid, "Invalid trigger condition should be rejected"
            assert "Invalid trigger condition" in error
            print("   ✓ Invalid trigger condition rejected")

            # Test resolved parent rejection
            root_market.status = "resolved"
            await session.commit()

            is_valid, error, depth = await validate_chain_creation(
                parent_market_id=root_market.id,
                trigger_condition="parent_resolves_yes",
                db=session
            )
            assert not is_valid, "Chain to resolved market should be rejected"
            assert "already-resolved" in error
            print("   ✓ Chain to resolved market rejected")

            # Clean up
            await session.delete(root_market)
            await session.delete(test_room)
            await session.commit()

        print("✅ Chain validation logic verified")
        return True
    except Exception as e:
        print(f"❌ Chain validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_child_activation():
    """Test that children activate when parent resolves"""
    try:
        from app.services.chains import activate_child_markets
        from app.database import AsyncSessionLocal
        from app.models.market import Market
        from app.models.room import Room
        from datetime import datetime, timedelta
        import random
        import string

        async with AsyncSessionLocal() as session:
            # Create test room with unique join code
            unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            test_room = Room(
                name="Test Activation Room",
                join_code=unique_code,
                currency_mode="virtual"
            )
            session.add(test_room)
            await session.commit()
            await session.refresh(test_room)

            # Create root market
            root_market = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Root Market",
                category="test",
                market_type="standard",
                chain_depth=0,
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.utcnow() + timedelta(hours=48)
            )
            session.add(root_market)
            await session.commit()
            await session.refresh(root_market)

            # Create two child markets (one for each outcome)
            child_yes = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Child if YES",
                category="test",
                market_type="chained",
                parent_market_id=root_market.id,
                trigger_condition="parent_resolves_yes",
                chain_depth=1,
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="pending",
                expires_at=datetime.utcnow() + timedelta(hours=48)
            )
            child_no = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Child if NO",
                category="test",
                market_type="chained",
                parent_market_id=root_market.id,
                trigger_condition="parent_resolves_no",
                chain_depth=1,
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="pending",
                expires_at=datetime.utcnow() + timedelta(hours=48)
            )
            session.add_all([child_yes, child_no])
            await session.commit()
            await session.refresh(child_yes)
            await session.refresh(child_no)

            # Activate children when parent resolves YES
            activated = await activate_child_markets(root_market, "yes", session)

            assert len(activated) == 1, f"Expected 1 activated child, got {len(activated)}"
            assert activated[0].id == child_yes.id, "Wrong child was activated"

            # Refresh and check status
            await session.refresh(child_yes)
            await session.refresh(child_no)

            assert child_yes.status == "active", f"Child YES should be active, got {child_yes.status}"
            assert child_no.status == "pending", f"Child NO should still be pending, got {child_no.status}"
            print("   ✓ Correct child activated when parent resolves YES")

            # Clean up (delete children first due to foreign key)
            await session.delete(child_yes)
            await session.delete(child_no)
            await session.commit()
            await session.delete(root_market)
            await session.commit()
            await session.delete(test_room)
            await session.commit()

        print("✅ Child activation logic verified")
        return True
    except Exception as e:
        print(f"❌ Child activation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chain_endpoints():
    """Test that chain endpoints are registered"""
    try:
        from app.routers.markets import router

        routes = {route.path for route in router.routes}

        expected_routes = [
            '/chains/create',
            '/{market_id}/chain-tree',
            '/{market_id}/children'
        ]

        for route in expected_routes:
            assert route in routes, f"Missing route: {route}"

        print("✅ Chain endpoints registered")
        print(f"   ✓ POST /api/markets/chains/create")
        print(f"   ✓ GET  /api/markets/{{id}}/chain-tree")
        print(f"   ✓ GET  /api/markets/{{id}}/children")
        return True
    except Exception as e:
        print(f"❌ Chain endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_resolution_integration():
    """Test that resolution service activates children"""
    try:
        from app.services.resolution import resolve_market

        # Check that activate_child_markets is imported
        import inspect
        source = inspect.getsource(resolve_market)
        assert 'activate_child_markets' in source, "Resolution service should call activate_child_markets"
        assert 'children_activated' in source, "Resolution should return children_activated count"

        print("✅ Resolution service integrated with chain activation")
        return True
    except Exception as e:
        print(f"❌ Resolution integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🧪 Testing Step 8: Chained Markets\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_chain_depth_limit()
    all_passed &= await test_chain_validation_logic()
    all_passed &= await test_child_activation()
    all_passed &= test_chain_endpoints()
    all_passed &= await test_resolution_integration()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 8 VERIFICATION PASSED")
        print("="*50)
        print("\nChained Markets ready:")
        print("  POST   /api/markets/chains/create")
        print("  GET    /api/markets/{id}/chain-tree")
        print("  GET    /api/markets/{id}/children")
        print("\nChained Market Features:")
        print("  ✓ 2-level chains (root → child)")
        print("  ✓ Trigger conditions (parent_resolves_yes/no)")
        print("  ✓ Pending → Active status flow")
        print("  ✓ Auto-activation on parent resolution")
        print("  ✓ Chain validation (depth limits, resolved parent check)")
        print("  ✓ Chain tree visualization endpoint")
        sys.exit(0)
    else:
        print("❌ STEP 8 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

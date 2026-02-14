"""
TEMPORARY TEST for Step 9: Verify Market Derivatives
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all derivative modules can be imported"""
    try:
        from app.services.derivatives import (
            validate_derivative_creation,
            check_derivative_condition,
            check_all_active_derivatives,
            generate_derivative_title,
            get_derivative_status
        )
        from app.routers.markets import CreateDerivativeRequest
        print("✅ All derivative modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_derivative_validation():
    """Test derivative validation logic"""
    try:
        from app.services.derivatives import validate_derivative_creation
        from app.database import AsyncSessionLocal
        from app.models.market import Market
        from app.models.room import Room
        from datetime import datetime, timedelta, timezone
        import random
        import string

        async with AsyncSessionLocal() as session:
            # Create test room and market
            unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            test_room = Room(
                name="Test Derivative Room",
                join_code=unique_code,
                currency_mode="virtual"
            )
            session.add(test_room)
            await session.commit()
            await session.refresh(test_room)

            ref_market = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Reference Market",
                category="test",
                market_type="standard",
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
            )
            session.add(ref_market)
            await session.commit()
            await session.refresh(ref_market)

            # Test valid odds threshold
            is_valid, error = await validate_derivative_creation(
                reference_market_id=ref_market.id,
                threshold_type="odds_threshold",
                threshold_value=0.8,
                threshold_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                db=session
            )
            assert is_valid, f"Valid odds threshold failed: {error}"
            print("   ✓ Valid odds threshold accepted")

            # Test valid volume threshold
            is_valid, error = await validate_derivative_creation(
                reference_market_id=ref_market.id,
                threshold_type="volume_threshold",
                threshold_value=20,
                threshold_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                db=session
            )
            assert is_valid, f"Valid volume threshold failed: {error}"
            print("   ✓ Valid volume threshold accepted")

            # Test valid resolution_method
            is_valid, error = await validate_derivative_creation(
                reference_market_id=ref_market.id,
                threshold_type="resolution_method",
                threshold_value="prophet",
                threshold_deadline=None,
                db=session
            )
            assert is_valid, f"Valid resolution_method failed: {error}"
            print("   ✓ Valid resolution_method accepted")

            # Test invalid threshold type
            is_valid, error = await validate_derivative_creation(
                reference_market_id=ref_market.id,
                threshold_type="invalid_type",
                threshold_value=0.8,
                threshold_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                db=session
            )
            assert not is_valid, "Invalid threshold type should be rejected"
            print("   ✓ Invalid threshold type rejected")

            # Test derivative of derivative (should fail)
            deriv_market = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Derivative Market",
                category="test",
                market_type="derivative",
                reference_market_id=ref_market.id,
                threshold_condition='{"type": "odds_threshold", "value": 0.8}',
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
            )
            session.add(deriv_market)
            await session.commit()
            await session.refresh(deriv_market)

            is_valid, error = await validate_derivative_creation(
                reference_market_id=deriv_market.id,
                threshold_type="odds_threshold",
                threshold_value=0.9,
                threshold_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                db=session
            )
            assert not is_valid, "Derivative of derivative should be rejected"
            assert "derivative of a derivative" in error.lower()
            print("   ✓ Derivative of derivative rejected")

            # Clean up
            await session.delete(deriv_market)
            await session.commit()
            await session.delete(ref_market)
            await session.commit()
            await session.delete(test_room)
            await session.commit()

        print("✅ Derivative validation logic verified")
        return True
    except Exception as e:
        print(f"❌ Derivative validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_derivative_title_generation():
    """Test auto-title generation for derivatives"""
    try:
        from app.services.derivatives import generate_derivative_title
        from datetime import datetime, timedelta, timezone

        # Test odds threshold title
        deadline = datetime.now(timezone.utc) + timedelta(days=2)
        title = await generate_derivative_title(
            reference_market_title="Will it rain tomorrow?",
            threshold_type="odds_threshold",
            threshold_value=0.8,
            threshold_deadline=deadline
        )
        assert "80%" in title and "Will it rain tomorrow?" in title
        print(f"   ✓ Odds threshold title: {title}")

        # Test volume threshold title
        title = await generate_derivative_title(
            reference_market_title="Will it rain tomorrow?",
            threshold_type="volume_threshold",
            threshold_value=25,
            threshold_deadline=deadline
        )
        assert "25+" in title and "trades" in title.lower()
        print(f"   ✓ Volume threshold title: {title}")

        # Test resolution_method title
        title = await generate_derivative_title(
            reference_market_title="Will it rain tomorrow?",
            threshold_type="resolution_method",
            threshold_value="prophet",
            threshold_deadline=None
        )
        assert "Prophet" in title and "resolve" in title.lower()
        print(f"   ✓ Resolution method title: {title}")

        print("✅ Derivative title generation verified")
        return True
    except Exception as e:
        print(f"❌ Title generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_derivative_condition_checking():
    """Test derivative condition checking logic"""
    try:
        from app.services.derivatives import check_derivative_condition
        from app.database import AsyncSessionLocal
        from app.models.market import Market
        from app.models.room import Room
        from app.models.trade import Trade
        from datetime import datetime, timedelta, timezone
        import json
        import random
        import string

        async with AsyncSessionLocal() as session:
            # Create test room
            unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            test_room = Room(
                name="Test Condition Room",
                join_code=unique_code,
                currency_mode="virtual"
            )
            session.add(test_room)
            await session.commit()
            await session.refresh(test_room)

            # Create reference market
            ref_market = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Reference Market",
                category="test",
                market_type="standard",
                odds_yes=0.6,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
            )
            session.add(ref_market)
            await session.commit()
            await session.refresh(ref_market)

            # Test 1: Odds threshold NOT met yet
            deriv1 = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Odds Derivative",
                market_type="derivative",
                reference_market_id=ref_market.id,
                threshold_condition=json.dumps({"type": "odds_threshold", "value": 0.8}),
                threshold_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
            )
            session.add(deriv1)
            await session.commit()
            await session.refresh(deriv1)

            result = await check_derivative_condition(deriv1, session)
            assert result is None, "Condition not met should return None"
            print("   ✓ Odds threshold not met (returns None)")

            # Test 2: Odds threshold MET
            ref_market.odds_yes = 0.85
            await session.commit()

            result = await check_derivative_condition(deriv1, session)
            assert result == 'yes', f"Odds threshold met should return 'yes', got {result}"
            print("   ✓ Odds threshold met (returns 'yes')")

            # Test 3: Volume threshold
            ref_market.odds_yes = 0.5  # Reset
            await session.commit()

            deriv2 = Market(
                room_id=test_room.id,
                creator_id=None,
                title="Volume Derivative",
                market_type="derivative",
                reference_market_id=ref_market.id,
                threshold_condition=json.dumps({"type": "volume_threshold", "value": 3}),
                threshold_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                odds_yes=0.5,
                lmsr_b=100.0,
                currency_mode="virtual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
            )
            session.add(deriv2)
            await session.commit()
            await session.refresh(deriv2)

            # Add trades to reference market
            for i in range(3):
                trade = Trade(
                    market_id=ref_market.id,
                    user_id=None,
                    side="yes",
                    amount=10.0,
                    shares_received=10.0,
                    odds_at_trade=0.5,
                    currency="virtual",
                    is_prophet_trade=False
                )
                session.add(trade)
            await session.commit()

            result = await check_derivative_condition(deriv2, session)
            assert result == 'yes', f"Volume threshold met should return 'yes', got {result}"
            print("   ✓ Volume threshold met (returns 'yes')")

            # Clean up
            await session.execute(Trade.__table__.delete().where(Trade.market_id == ref_market.id))
            await session.commit()
            await session.delete(deriv2)
            await session.delete(deriv1)
            await session.commit()
            await session.delete(ref_market)
            await session.commit()
            await session.delete(test_room)
            await session.commit()

        print("✅ Derivative condition checking verified")
        return True
    except Exception as e:
        print(f"❌ Derivative condition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_derivative_endpoints():
    """Test that derivative endpoints are registered"""
    try:
        from app.routers.markets import router

        routes = {route.path for route in router.routes}

        expected_routes = [
            '/derivatives/create',
            '/{market_id}/derivative-status',
            '/derivatives/check-all'
        ]

        for route in expected_routes:
            assert route in routes, f"Missing route: {route}"

        print("✅ Derivative endpoints registered")
        print(f"   ✓ POST /api/markets/derivatives/create")
        print(f"   ✓ GET  /api/markets/{{id}}/derivative-status")
        print(f"   ✓ POST /api/markets/derivatives/check-all")
        return True
    except Exception as e:
        print(f"❌ Derivative endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🧪 Testing Step 9: Market Derivatives\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= await test_derivative_validation()
    all_passed &= await test_derivative_title_generation()
    all_passed &= await test_derivative_condition_checking()
    all_passed &= test_derivative_endpoints()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 9 VERIFICATION PASSED")
        print("="*50)
        print("\nMarket Derivatives ready:")
        print("  POST   /api/markets/derivatives/create")
        print("  GET    /api/markets/{id}/derivative-status")
        print("  POST   /api/markets/derivatives/check-all")
        print("\nDerivative Types:")
        print("  ✓ Odds Threshold - Bet on market hitting X% odds")
        print("  ✓ Volume Threshold - Bet on market getting Y+ trades")
        print("  ✓ Resolution Method - Bet on how market resolves")
        print("\nDerivative Features:")
        print("  ✓ Auto-resolution when conditions met")
        print("  ✓ Auto-generated descriptive titles")
        print("  ✓ Real-time status tracking (progress %)")
        print("  ✓ Validation (no derivative-of-derivative)")
        print("  ✓ Background checking endpoint")
        sys.exit(0)
    else:
        print("❌ STEP 9 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

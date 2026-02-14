"""
TEMPORARY TEST for Step 4: Verify Rooms System
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all room modules can be imported"""
    try:
        from app.models.room import Room, Membership
        from app.routers.rooms import router as rooms_router
        print("✅ All room modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_room_model():
    """Test Room model structure"""
    try:
        from app.models.room import Room

        # Check model has required fields
        required_fields = [
            'id', 'name', 'join_code', 'creator_id', 'currency_mode',
            'min_bet', 'max_bet', 'max_members', 'is_active'
        ]

        for field in required_fields:
            assert hasattr(Room, field), f"Room model missing field: {field}"

        # Check methods
        assert hasattr(Room, 'to_dict'), "Room model missing to_dict method"
        assert hasattr(Room, 'generate_join_code'), "Room model missing generate_join_code method"

        # Test join code generation
        code = Room.generate_join_code()
        assert len(code) == 6, f"Join code should be 6 chars, got {len(code)}"
        assert code.isalnum(), "Join code should be alphanumeric"

        print(f"✅ Room model structure verified (sample join code: {code})")
        return True
    except Exception as e:
        print(f"❌ Room model test failed: {e}")
        return False

def test_membership_model():
    """Test Membership model structure"""
    try:
        from app.models.room import Membership

        # Check model has required fields
        required_fields = [
            'id', 'user_id', 'room_id', 'role', 'coins_virtual', 'joined_at'
        ]

        for field in required_fields:
            assert hasattr(Membership, field), f"Membership model missing field: {field}"

        # Check methods
        assert hasattr(Membership, 'to_dict'), "Membership model missing to_dict method"

        print("✅ Membership model structure verified")
        return True
    except Exception as e:
        print(f"❌ Membership model test failed: {e}")
        return False

def test_rooms_router():
    """Test rooms router endpoints are defined"""
    try:
        from app.routers.rooms import router

        # Check routes exist
        routes = {route.path for route in router.routes}

        expected_routes = [
            '', '/{room_id}', '/{room_id}/join', '/{room_id}/leave',
            '/{room_id}/members', '/{room_id}/leaderboard'
        ]

        for expected in expected_routes:
            assert expected in routes, f"Missing route: {expected}"

        print(f"✅ Rooms router has all required endpoints")
        return True
    except Exception as e:
        print(f"❌ Rooms router test failed: {e}")
        return False

async def test_database_tables():
    """Test that room tables exist in database"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Check rooms table
            result = await session.execute(text("SELECT COUNT(*) FROM rooms"))
            room_count = result.scalar()
            print(f"   ✓ rooms table: {room_count} rows")

            # Check memberships table
            result = await session.execute(text("SELECT COUNT(*) FROM memberships"))
            membership_count = result.scalar()
            print(f"   ✓ memberships table: {membership_count} rows")

        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database table test failed: {e}")
        return False

def test_main_app_integration():
    """Test that rooms router is integrated into main app"""
    try:
        from app.main import app

        # Check that routes are registered
        all_routes = [route.path for route in app.routes]

        rooms_routes = [r for r in all_routes if r.startswith('/api/rooms')]
        assert len(rooms_routes) > 0, "No /api/rooms routes found"

        print(f"✅ Main app has rooms router registered ({len(rooms_routes)} routes)")
        return True
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False

async def main():
    print("\n🧪 Testing Step 4: Rooms System\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_room_model()
    all_passed &= test_membership_model()
    all_passed &= test_rooms_router()
    all_passed &= await test_database_tables()
    all_passed &= test_main_app_integration()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 4 VERIFICATION PASSED")
        print("="*50)
        print("\nRooms system ready:")
        print("  POST   /api/rooms")
        print("  GET    /api/rooms")
        print("  GET    /api/rooms/{id}")
        print("  POST   /api/rooms/{id}/join")
        print("  POST   /api/rooms/{id}/leave")
        print("  GET    /api/rooms/{id}/members")
        print("  GET    /api/rooms/{id}/leaderboard")
        sys.exit(0)
    else:
        print("❌ STEP 4 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

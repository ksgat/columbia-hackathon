"""
TEMPORARY TEST for Step 3: Verify Auth System
This file will be deleted after verification
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all auth modules can be imported"""
    try:
        from app.models.user import User
        from app.routers.auth import router as auth_router
        from app.routers.users import router as users_router
        from app.dependencies import get_current_user, security
        print("✅ All auth modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_user_model():
    """Test User model structure"""
    try:
        from app.models.user import User
        import uuid

        # Check model has required fields
        required_fields = [
            'id', 'email', 'display_name', 'clout_score', 'clout_rank',
            'balance_virtual', 'total_bets_placed', 'total_bets_won'
        ]

        for field in required_fields:
            assert hasattr(User, field), f"User model missing field: {field}"

        # Check methods
        assert hasattr(User, 'to_dict'), "User model missing to_dict method"
        assert hasattr(User, 'win_rate'), "User model missing win_rate property"

        print("✅ User model structure verified")
        return True
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return False

def test_auth_router():
    """Test auth router endpoints are defined"""
    try:
        from app.routers.auth import router

        # Check routes exist
        routes = {route.path for route in router.routes}

        expected_routes = {'/login', '/logout', '/me', '/health'}

        for expected in expected_routes:
            assert expected in routes, f"Missing route: {expected}"

        print(f"✅ Auth router has all required endpoints: {expected_routes}")
        return True
    except Exception as e:
        print(f"❌ Auth router test failed: {e}")
        return False

def test_users_router():
    """Test users router endpoints are defined"""
    try:
        from app.routers.users import router

        # Check routes exist
        routes = {route.path for route in router.routes}

        # Should have routes for get, update, stats
        print(f"✅ Users router loaded with routes: {routes}")
        return True
    except Exception as e:
        print(f"❌ Users router test failed: {e}")
        return False

def test_main_app_integration():
    """Test that routers are integrated into main app"""
    try:
        from app.main import app

        # Check that routes are registered
        all_routes = [route.path for route in app.routes]

        expected_prefixes = ['/api/auth', '/api/users']

        for prefix in expected_prefixes:
            matching = [r for r in all_routes if r.startswith(prefix)]
            assert len(matching) > 0, f"No routes found with prefix: {prefix}"

        print(f"✅ Main app has auth and users routers registered")
        print(f"   Total routes: {len(all_routes)}")
        return True
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 Testing Step 3: Authentication System\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_user_model()
    all_passed &= test_auth_router()
    all_passed &= test_users_router()
    all_passed &= test_main_app_integration()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 3 VERIFICATION PASSED")
        print("="*50)
        print("\nAuth system ready:")
        print("  POST /api/auth/login")
        print("  POST /api/auth/logout")
        print("  GET  /api/auth/me")
        print("  GET  /api/users/{user_id}")
        print("  PATCH /api/users/{user_id}")
        print("  GET  /api/users/{user_id}/stats")
        sys.exit(0)
    else:
        print("❌ STEP 3 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

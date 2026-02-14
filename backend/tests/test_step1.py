"""
TEMPORARY TEST for Step 1: Verify FastAPI app structure
This file will be deleted after verification
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that core modules can be imported"""
    try:
        from app.main import app
        from app.config import settings
        print("✅ Core modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test that config loads"""
    try:
        from app.config import settings
        print(f"✅ Config loaded: {settings.app_name}")
        print(f"   Debug mode: {settings.debug}")
        return True
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return False

def test_app_structure():
    """Test that FastAPI app is properly structured"""
    try:
        from app.main import app
        print(f"✅ FastAPI app created: {app.title}")
        print(f"   Version: {app.version}")
        print(f"   Routes: {[route.path for route in app.routes]}")
        return True
    except Exception as e:
        print(f"❌ App structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 Testing Step 1: Project Structure\n")

    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_config()
    all_passed &= test_app_structure()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 1 VERIFICATION PASSED")
        print("="*50)
        sys.exit(0)
    else:
        print("❌ STEP 1 VERIFICATION FAILED")
        print("="*50)
        sys.exit(1)

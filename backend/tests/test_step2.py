"""
TEMPORARY TEST for Step 2: Verify Database Connection
This file will be deleted after verification
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_db_connection():
    """Test basic database connection"""
    try:
        from app.database import test_db_connection
        result = await test_db_connection()
        if result:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def test_query_users():
    """Test querying the users table"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Query for Prophet user
            result = await session.execute(
                text("SELECT id, display_name, email FROM users WHERE email = 'prophet@prophecy.ai'")
            )
            prophet = result.fetchone()

            if prophet:
                print(f"✅ Found Prophet user: {prophet.display_name} ({prophet.email})")
                return True
            else:
                print("❌ Prophet user not found. Did you run schema.sql?")
                return False

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

async def test_supabase_client():
    """Test Supabase client initialization"""
    try:
        from app.database import get_supabase_client
        client = get_supabase_client()
        print(f"✅ Supabase client initialized: {client.supabase_url}")
        return True
    except Exception as e:
        print(f"❌ Supabase client failed: {e}")
        return False

async def test_tables_exist():
    """Test that all required tables exist"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        required_tables = [
            'users', 'rooms', 'memberships', 'markets', 'trades',
            'resolution_votes', 'prophet_bets', 'anomaly_flags',
            'narrative_events', 'whispers', 'achievements'
        ]

        async with AsyncSessionLocal() as session:
            for table in required_tables:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                count = result.scalar()
                print(f"   ✓ {table}: {count} rows")

        print(f"✅ All {len(required_tables)} tables exist")
        return True

    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

async def main():
    print("\n🧪 Testing Step 2: Database Connection\n")

    all_passed = True
    all_passed &= await test_db_connection()
    all_passed &= await test_supabase_client()
    all_passed &= await test_tables_exist()
    all_passed &= await test_query_users()

    print("\n" + "="*50)
    if all_passed:
        print("✅ STEP 2 VERIFICATION PASSED")
        print("="*50)
        sys.exit(0)
    else:
        print("❌ STEP 2 VERIFICATION FAILED")
        print("\nPlease check:")
        print("1. DATABASE_URL is set in .env")
        print("2. Supabase project is running")
        print("3. schema.sql was executed in Supabase SQL Editor")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

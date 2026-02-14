"""
Simple migration script to update database schema
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    """Add missing columns to users table"""

    migrations = [
        # Add is_npc column if it doesn't exist
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_name='users' AND column_name='is_npc') THEN
                ALTER TABLE users ADD COLUMN is_npc BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,

        # Ensure tokens column exists with correct type
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_name='users' AND column_name='tokens') THEN
                ALTER TABLE users ADD COLUMN tokens DOUBLE PRECISION DEFAULT 1000.0;
            END IF;
        END $$;
        """,

        # Add total_trades if missing
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_name='users' AND column_name='total_trades') THEN
                ALTER TABLE users ADD COLUMN total_trades INTEGER DEFAULT 0;
            END IF;
        END $$;
        """,

        # Add successful_predictions if missing
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_name='users' AND column_name='successful_predictions') THEN
                ALTER TABLE users ADD COLUMN successful_predictions INTEGER DEFAULT 0;
            END IF;
        END $$;
        """,
    ]

    print("Running database migrations...")
    async with engine.begin() as conn:
        for migration in migrations:
            try:
                await conn.execute(text(migration))
                print("✓ Migration executed successfully")
            except Exception as e:
                print(f"✗ Migration failed: {e}")

    print("✅ Migrations complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

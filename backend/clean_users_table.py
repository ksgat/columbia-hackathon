"""
Clean migration: Drop and recreate users table with correct schema
"""
import asyncio
from sqlalchemy import text
from app.database import engine
from app.models.user import User

async def clean_users_table():
    """Drop and recreate users table with clean schema"""
    async with engine.begin() as conn:
        print("🗑️  Dropping existing users table...")
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))

        print("✨ Creating clean users table...")
        # Create table with exact columns from User model
        await conn.execute(text("""
            CREATE TABLE users (
                id VARCHAR PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                display_name VARCHAR NOT NULL,
                is_npc BOOLEAN DEFAULT FALSE,
                tokens DOUBLE PRECISION DEFAULT 1000.0,
                total_trades INTEGER DEFAULT 0,
                successful_predictions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create index on email
        await conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))

        print("👤 Creating demo user...")
        await conn.execute(text("""
            INSERT INTO users (id, email, display_name, is_npc, tokens, total_trades, successful_predictions)
            VALUES (
                gen_random_uuid()::text,
                'demo@prophecy.com',
                'Demo User',
                FALSE,
                1000.0,
                0,
                0
            )
        """))

        # Create some NPC users
        print("🤖 Creating NPC users...")
        npc_names = ['Prophet Alpha', 'Oracle Beta', 'Seer Gamma', 'Sage Delta']
        for i, name in enumerate(npc_names):
            await conn.execute(text(f"""
                INSERT INTO users (id, email, display_name, is_npc, tokens, total_trades, successful_predictions)
                VALUES (
                    gen_random_uuid()::text,
                    'npc{i+1}@prophecy.com',
                    '{name}',
                    TRUE,
                    1000.0,
                    0,
                    0
                )
            """))

        print("✅ Users table cleaned and seeded successfully!")

if __name__ == "__main__":
    asyncio.run(clean_users_table())

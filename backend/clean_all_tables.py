"""
Comprehensive clean migration: Drop and recreate all tables with correct schema
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def clean_all_tables():
    """Drop and recreate all tables with clean schemas"""
    async with engine.begin() as conn:
        print("🗑️  Dropping existing tables and types...")
        await conn.execute(text("DROP TABLE IF EXISTS trades CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS votes CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS markets CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS memberships CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS rooms CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS roomstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS markettype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS marketstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS tradetype CASCADE"))

        print("✨ Creating clean users table...")
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
        await conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))

        print("✨ Creating RoomStatus ENUM type...")
        await conn.execute(text("""
            CREATE TYPE roomstatus AS ENUM ('ACTIVE', 'ARCHIVED', 'LOCKED')
        """))

        print("✨ Creating clean rooms table...")
        await conn.execute(text("""
            CREATE TABLE rooms (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                slug VARCHAR UNIQUE NOT NULL,
                creator_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                is_public BOOLEAN DEFAULT TRUE,
                status roomstatus DEFAULT 'ACTIVE',
                max_members INTEGER DEFAULT 100,
                theme_color VARCHAR,
                cover_image VARCHAR,
                member_count INTEGER DEFAULT 0,
                market_count INTEGER DEFAULT 0,
                total_volume INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX idx_rooms_slug ON rooms(slug)"))
        await conn.execute(text("CREATE INDEX idx_rooms_creator ON rooms(creator_id)"))

        print("✨ Creating MarketType and MarketStatus ENUM types...")
        await conn.execute(text("""
            CREATE TYPE markettype AS ENUM ('BINARY', 'MULTIPLE_CHOICE', 'SCALAR')
        """))
        await conn.execute(text("""
            CREATE TYPE marketstatus AS ENUM ('OPEN', 'CLOSED', 'RESOLVED', 'CANCELLED')
        """))

        print("✨ Creating clean markets table...")
        await conn.execute(text("""
            CREATE TABLE markets (
                id VARCHAR PRIMARY KEY,
                question TEXT NOT NULL,
                description TEXT,
                room_id VARCHAR NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                creator_id VARCHAR NOT NULL REFERENCES users(id),
                market_type markettype DEFAULT 'BINARY',
                status marketstatus DEFAULT 'OPEN',
                options JSON,
                liquidity DOUBLE PRECISION DEFAULT 100.0,
                shares JSON DEFAULT '{}',
                prices JSON DEFAULT '{}',
                resolution VARCHAR,
                resolved_at TIMESTAMP,
                resolved_by VARCHAR REFERENCES users(id),
                close_time TIMESTAMP,
                resolve_time TIMESTAMP,
                total_volume DOUBLE PRECISION DEFAULT 0.0,
                total_traders INTEGER DEFAULT 0,
                prophet_prediction DOUBLE PRECISION,
                prophet_reasoning TEXT,
                prophet_last_update TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX idx_markets_room ON markets(room_id)"))
        await conn.execute(text("CREATE INDEX idx_markets_creator ON markets(creator_id)"))

        print("✨ Creating TradeType ENUM type...")
        await conn.execute(text("""
            CREATE TYPE tradetype AS ENUM ('BUY', 'SELL')
        """))

        print("✨ Creating clean trades table...")
        await conn.execute(text("""
            CREATE TABLE trades (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id),
                market_id VARCHAR NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
                trade_type tradetype NOT NULL,
                outcome VARCHAR NOT NULL,
                shares DOUBLE PRECISION NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                cost DOUBLE PRECISION NOT NULL,
                previous_shares DOUBLE PRECISION DEFAULT 0.0,
                realized_profit DOUBLE PRECISION,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX idx_trades_market ON trades(market_id)"))
        await conn.execute(text("CREATE INDEX idx_trades_user ON trades(user_id)"))

        print("👤 Creating demo user...")
        result = await conn.execute(text("""
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
            RETURNING id
        """))
        demo_user_id = result.scalar()

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

        print("🏠 Creating sample room...")
        await conn.execute(text(f"""
            INSERT INTO rooms (id, name, description, slug, creator_id, is_public, member_count)
            VALUES (
                gen_random_uuid()::text,
                'Demo Room',
                'A sample room for getting started',
                'demo-room',
                '{demo_user_id}',
                TRUE,
                1
            )
        """))

        print("✅ All tables cleaned and seeded successfully!")

if __name__ == "__main__":
    asyncio.run(clean_all_tables())

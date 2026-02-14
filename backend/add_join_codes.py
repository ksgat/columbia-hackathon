"""
Migration: Add join_code to rooms table
"""
import asyncio
import random
import string
from sqlalchemy import text
from app.database import engine


def generate_join_code(length=8):
    """Generate a random join code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


async def migrate():
    """Add join_code column to rooms table"""
    async with engine.begin() as conn:
        # Add join_code column
        print("Adding join_code column to rooms table...")
        try:
            await conn.execute(text("""
                ALTER TABLE rooms
                ADD COLUMN IF NOT EXISTS join_code VARCHAR NOT NULL DEFAULT 'TEMP0000'
            """))
            print("✓ Column added")
        except Exception as e:
            print(f"Column might already exist: {e}")

        # Generate unique join codes for existing rooms
        print("Generating unique join codes for existing rooms...")
        result = await conn.execute(text("SELECT id FROM rooms"))
        room_ids = [row[0] for row in result]

        used_codes = set()
        for room_id in room_ids:
            # Generate unique code
            while True:
                code = generate_join_code()
                if code not in used_codes:
                    used_codes.add(code)
                    break

            await conn.execute(
                text("UPDATE rooms SET join_code = :code WHERE id = :id"),
                {"code": code, "id": room_id}
            )
            print(f"  Room {room_id}: {code}")

        # Add unique constraint
        print("Adding unique constraint to join_code...")
        try:
            await conn.execute(text("""
                ALTER TABLE rooms
                ADD CONSTRAINT rooms_join_code_unique UNIQUE (join_code)
            """))
            print("✓ Constraint added")
        except Exception as e:
            print(f"Constraint might already exist: {e}")

        print("\n✓ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

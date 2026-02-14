"""
Database connection and session management
Uses SQLAlchemy 2.0 with async support
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from app.config import settings

# Create async engine
# Note: asyncpg requires postgresql+asyncpg:// prefix
if settings.database_url:
    # Convert postgres:// to postgresql+asyncpg://
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://")
else:
    # Fallback if DATABASE_URL not set
    db_url = "postgresql+asyncpg://localhost/prophecy"

engine = create_async_engine(
    db_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass

# Dependency for FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session to route handlers.
    Automatically commits on success, rolls back on error.

    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Alternative: Supabase client for Realtime and Auth
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """
    Get Supabase client for Auth and Realtime features.
    For database operations, prefer SQLAlchemy above.
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError("Supabase credentials not configured")

    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key
    )

# Test connection
async def test_db_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

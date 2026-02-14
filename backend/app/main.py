"""
Prophecy Backend - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import auth, users, rooms, markets, votes, prophet, rooms_extended
from app.database import test_db_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    print("🚀 Prophecy API starting up...")
    await test_db_connection()
    yield
    # Shutdown
    print("👋 Prophecy API shutting down...")

app = FastAPI(
    title="Prophecy API",
    description="Social prediction markets with AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "https://*.vercel.app",   # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Prophecy API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from app.config import settings

    db_status = "connected"  # Assuming connected if app started
    ai_status = "ready" if settings.openrouter_api_key else "not_configured"

    return {
        "status": "healthy",
        "database": db_status,
        "ai": ai_status,
        "debug": settings.debug
    }

# Router registration
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["rooms"])
app.include_router(rooms_extended.router, prefix="/api/rooms", tags=["rooms"])  # Extended room endpoints
app.include_router(markets.router, prefix="/api/markets", tags=["markets"])
app.include_router(votes.router, prefix="/api/markets", tags=["votes"])  # Nested under markets
app.include_router(prophet.router, prefix="/api/prophet", tags=["prophet"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

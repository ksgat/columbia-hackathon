"""
Prophet AI routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.room import Room
from app.models.market import Market
from app.dependencies import get_current_user
from app.services.prophet import get_prophet


router = APIRouter()


class AnalyzeMarketRequest(BaseModel):
    question: str
    description: Optional[str] = None
    context: Optional[dict] = None


class SuggestMarketsRequest(BaseModel):
    room_id: str
    count: int = 5


@router.post("/analyze")
async def analyze_question(request: AnalyzeMarketRequest):
    """
    Get Prophet's analysis of a market question.
    Useful for testing ideas before creating a market.
    """
    prophet = get_prophet()

    analysis = await prophet.analyze_market(
        question=request.question,
        description=request.description,
        context=request.context
    )

    return {
        "question": request.question,
        "analysis": analysis,
    }


@router.post("/suggest")
async def suggest_markets(
    request: SuggestMarketsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Prophet's suggestions for new markets in a room.
    """
    # Get room
    result = await db.execute(
        select(Room).where(Room.id == request.room_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Get existing markets in room
    result = await db.execute(
        select(Market.question)
        .where(Market.room_id == request.room_id)
        .limit(20)
    )
    existing_questions = [row[0] for row in result.all()]

    # Get suggestions from Prophet
    prophet = get_prophet()
    suggestions = await prophet.suggest_markets(
        room_name=room.name,
        room_description=room.description,
        existing_markets=existing_questions,
        count=request.count
    )

    return {
        "room_id": room.id,
        "room_name": room.name,
        "suggestions": suggestions,
    }


@router.get("/health")
async def prophet_health():
    """
    Check if Prophet AI service is available.
    """
    from app.config import settings

    if not settings.openrouter_api_key:
        return {
            "status": "not_configured",
            "message": "OpenRouter API key not set"
        }

    # Try a simple test
    try:
        prophet = get_prophet()
        # Could do a test call here if needed
        return {
            "status": "ready",
            "model": prophet.model,
            "message": "Prophet AI is ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

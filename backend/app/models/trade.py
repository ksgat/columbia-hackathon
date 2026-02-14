"""
Trade model - represents trades/bets on markets
"""
from sqlalchemy import String, Float, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid

from app.database import Base

class Trade(Base):
    """Trade model - records of trades placed on markets"""
    __tablename__ = "trades"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Relationships
    market_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,  # NULL for Prophet's trades
        index=True
    )

    # Prophet flag
    is_prophet_trade: Mapped[bool] = mapped_column(Boolean, default=False)

    # Trade details
    side: Mapped[str] = mapped_column(
        String,
        nullable=False
        # CHECK constraint in database
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Coins spent
    shares_received: Mapped[float] = mapped_column(Float, nullable=False)  # Shares received
    odds_at_trade: Mapped[float] = mapped_column(Float, nullable=False)  # Snapshot of odds_yes

    # Currency
    currency: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="virtual"
        # CHECK constraint in database
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, market_id={self.market_id}, side={self.side}, amount={self.amount})>"

    def to_dict(self) -> dict:
        """Convert trade to dictionary for API responses"""
        return {
            "id": str(self.id),
            "market_id": str(self.market_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "is_prophet_trade": self.is_prophet_trade,
            "side": self.side,
            "amount": self.amount,
            "shares_received": self.shares_received,
            "odds_at_trade": self.odds_at_trade,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

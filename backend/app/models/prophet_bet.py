"""
ProphetBet model - Prophet's own positions on markets
"""
from sqlalchemy import String, Float, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.database import Base

class ProphetBet(Base):
    """ProphetBet model - Oracle's own betting positions"""
    __tablename__ = "prophet_bets"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Relationship (unique - one Prophet bet per market)
    market_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Prophet's position
    side: Mapped[str] = mapped_column(
        String,
        nullable=False
        # CHECK constraint in database
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    reasoning: Mapped[str] = mapped_column(String, nullable=False)  # Public explanation

    # Trade details
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Virtual coins staked
    shares_received: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ProphetBet(market_id={self.market_id}, side={self.side}, confidence={self.confidence})>"

    def to_dict(self) -> dict:
        """Convert Prophet bet to dictionary"""
        return {
            "id": str(self.id),
            "market_id": str(self.market_id),
            "side": self.side,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "amount": self.amount,
            "shares_received": self.shares_received,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

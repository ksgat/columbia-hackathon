"""
User model - represents users in the prediction market
"""
from sqlalchemy import String, Float, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid

from app.database import Base

class User(Base):
    """User model matching the database schema"""
    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Auth fields
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Clout/scoring system
    clout_score: Mapped[float] = mapped_column(Float, default=1000.0)
    clout_rank: Mapped[str] = mapped_column(String, default="Silver")

    # Stats
    total_bets_placed: Mapped[int] = mapped_column(Integer, default=0)
    total_bets_won: Mapped[int] = mapped_column(Integer, default=0)
    total_markets_created: Mapped[int] = mapped_column(Integer, default=0)
    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_best: Mapped[int] = mapped_column(Integer, default=0)

    # Balances
    balance_virtual: Mapped[float] = mapped_column(Float, default=1000.0)
    balance_cash: Mapped[float] = mapped_column(Float, default=0.0)

    # Wallet (future)
    wallet_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, display_name={self.display_name})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses"""
        return {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "clout_score": self.clout_score,
            "clout_rank": self.clout_rank,
            "total_bets_placed": self.total_bets_placed,
            "total_bets_won": self.total_bets_won,
            "total_markets_created": self.total_markets_created,
            "streak_current": self.streak_current,
            "streak_best": self.streak_best,
            "balance_virtual": self.balance_virtual,
            "balance_cash": self.balance_cash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_bets_placed == 0:
            return 0.0
        return (self.total_bets_won / self.total_bets_placed) * 100

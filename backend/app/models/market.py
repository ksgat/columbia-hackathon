"""
Market model - represents prediction markets
"""
from sqlalchemy import String, Float, Integer, TIMESTAMP, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid

from app.database import Base

class Market(Base):
    """Market model - yes/no prediction markets"""
    __tablename__ = "markets"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Relationships
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True  # NULL for Prophet-generated markets
    )

    # Market content
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Market type
    market_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="standard"
        # CHECK constraint in database
    )

    # Chained market fields
    parent_market_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("markets.id"),
        nullable=True,
        index=True
    )
    trigger_condition: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    chain_depth: Mapped[int] = mapped_column(Integer, default=0)

    # Derivative market fields
    reference_market_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("markets.id"),
        nullable=True,
        index=True
    )
    threshold_condition: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    threshold_deadline: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    # Odds and trading (LMSR state)
    odds_yes: Mapped[float] = mapped_column(Float, default=0.5)
    # odds_no is computed column in database: 1.0 - odds_yes
    total_pool: Mapped[float] = mapped_column(Float, default=0.0)
    total_yes_shares: Mapped[float] = mapped_column(Float, default=0.0)
    total_no_shares: Mapped[float] = mapped_column(Float, default=0.0)
    lmsr_b: Mapped[float] = mapped_column(Float, default=100.0)

    # Currency
    currency_mode: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="virtual"
        # CHECK constraint in database
    )

    # Status and resolution
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="active"
        # CHECK constraint in database
    )
    resolution_result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resolution_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    voting_deadline: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
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
        return f"<Market(id={self.id}, title={self.title}, status={self.status})>"

    def to_dict(self) -> dict:
        """Convert market to dictionary for API responses"""
        return {
            "id": str(self.id),
            "room_id": str(self.room_id),
            "creator_id": str(self.creator_id) if self.creator_id else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "market_type": self.market_type,
            "parent_market_id": str(self.parent_market_id) if self.parent_market_id else None,
            "trigger_condition": self.trigger_condition,
            "chain_depth": self.chain_depth,
            "odds_yes": self.odds_yes,
            "odds_no": 1.0 - self.odds_yes,
            "total_pool": self.total_pool,
            "total_yes_shares": self.total_yes_shares,
            "total_no_shares": self.total_no_shares,
            "lmsr_b": self.lmsr_b,
            "currency_mode": self.currency_mode,
            "status": self.status,
            "resolution_result": self.resolution_result,
            "resolution_method": self.resolution_method,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def odds_no(self) -> float:
        """Computed property for NO odds"""
        return 1.0 - self.odds_yes

    @property
    def is_active(self) -> bool:
        """Check if market is active for trading"""
        return self.status == "active"

    @property
    def is_resolved(self) -> bool:
        """Check if market is resolved"""
        return self.status == "resolved"

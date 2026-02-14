"""
ResolutionVote model - represents votes on market outcomes
"""
from sqlalchemy import String, Float, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.database import Base

class ResolutionVote(Base):
    """ResolutionVote model - community votes on market resolution"""
    __tablename__ = "resolution_votes"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Relationships
    market_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Vote
    vote: Mapped[str] = mapped_column(
        String,
        nullable=False
        # CHECK constraint in database
    )

    # Bond (for serious mode in cash rooms)
    bond_amount: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Unique constraint: one vote per user per market
    __table_args__ = (
        UniqueConstraint('market_id', 'user_id', name='uq_market_user_vote'),
    )

    def __repr__(self) -> str:
        return f"<ResolutionVote(market_id={self.market_id}, user_id={self.user_id}, vote={self.vote})>"

    def to_dict(self) -> dict:
        """Convert vote to dictionary"""
        return {
            "id": str(self.id),
            "market_id": str(self.market_id),
            "user_id": str(self.user_id),
            "vote": self.vote,
            "bond_amount": self.bond_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

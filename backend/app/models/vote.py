"""
Vote model for Prophecy - for market resolution voting
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Vote(Base):
    """Vote model - votes on market resolution"""
    __tablename__ = "resolution_votes"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Relations
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(String, ForeignKey("markets.id"), nullable=False, index=True)

    # Vote details
    outcome = Column(String, nullable=False)  # Which outcome they vote for
    reasoning = Column(Text, nullable=True)  # Optional explanation

    # Voting power (based on shares held, reputation, etc.)
    weight = Column(Float, default=1.0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User", back_populates="votes")
    # market = relationship("Market", back_populates="votes")

    def __repr__(self):
        return f"<Vote {self.outcome} by user {self.user_id}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "market_id": self.market_id,
            "outcome": self.outcome,
            "reasoning": self.reasoning,
            "weight": self.weight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

"""
User model for Prophecy
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class User(Base):
    """User model - represents a user in the prediction market"""
    __tablename__ = "users"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Auth fields
    email = Column(String, unique=True, nullable=False, index=True)

    # Profile
    display_name = Column(String, nullable=False)

    # Account type
    is_npc = Column(Boolean, default=False)

    # Game state
    tokens = Column(Float, default=1000.0)  # Starting balance

    # Stats
    total_trades = Column(Integer, default=0)
    successful_predictions = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (defined as strings to avoid circular imports)
    # trades = relationship("Trade", back_populates="user")
    # votes = relationship("Vote", back_populates="user")
    # memberships = relationship("Membership", back_populates="user")

    def __repr__(self):
        return f"<User {self.display_name} ({self.email})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "is_npc": self.is_npc,
            "tokens": self.tokens,
            "total_trades": self.total_trades,
            "successful_predictions": self.successful_predictions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

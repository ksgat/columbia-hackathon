"""
Market model for Prophecy
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
import enum


class MarketStatus(str, enum.Enum):
    """Market lifecycle states"""
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class MarketType(str, enum.Enum):
    """Market types"""
    BINARY = "binary"  # Yes/No
    MULTIPLE_CHOICE = "multiple_choice"  # Multiple options
    SCALAR = "scalar"  # Numeric prediction


class Market(Base):
    """Market model - a prediction market question"""
    __tablename__ = "markets"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic info
    question = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Relations
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False, index=True)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Market configuration
    market_type = Column(Enum(MarketType), default=MarketType.BINARY)
    status = Column(Enum(MarketStatus), default=MarketStatus.OPEN)

    # Options for multiple choice markets (JSON array)
    options = Column(JSON, nullable=True)  # ["Option A", "Option B", ...]

    # LMSR parameters
    liquidity = Column(Float, default=100.0)  # b parameter for LMSR

    # Current state (JSON object with shares for each outcome)
    # For binary: {"yes": 50, "no": 50}
    # For multiple choice: {"0": 33, "1": 33, "2": 34}
    shares = Column(JSON, default=dict)

    # Prices (calculated from shares, cached for performance)
    # For binary: {"yes": 0.5, "no": 0.5}
    prices = Column(JSON, default=dict)

    # Resolution
    resolution = Column(String, nullable=True)  # Which outcome won
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Deadlines
    close_time = Column(DateTime, nullable=True)
    resolve_time = Column(DateTime, nullable=True)

    # Stats
    total_volume = Column(Float, default=0.0)
    total_traders = Column(Integer, default=0)

    # AI insights
    prophet_prediction = Column(Float, nullable=True)  # Prophet's probability
    prophet_reasoning = Column(Text, nullable=True)
    prophet_last_update = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # room = relationship("Room", back_populates="markets")
    # creator = relationship("User", foreign_keys=[creator_id])
    # trades = relationship("Trade", back_populates="market")
    # votes = relationship("Vote", back_populates="market")

    def __repr__(self):
        return f"<Market {self.question[:50]}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "question": self.question,
            "description": self.description,
            "room_id": self.room_id,
            "creator_id": self.creator_id,
            "market_type": self.market_type.value if self.market_type else None,
            "status": self.status.value if self.status else None,
            "options": self.options,
            "liquidity": self.liquidity,
            "shares": self.shares,
            "prices": self.prices,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "total_volume": self.total_volume,
            "total_traders": self.total_traders,
            "prophet_prediction": self.prophet_prediction,
            "prophet_reasoning": self.prophet_reasoning,
            "prophet_last_update": self.prophet_last_update.isoformat() if self.prophet_last_update else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

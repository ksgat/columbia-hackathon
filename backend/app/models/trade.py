"""
Trade model for Prophecy
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
import enum


class TradeType(str, enum.Enum):
    """Trade types"""
    BUY = "buy"
    SELL = "sell"


class Trade(Base):
    """Trade model - records a market trade"""
    __tablename__ = "trades"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Relations
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(String, ForeignKey("markets.id"), nullable=False, index=True)

    # Trade details
    trade_type = Column(Enum(TradeType), nullable=False)
    outcome = Column(String, nullable=False)  # "yes"/"no" for binary, "0"/"1"/etc for multiple choice

    # Amounts
    shares = Column(Float, nullable=False)  # Number of shares traded
    price = Column(Float, nullable=False)  # Price per share at time of trade
    cost = Column(Float, nullable=False)  # Total cost/revenue (including LMSR slippage)

    # State before trade (for profit calculation)
    previous_shares = Column(Float, default=0.0)

    # Profit/loss tracking
    realized_profit = Column(Float, nullable=True)  # Only set when position is closed

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    # user = relationship("User", back_populates="trades")
    # market = relationship("Market", back_populates="trades")

    def __repr__(self):
        return f"<Trade {self.trade_type.value} {self.shares} @ {self.price}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "market_id": self.market_id,
            "trade_type": self.trade_type.value if self.trade_type else None,
            "outcome": self.outcome,
            "shares": self.shares,
            "price": self.price,
            "cost": self.cost,
            "previous_shares": self.previous_shares,
            "realized_profit": self.realized_profit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

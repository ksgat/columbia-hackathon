"""
Room model - represents prediction market rooms
"""
from sqlalchemy import String, Float, Integer, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
import uuid
import random
import string

from app.database import Base

class Room(Base):
    """Room model - private prediction market spaces for friend groups"""
    __tablename__ = "rooms"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Basic info
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    join_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False, index=True)

    # Creator
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Settings
    currency_mode: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="virtual",
        # CHECK constraint defined in database
    )
    min_bet: Mapped[float] = mapped_column(Float, default=10.0)
    max_bet: Mapped[float] = mapped_column(Float, default=500.0)
    rake_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Prophet settings
    prophet_persona: Mapped[str] = mapped_column(String, default="default")

    # Resolution settings
    resolution_window_hours: Mapped[int] = mapped_column(Integer, default=24)
    resolution_bond_required: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_bond_amount: Mapped[float] = mapped_column(Float, default=0.0)

    # Capacity
    max_members: Mapped[int] = mapped_column(Integer, default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

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
        return f"<Room(id={self.id}, name={self.name}, join_code={self.join_code})>"

    def to_dict(self) -> dict:
        """Convert room to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "join_code": self.join_code,
            "creator_id": str(self.creator_id),
            "currency_mode": self.currency_mode,
            "min_bet": self.min_bet,
            "max_bet": self.max_bet,
            "rake_percent": self.rake_percent,
            "prophet_persona": self.prophet_persona,
            "resolution_window_hours": self.resolution_window_hours,
            "max_members": self.max_members,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def generate_join_code(length: int = 6) -> str:
        """Generate a random alphanumeric join code"""
        chars = string.ascii_uppercase + string.digits
        # Exclude confusing characters
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        return ''.join(random.choice(chars) for _ in range(length))


class Membership(Base):
    """Membership model - links users to rooms with roles and balances"""
    __tablename__ = "memberships"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)

    # Role
    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="participant"
        # CHECK constraint defined in database
    )

    # Room-specific balances
    coins_virtual: Mapped[float] = mapped_column(Float, default=500.0)
    coins_earned_total: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamp
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Membership(user_id={self.user_id}, room_id={self.room_id}, role={self.role})>"

    def to_dict(self) -> dict:
        """Convert membership to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "room_id": str(self.room_id),
            "role": self.role,
            "coins_virtual": self.coins_virtual,
            "coins_earned_total": self.coins_earned_total,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

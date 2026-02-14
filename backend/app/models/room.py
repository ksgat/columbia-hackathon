"""
Room model for Prophecy
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
import enum


class RoomStatus(str, enum.Enum):
    """Room lifecycle states"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    LOCKED = "locked"


class Room(Base):
    """Room model - a prediction market room/space"""
    __tablename__ = "rooms"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String, unique=True, nullable=False, index=True)

    # Creator
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Settings
    is_public = Column(Boolean, default=True)
    status = Column(Enum(RoomStatus), default=RoomStatus.ACTIVE)
    max_members = Column(Integer, default=100)

    # Theming
    theme_color = Column(String, nullable=True)
    cover_image = Column(String, nullable=True)

    # Stats
    member_count = Column(Integer, default=0)
    market_count = Column(Integer, default=0)
    total_volume = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # creator = relationship("User", foreign_keys=[creator_id])
    # markets = relationship("Market", back_populates="room")
    # memberships = relationship("Membership", back_populates="room")

    def __repr__(self):
        return f"<Room {self.name} ({self.slug})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "slug": self.slug,
            "creator_id": self.creator_id,
            "is_public": self.is_public,
            "status": self.status.value if self.status else None,
            "max_members": self.max_members,
            "theme_color": self.theme_color,
            "cover_image": self.cover_image,
            "member_count": self.member_count,
            "market_count": self.market_count,
            "total_volume": self.total_volume,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

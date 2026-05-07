from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class Notice(Base, TimestampMixin):
    """School notice/announcement."""
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(String(2000), nullable=False)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    target_roles = Column(JSONB, nullable=True)  # List of target roles
    class_section_ids = Column(JSONB, nullable=True)  # List of specific class section IDs
    publish_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)

    # Relationships
    school = relationship("School", back_populates="notices")
    author = relationship("User")

    def __repr__(self) -> str:
        return f"<Notice(id={self.id}, title='{self.title}', is_published={self.is_published})>"


class Message(Base, TimestampMixin):
    """Direct message between users."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(200), nullable=True)
    body = Column(String(2000), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    sent_at = Column(Date, nullable=False, default=datetime.utcnow)
    read_at = Column(Date, nullable=True)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id})>"


class Announcement(Base, TimestampMixin):
    """General school announcement."""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(String(2000), nullable=False)
    target_audience = Column(String(50), nullable=True)  # all, students, teachers, parents
    publish_at = Column(Date, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    school = relationship("School", back_populates="announcements")
    created_by = relationship("User")

    def __repr__(self) -> str:
        return f"<Announcement(id={self.id}, title='{self.title}')>"

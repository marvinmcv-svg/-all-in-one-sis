from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class User(Base, TimestampMixin):
    """User account that authenticates to the system."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role", create_type=False), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    person = relationship("Person", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    ai_conversations = relationship("AIConversation", back_populates="user")
    ai_usage_logs = relationship("AIUsageLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"


class Person(Base, TimestampMixin):
    """Personal information linked to a user account."""
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=True)
    dob = Column(DateTime, nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)

    # Relationships
    user = relationship("User", back_populates="person")
    student = relationship("Student", back_populates="person", uselist=False, cascade="all, delete-orphan")
    teacher = relationship("Teacher", back_populates="person", uselist=False, cascade="all, delete-orphan")
    parent = relationship("Parent", back_populates="person", uselist=False, cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Person(id={self.id}, full_name='{self.full_name}')>"

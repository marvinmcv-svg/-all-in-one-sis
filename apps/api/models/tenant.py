from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """Multi-tenant organization (e.g., a school network or educational group)."""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    settings = Column(JSONB, nullable=True, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    schools = relationship("School", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class School(Base, TimestampMixin):
    """School belonging to a tenant."""
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    academic_year = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    logo_url = Column(String(500), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="schools")
    departments = relationship("Department", back_populates="school", cascade="all, delete-orphan")
    academic_terms = relationship("AcademicTerm", back_populates="school", cascade="all, delete-orphan")
    grade_levels = relationship("GradeLevel", back_populates="school", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    class_sections = relationship("ClassSection", back_populates="school", cascade="all, delete-orphan")
    fee_categories = relationship("FeeCategory", back_populates="school", cascade="all, delete-orphan")
    fee_structures = relationship("FeeStructure", back_populates="school", cascade="all, delete-orphan")
    grading_systems = relationship("GradingSystem", back_populates="school", cascade="all, delete-orphan")
    exam_types = relationship("ExamType", back_populates="school", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="school", cascade="all, delete-orphan")
    notices = relationship("Notice", back_populates="school", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="school", cascade="all, delete-orphan")
    timetable_templates = relationship("TimetableTemplate", back_populates="school", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<School(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"

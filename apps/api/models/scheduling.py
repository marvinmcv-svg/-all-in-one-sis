from sqlalchemy import Column, Integer, String, Time, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import time

from .base import Base, TimestampMixin


class Schedule(Base, TimestampMixin):
    """Class schedule for a specific period."""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    period_number = Column(Integer, nullable=False)
    room_number = Column(String(20), nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    class_section = relationship("ClassSection", back_populates="schedules")
    subject = relationship("Subject")
    teacher = relationship("Teacher")
    academic_term = relationship("AcademicTerm", back_populates="schedules")

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, class_section_id={self.class_section_id}, day={self.day_of_week}, period={self.period_number})>"


class TimetableTemplate(Base, TimestampMixin):
    """Template for timetable periods and days."""
    __tablename__ = "timetable_templates"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    periods = Column(JSONB, nullable=False)  # List of period definitions with start/end times
    days = Column(JSONB, nullable=False)  # List of working days

    # Relationships
    school = relationship("School", back_populates="timetable_templates")

    def __repr__(self) -> str:
        return f"<TimetableTemplate(id={self.id}, name='{self.name}')>"

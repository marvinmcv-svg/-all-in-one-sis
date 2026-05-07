from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class AttendanceStatus(str, enum.Enum):
    """Attendance status enumeration."""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class ExcuseStatus(str, enum.Enum):
    """Excuse status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AttendanceRecord(Base, TimestampMixin):
    """Daily attendance record for a student."""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    status = Column(SQLEnum(AttendanceStatus, name="attendance_status", create_type=False), nullable=False)
    excuse_id = Column(Integer, ForeignKey("attendance_excuses.id", ondelete="SET NULL"), nullable=True)
    marked_by_teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    class_section = relationship("ClassSection", back_populates="attendance_records")
    academic_term = relationship("AcademicTerm", back_populates="attendance_records")
    excuse = relationship("AttendanceExcuse", foreign_keys=[excuse_id])
    marked_by_teacher = relationship("Teacher", foreign_keys=[marked_by_teacher_id], back_populates="marked_attendances")

    def __repr__(self) -> str:
        return f"<AttendanceRecord(id={self.id}, student_id={self.student_id}, date={self.date}, status={self.status.value})>"


class AttendanceExcuse(Base, TimestampMixin):
    """Excuse request for student absence."""
    __tablename__ = "attendance_excuses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(500), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(ExcuseStatus, name="excuse_status", create_type=False), default=ExcuseStatus.PENDING, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="attendance_excuses")
    approved_by = relationship("Teacher")
    attendance_records = relationship("AttendanceRecord", back_populates="excuse")

    def __repr__(self) -> str:
        return f"<AttendanceExcuse(id={self.id}, student_id={self.student_id}, status={self.status.value})>"


class StaffAttendance(Base, TimestampMixin):
    """Attendance record for staff (teachers)."""
    __tablename__ = "staff_attendances"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # present, absent, late, etc.
    marked_by_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="staff_attendances")
    marked_by = relationship("Teacher", foreign_keys=[marked_by_id])

    def __repr__(self) -> str:
        return f"<StaffAttendance(id={self.id}, teacher_id={self.teacher_id}, date={self.date})>"

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class StudentStatus(str, enum.Enum):
    """Student enrollment status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    EXPELLED = "expelled"


class Student(Base, TimestampMixin):
    """Student record linked to a person."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    student_id = Column(String(50), unique=True, nullable=False, index=True)  # Admission number
    admission_date = Column(Date, nullable=False)
    status = Column(SQLEnum(StudentStatus, name="student_status", create_type=False), default=StudentStatus.ACTIVE, nullable=False)
    father_name = Column(String(200), nullable=True)
    mother_name = Column(String(200), nullable=True)
    guardian_id = Column(Integer, ForeignKey("parents.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    person = relationship("Person", back_populates="student")
    guardian = relationship("Parent", foreign_keys=[guardian_id])
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    attendance_excuses = relationship("AttendanceExcuse", back_populates="student", cascade="all, delete-orphan")
    exam_results = relationship("ExamResult", back_populates="student", cascade="all, delete-orphan")
    grade_reports = relationship("GradeReport", back_populates="student", cascade="all, delete-orphan")
    student_fees = relationship("StudentFee", back_populates="student", cascade="all, delete-orphan")
    course_enrollments = relationship("CourseEnrollment", back_populates="student", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="student", cascade="all, delete-orphan")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="student", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="student", cascade="all, delete-orphan")
    student_analytics = relationship("StudentAnalytics", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id='{self.student_id}', status={self.status.value})>"


class Enrollment(Base, TimestampMixin):
    """Student enrollment in a specific academic term and class section."""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    roll_number = Column(String(20), nullable=True)
    status = Column(String(20), default="active", nullable=False)

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    academic_term = relationship("AcademicTerm")
    grade_level = relationship("GradeLevel")
    class_section = relationship("ClassSection")

    def __repr__(self) -> str:
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, section_id={self.section_id})>"

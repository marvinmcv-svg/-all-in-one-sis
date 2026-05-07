from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Enum as SQLEnum, Time
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class SubjectType(str, enum.Enum):
    """Subject type enumeration."""
    THEORY = "theory"
    PRACTICAL = "practical"


class AcademicTerm(Base, TimestampMixin):
    """Academic term (e.g., Fall 2026, Semester 1)."""
    __tablename__ = "academic_terms"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)

    # Relationships
    school = relationship("School", back_populates="academic_terms")
    enrollments = relationship("Enrollment", back_populates="academic_term")
    schedules = relationship("Schedule", back_populates="academic_term")
    exams = relationship("Exam", back_populates="academic_term")
    grade_reports = relationship("GradeReport", back_populates="academic_term")
    class_sections = relationship("ClassSection", back_populates="academic_term")
    fee_structures = relationship("FeeStructure", back_populates="academic_term")
    teacher_assignments = relationship("TeacherAssignment", back_populates="academic_term")
    attendance_records = relationship("AttendanceRecord", back_populates="academic_term")
    student_analytics = relationship("StudentAnalytics", back_populates="academic_term")

    def __repr__(self) -> str:
        return f"<AcademicTerm(id={self.id}, name='{self.name}', is_current={self.is_current})>"


class GradeLevel(Base, TimestampMixin):
    """Grade level or year (e.g., Grade 1, Year 10)."""
    __tablename__ = "grade_levels"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    next_grade_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="SET NULL"), nullable=True)
    sequence = Column(Integer, nullable=False, default=0)

    # Relationships
    school = relationship("School", back_populates="grade_levels")
    next_grade = relationship("GradeLevel", remote_side=[id])
    enrollments = relationship("Enrollment", back_populates="grade_level")
    class_sections = relationship("ClassSection", back_populates="grade_level")

    def __repr__(self) -> str:
        return f"<GradeLevel(id={self.id}, name='{self.name}', code='{self.code}')>"


class Department(Base, TimestampMixin):
    """Academic department within a school."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    head_teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    school = relationship("School", back_populates="departments")
    head_teacher = relationship("Teacher", foreign_keys=[head_teacher_id], back_populates="department_head")
    teachers = relationship("Teacher", back_populates="department")

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}')>"


class Subject(Base, TimestampMixin):
    """Subject/course offered by a school."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    description = Column(String(500), nullable=True)
    credit_hours = Column(Integer, default=0, nullable=False)
    subject_type = Column(SQLEnum(SubjectType, name="subject_type", create_type=False), default=SubjectType.THEORY, nullable=False)

    # Relationships
    school = relationship("School", back_populates="subjects")
    teacher_assignments = relationship("TeacherAssignment", back_populates="subject")
    exams = relationship("Exam", back_populates="subject")
    class_subjects = relationship("ClassSubject", back_populates="subject")
    courses = relationship("Course", back_populates="subject")

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, name='{self.name}', code='{self.code}')>"


class ClassSection(Base, TimestampMixin):
    """A class section (e.g., Grade 10-A)."""
    __tablename__ = "class_sections"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    room_number = Column(String(20), nullable=True)
    capacity = Column(Integer, default=40, nullable=False)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    school = relationship("School", back_populates="class_sections")
    grade_level = relationship("GradeLevel", back_populates="class_sections")
    academic_term = relationship("AcademicTerm", back_populates="class_sections")
    enrollments = relationship("Enrollment", back_populates="class_section")
    schedules = relationship("Schedule", back_populates="class_section")
    teacher_assignments = relationship("TeacherAssignment", back_populates="class_section")
    class_subjects = relationship("ClassSubject", back_populates="class_section")
    exams = relationship("Exam", back_populates="class_section")
    attendance_records = relationship("AttendanceRecord", back_populates="class_section")

    def __repr__(self) -> str:
        return f"<ClassSection(id={self.id}, name='{self.name}', grade_level_id={self.grade_level_id})>"


class ClassSubject(Base, TimestampMixin):
    """Subject assigned to a class section."""
    __tablename__ = "class_subjects"

    id = Column(Integer, primary_key=True, index=True)
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_assignment_id = Column(Integer, ForeignKey("teacher_assignments.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    class_section = relationship("ClassSection", back_populates="class_subjects")
    subject = relationship("Subject", back_populates="class_subjects")
    teacher_assignment = relationship("TeacherAssignment", back_populates="class_subjects")

    def __repr__(self) -> str:
        return f"<ClassSubject(id={self.id}, class_section_id={self.class_section_id}, subject_id={self.subject_id})>"

from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class GradingSystem(Base, TimestampMixin):
    """Grading system (e.g., A-F, 1-10, GPA)."""
    __tablename__ = "grading_systems"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    grading_type = Column(String(50), nullable=False)  # letter, percentage, gpa, etc.
    is_default = Column(Boolean, default=False, nullable=False)

    # Relationships
    school = relationship("School", back_populates="grading_systems")
    grade_scales = relationship("GradeScale", back_populates="grading_system", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GradingSystem(id={self.id}, name='{self.name}', is_default={self.is_default})>"


class GradeScale(Base, TimestampMixin):
    """Individual grade within a grading system."""
    __tablename__ = "grade_scales"

    id = Column(Integer, primary_key=True, index=True)
    grading_system_id = Column(Integer, ForeignKey("grading_systems.id", ondelete="CASCADE"), nullable=False, index=True)
    letter = Column(String(5), nullable=False)
    min_percentage = Column(Numeric(5, 2), nullable=False)
    max_percentage = Column(Numeric(5, 2), nullable=False)
    grade_point = Column(Numeric(4, 2), nullable=False)

    # Relationships
    grading_system = relationship("GradingSystem", back_populates="grade_scales")
    exam_results = relationship("ExamResult", back_populates="grade")

    def __repr__(self) -> str:
        return f"<GradeScale(id={self.id}, letter='{self.letter}', min={self.min_percentage}, max={self.max_percentage})>"


class ExamType(Base, TimestampMixin):
    """Type of exam (e.g., FA, SA1, Final)."""
    __tablename__ = "exam_types"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    weight = Column(Numeric(5, 2), default=0, nullable=False)  # Weight in overall grade
    description = Column(String(500), nullable=True)

    # Relationships
    school = relationship("School", back_populates="exam_types")
    exams = relationship("Exam", back_populates="exam_type")

    def __repr__(self) -> str:
        return f"<ExamType(id={self.id}, name='{self.name}', weight={self.weight})>"


class Exam(Base, TimestampMixin):
    """Exam instance."""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_type_id = Column(Integer, ForeignKey("exam_types.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    max_marks = Column(Numeric(10, 2), nullable=False)
    exam_date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, default=60, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)

    # Relationships
    academic_term = relationship("AcademicTerm", back_populates="exams")
    class_section = relationship("ClassSection", back_populates="exams")
    subject = relationship("Subject", back_populates="exams")
    exam_type = relationship("ExamType", back_populates="exams")
    results = relationship("ExamResult", back_populates="exam", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Exam(id={self.id}, name='{self.name}', max_marks={self.max_marks})>"


class ExamResult(Base, TimestampMixin):
    """Result of an exam for a student."""
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    marks_obtained = Column(Numeric(10, 2), nullable=False)
    grade_id = Column(Integer, ForeignKey("grade_scales.id", ondelete="SET NULL"), nullable=True)
    remarks = Column(String(500), nullable=True)
    graded_by_teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    graded_at = Column(Date, nullable=True)

    # Relationships
    exam = relationship("Exam", back_populates="results")
    student = relationship("Student", back_populates="exam_results")
    grade = relationship("GradeScale", back_populates="exam_results")
    graded_by_teacher = relationship("Teacher", foreign_keys=[graded_by_teacher_id], back_populates="graded_exam_results")

    def __repr__(self) -> str:
        return f"<ExamResult(id={self.id}, exam_id={self.exam_id}, student_id={self.student_id}, marks={self.marks_obtained})>"


class GradeReport(Base, TimestampMixin):
    """Cumulative grade report for a student in an academic term."""
    __tablename__ = "grade_reports"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    cumulative_gpa = Column(Numeric(4, 2), nullable=True)
    rank = Column(Integer, nullable=True)
    teacher_remarks = Column(String(1000), nullable=True)
    finalized_at = Column(Date, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="grade_reports")
    academic_term = relationship("AcademicTerm", back_populates="grade_reports")

    def __repr__(self) -> str:
        return f"<GradeReport(id={self.id}, student_id={self.student_id}, gpa={self.cumulative_gpa})>"

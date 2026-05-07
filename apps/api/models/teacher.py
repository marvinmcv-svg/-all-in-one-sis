from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class Teacher(Base, TimestampMixin):
    """Teacher record linked to a person."""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    designation = Column(String(100), nullable=True)
    salary = Column(Integer, nullable=True)
    hire_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    person = relationship("Person", back_populates="teacher")
    department = relationship("Department", back_populates="teachers")
    assignments = relationship("TeacherAssignment", back_populates="teacher", cascade="all, delete-orphan")
    staff_attendances = relationship("StaffAttendance", back_populates="teacher", cascade="all, delete-orphan")
    taught_courses = relationship("Course", back_populates="teacher")
    marked_attendances = relationship("AttendanceRecord", foreign_keys="AttendanceRecord.marked_by_teacher_id", back_populates="marked_by_teacher")
    graded_exam_results = relationship("ExamResult", foreign_keys="ExamResult.graded_by_teacher_id", back_populates="graded_by_teacher")
    department_head = relationship("Department", foreign_keys="Department.head_teacher_id", back_populates="head_teacher")

    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, employee_id='{self.employee_id}', is_active={self.is_active})>"


class TeacherAssignment(Base, TimestampMixin):
    """Assignment of a teacher to a subject in a class section for an academic term."""
    __tablename__ = "teacher_assignments"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="assignments")
    subject = relationship("Subject")
    class_section = relationship("ClassSection")
    academic_term = relationship("AcademicTerm")
    class_subjects = relationship("ClassSubject", back_populates="teacher_assignment")

    def __repr__(self) -> str:
        return f"<TeacherAssignment(id={self.id}, teacher_id={self.teacher_id}, subject_id={self.subject_id})>"

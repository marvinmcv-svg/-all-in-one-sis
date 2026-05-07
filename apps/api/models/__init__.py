"""All SQLAlchemy models for the All-in-One SIS."""

from .base import Base, TimestampMixin
from .tenant import Tenant, School
from .person import User, Person, UserRole
from .student import Student, Enrollment, StudentStatus
from .teacher import Teacher, TeacherAssignment
from .parent import Parent
from .academic import (
    AcademicTerm,
    GradeLevel,
    Department,
    Subject,
    ClassSection,
    ClassSubject,
    SubjectType,
)
from .attendance import (
    AttendanceRecord,
    AttendanceExcuse,
    StaffAttendance,
    AttendanceStatus,
    ExcuseStatus,
)
from .gradebook import (
    GradingSystem,
    GradeScale,
    ExamType,
    Exam,
    ExamResult,
    GradeReport,
)
from .scheduling import Schedule, TimetableTemplate
from .fees import (
    FeeCategory,
    FeeStructure,
    StudentFee,
    Payment,
    FeePaymentStatus,
)
from .lms import (
    Course,
    CourseEnrollment,
    Chapter,
    Lesson,
    LessonProgress,
    Assignment,
    AssignmentSubmission,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizResponse,
    Certificate,
)
from .communication import Notice, Message, Announcement
from .ai import AIConversation, AIUsageLog, StudentAnalytics

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Tenant
    "Tenant",
    "School",
    # Person
    "User",
    "Person",
    "UserRole",
    # Student
    "Student",
    "Enrollment",
    "StudentStatus",
    # Teacher
    "Teacher",
    "TeacherAssignment",
    # Parent
    "Parent",
    # Academic
    "AcademicTerm",
    "GradeLevel",
    "Department",
    "Subject",
    "ClassSection",
    "ClassSubject",
    "SubjectType",
    # Attendance
    "AttendanceRecord",
    "AttendanceExcuse",
    "StaffAttendance",
    "AttendanceStatus",
    "ExcuseStatus",
    # Gradebook
    "GradingSystem",
    "GradeScale",
    "ExamType",
    "Exam",
    "ExamResult",
    "GradeReport",
    # Scheduling
    "Schedule",
    "TimetableTemplate",
    # Fees
    "FeeCategory",
    "FeeStructure",
    "StudentFee",
    "Payment",
    "FeePaymentStatus",
    # LMS
    "Course",
    "CourseEnrollment",
    "Chapter",
    "Lesson",
    "LessonProgress",
    "Assignment",
    "AssignmentSubmission",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "QuizResponse",
    "Certificate",
    # Communication
    "Notice",
    "Message",
    "Announcement",
    # AI
    "AIConversation",
    "AIUsageLog",
    "StudentAnalytics",
]

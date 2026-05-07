from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class AIConversation(Base, TimestampMixin):
    """AI conversation session."""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_type = Column(String(20), nullable=False)  # student, teacher, admin
    context = Column(String(100), nullable=True)  # context for the conversation (e.g., course_id, student_id)
    messages = Column(JSONB, nullable=False, default=list)  # List of message objects

    # Relationships
    user = relationship("User", back_populates="ai_conversations")

    def __repr__(self) -> str:
        return f"<AIConversation(id={self.id}, user_id={self.user_id}, user_type='{self.user_type}')>"


class AIUsageLog(Base, TimestampMixin):
    """Log of AI API usage."""
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module = Column(String(50), nullable=False)  # tutor, analytics, grading, etc.
    tokens_used = Column(Integer, default=0, nullable=False)
    response_time_ms = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", back_populates="ai_usage_logs")

    def __repr__(self) -> str:
        return f"<AIUsageLog(id={self.id}, user_id={self.user_id}, module='{self.module}')>"


class StudentAnalytics(Base, TimestampMixin):
    """Generated analytics for a student."""
    __tablename__ = "student_analytics"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_rate = Column(Integer, nullable=True)  # Percentage
    avg_marks = Column(Integer, nullable=True)  # Average marks percentage
    predicted_failure_risk = Column(Integer, nullable=True)  # Risk score 0-100
    engagement_score = Column(Integer, nullable=True)  # Score 0-100
    generated_at = Column(Date, nullable=False, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="student_analytics")
    academic_term = relationship("AcademicTerm", back_populates="student_analytics")

    def __repr__(self) -> str:
        return f"<StudentAnalytics(id={self.id}, student_id={self.student_id}, attendance_rate={self.attendance_rate})>"

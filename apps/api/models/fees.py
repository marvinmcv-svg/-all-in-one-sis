from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class FeePaymentStatus(str, enum.Enum):
    """Fee payment status."""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"


class FeeCategory(Base, TimestampMixin):
    """Category of fee (e.g., Tuition, Lab, Library)."""
    __tablename__ = "fee_categories"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)

    # Relationships
    school = relationship("School", back_populates="fee_categories")
    fee_structures = relationship("FeeStructure", back_populates="fee_category")

    def __repr__(self) -> str:
        return f"<FeeCategory(id={self.id}, name='{self.name}')>"


class FeeStructure(Base, TimestampMixin):
    """Fee structure for an academic term."""
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    late_fee_per_day = Column(Numeric(10, 2), default=0, nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    fee_category_id = Column(Integer, ForeignKey("fee_categories.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    school = relationship("School", back_populates="fee_structures")
    academic_term = relationship("AcademicTerm", back_populates="fee_structures")
    fee_category = relationship("FeeCategory", back_populates="fee_structures")
    student_fees = relationship("StudentFee", back_populates="fee_structure", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FeeStructure(id={self.id}, name='{self.name}', amount={self.amount})>"


class StudentFee(Base, TimestampMixin):
    """Fee assigned to a student."""
    __tablename__ = "student_fees"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)  # Original amount
    discount_amount = Column(Numeric(12, 2), default=0, nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0, nullable=False)
    status = Column(SQLEnum(FeePaymentStatus, name="fee_payment_status", create_type=False), default=FeePaymentStatus.PENDING, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(Date, nullable=True)
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(100), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="student_fees")
    fee_structure = relationship("FeeStructure", back_populates="student_fees")
    payments = relationship("Payment", back_populates="student_fee", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<StudentFee(id={self.id}, student_id={self.student_id}, status={self.status.value})>"


class Payment(Base, TimestampMixin):
    """Individual payment for a student fee."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    student_fee_id = Column(Integer, ForeignKey("student_fees.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=True)  # cash, card, online, etc.
    transaction_ref = Column(String(100), nullable=True)
    received_by_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    collected_at = Column(Date, nullable=False)

    # Relationships
    student_fee = relationship("StudentFee", back_populates="payments")
    received_by = relationship("Teacher")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, student_fee_id={self.student_fee_id}, amount={self.amount})>"

"""Fees router - Fee management API for the SIS."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel

from ..database import get_db
from ..models.fees import (
    FeeCategory,
    FeeStructure,
    StudentFee,
    Payment,
    FeePaymentStatus,
)
from ..models.student import Student, Enrollment
from ..models.person import Person, User, UserRole
from ..models.academic import AcademicTerm, ClassSection
from ..core.deps import get_current_user

router = APIRouter(prefix="/fees", tags=["Fees"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class FeeCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class FeeCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}


class FeeStructureCreate(BaseModel):
    name: str
    academic_term_id: int
    amount: float
    due_date: date
    late_fee_per_day: Optional[float] = 0
    is_mandatory: bool = True
    fee_category_id: Optional[int] = None


class FeeStructureUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[date] = None
    late_fee_per_day: Optional[float] = None
    is_mandatory: Optional[bool] = None
    fee_category_id: Optional[int] = None


class FeeStructureInfo(BaseModel):
    id: int
    name: str
    amount: float
    due_date: date

    model_config = {"from_attributes": True}


class FeeStructureResponse(BaseModel):
    id: int
    name: str
    academic_term_id: int
    academic_term_name: Optional[str] = None
    amount: float
    due_date: date
    late_fee_per_day: float
    is_mandatory: bool
    fee_category_id: Optional[int]
    fee_category_name: Optional[str] = None

    model_config = {"from_attributes": True}


class FeeStructureAssign(BaseModel):
    student_ids: List[int]
    discount_amount: Optional[float] = 0
    discount_reason: Optional[str] = None


class PaymentCreate(BaseModel):
    student_fee_id: int
    amount: float
    payment_method: str = "cash"  # cash, card, bank_transfer, online
    transaction_ref: Optional[str] = None


class PaymentInfo(BaseModel):
    id: int
    amount: float
    payment_method: str
    transaction_ref: Optional[str]
    collected_at: date
    received_by: str

    model_config = {"from_attributes": True}


class StudentFeeResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    fee_structure: FeeStructureInfo
    amount: float
    discount_amount: float
    paid_amount: float
    balance: float
    status: str  # pending, partial, paid
    due_date: date
    payments: List[PaymentInfo]

    model_config = {"from_attributes": True}


class StudentOutstanding(BaseModel):
    student_id: int
    student_name: str
    class_section: str
    total_fee: float
    paid: float
    outstanding: float


class OutstandingReport(BaseModel):
    total_students: int
    total_outstanding: float
    students: List[StudentOutstanding]


class CollectionReport(BaseModel):
    total_amount: float
    total_transactions: int
    payments: List[PaymentInfo]


class ClassFeeReport(BaseModel):
    class_section: str
    total_students: int
    total_fee: float
    total_paid: float
    total_outstanding: float
    students: List[StudentOutstanding]


# ============================================================================
# Helper Functions
# ============================================================================


def check_admin_access(current_user: User) -> bool:
    """Check if user is admin."""
    return current_user.role == UserRole.ADMIN


def check_fee_access(current_user: User, student_id: int) -> bool:
    """Check if user has access to fee data for a student."""
    if current_user.role == UserRole.ADMIN:
        return True
    if current_user.role == UserRole.STUDENT and current_user.person and current_user.person.student:
        return current_user.person.student.id == student_id
    return False


async def get_student_with_enrollment(
    db: AsyncSession, student_id: int
) -> Optional[Student]:
    """Fetch student with person and enrollment info."""
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.person),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.academic_term),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.class_section),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.grade_level),
        )
    )
    return result.scalar_one_or_none()


async def get_student_fee_by_id(
    db: AsyncSession, fee_id: int
) -> Optional[StudentFee]:
    """Fetch a student fee with all relationships."""
    result = await db.execute(
        select(StudentFee)
        .where(StudentFee.id == fee_id)
        .options(
            selectinload(StudentFee.student)
            .selectinload(Student.person),
            selectinload(StudentFee.fee_structure)
            .selectinload(FeeStructure.academic_term),
            selectinload(StudentFee.payments)
            .selectinload(Payment.received_by)
            .selectinload(Payment.received_by.person),
        )
    )
    return result.scalar_one_or_none()


def build_payment_info(payment: Payment) -> PaymentInfo:
    """Build PaymentInfo from Payment model."""
    received_by_name = ""
    if payment.received_by and payment.received_by.person:
        received_by_name = payment.received_by.person.full_name
    return PaymentInfo(
        id=payment.id,
        amount=float(payment.amount),
        payment_method=payment.payment_method or "cash",
        transaction_ref=payment.transaction_ref,
        collected_at=payment.collected_at,
        received_by=received_by_name,
    )


def build_student_fee_response(student_fee: StudentFee) -> StudentFeeResponse:
    """Build StudentFeeResponse from StudentFee model."""
    student_name = ""
    if student_fee.student and student_fee.student.person:
        student_name = student_fee.student.person.full_name

    fee_structure = student_fee.fee_structure
    fee_structure_info = FeeStructureInfo(
        id=fee_structure.id,
        name=fee_structure.name,
        amount=float(fee_structure.amount),
        due_date=fee_structure.due_date,
    )

    balance = float(student_fee.amount) - float(student_fee.discount_amount) - float(student_fee.paid_amount)

    payments = [build_payment_info(p) for p in student_fee.payments] if student_fee.payments else []

    return StudentFeeResponse(
        id=student_fee.id,
        student_id=student_fee.student_id,
        student_name=student_name,
        fee_structure=fee_structure_info,
        amount=float(student_fee.amount),
        discount_amount=float(student_fee.discount_amount),
        paid_amount=float(student_fee.paid_amount),
        balance=balance,
        status=student_fee.status.value if isinstance(student_fee.status, FeePaymentStatus) else student_fee.status,
        due_date=student_fee.due_date,
        payments=payments,
    )


# ============================================================================
# Fee Categories Endpoints
# ============================================================================


@router.get("/categories", response_model=List[FeeCategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all fee categories.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list fee categories",
        )

    result = await db.execute(select(FeeCategory).order_by(FeeCategory.name))
    categories = result.scalars().all()

    return [
        FeeCategoryResponse(
            id=c.id,
            name=c.name,
            description=c.description,
        )
        for c in categories
    ]


@router.post("/categories", response_model=FeeCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: FeeCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new fee category.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create fee categories",
        )

    # Check if category with same name exists
    result = await db.execute(
        select(FeeCategory).where(FeeCategory.name == category_data.name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fee category with this name already exists",
        )

    category = FeeCategory(
        name=category_data.name,
        description=category_data.description,
        school_id=current_user.tenant_id,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return FeeCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
    )


@router.put("/categories/{category_id}", response_model=FeeCategoryResponse)
async def update_category(
    category_id: int,
    category_data: FeeCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a fee category.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update fee categories",
        )

    result = await db.execute(
        select(FeeCategory).where(FeeCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee category with id {category_id} not found",
        )

    # Check if new name conflicts with existing category
    if category_data.name != category.name:
        result = await db.execute(
            select(FeeCategory).where(
                and_(
                    FeeCategory.name == category_data.name,
                    FeeCategory.id != category_id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fee category with this name already exists",
            )

    category.name = category_data.name
    category.description = category_data.description

    await db.commit()
    await db.refresh(category)

    return FeeCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a fee category.

    Requires admin authentication.
    Note: Fee structures using this category will have their category_id set to NULL.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete fee categories",
        )

    result = await db.execute(
        select(FeeCategory).where(FeeCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee category with id {category_id} not found",
        )

    await db.delete(category)
    await db.commit()


# ============================================================================
# Fee Structures Endpoints
# ============================================================================


@router.get("/structures", response_model=List[FeeStructureResponse])
async def list_structures(
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all fee structures.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list fee structures",
        )

    query = select(FeeStructure).options(
        selectinload(FeeStructure.academic_term),
        selectinload(FeeStructure.fee_category),
    )

    if academic_term_id:
        query = query.where(FeeStructure.academic_term_id == academic_term_id)

    query = query.order_by(FeeStructure.due_date.desc())

    result = await db.execute(query)
    structures = result.scalars().all()

    return [
        FeeStructureResponse(
            id=s.id,
            name=s.name,
            academic_term_id=s.academic_term_id,
            academic_term_name=s.academic_term.name if s.academic_term else None,
            amount=float(s.amount),
            due_date=s.due_date,
            late_fee_per_day=float(s.late_fee_per_day) if s.late_fee_per_day else 0,
            is_mandatory=s.is_mandatory,
            fee_category_id=s.fee_category_id,
            fee_category_name=s.fee_category.name if s.fee_category else None,
        )
        for s in structures
    ]


@router.post("/structures", response_model=FeeStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_structure(
    structure_data: FeeStructureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new fee structure.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create fee structures",
        )

    # Validate academic term exists
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == structure_data.academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    if not academic_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic term with id {structure_data.academic_term_id} not found",
        )

    # Validate fee category if provided
    if structure_data.fee_category_id:
        result = await db.execute(
            select(FeeCategory).where(FeeCategory.id == structure_data.fee_category_id)
        )
        fee_category = result.scalar_one_or_none()
        if not fee_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fee category with id {structure_data.fee_category_id} not found",
            )

    structure = FeeStructure(
        name=structure_data.name,
        academic_term_id=structure_data.academic_term_id,
        amount=structure_data.amount,
        due_date=structure_data.due_date,
        late_fee_per_day=structure_data.late_fee_per_day or 0,
        is_mandatory=structure_data.is_mandatory,
        fee_category_id=structure_data.fee_category_id,
        school_id=current_user.tenant_id,
    )
    db.add(structure)
    await db.commit()
    await db.refresh(structure)

    # Load relationships
    result = await db.execute(
        select(FeeStructure)
        .where(FeeStructure.id == structure.id)
        .options(
            selectinload(FeeStructure.academic_term),
            selectinload(FeeStructure.fee_category),
        )
    )
    structure = result.scalar_one()

    return FeeStructureResponse(
        id=structure.id,
        name=structure.name,
        academic_term_id=structure.academic_term_id,
        academic_term_name=structure.academic_term.name if structure.academic_term else None,
        amount=float(structure.amount),
        due_date=structure.due_date,
        late_fee_per_day=float(structure.late_fee_per_day) if structure.late_fee_per_day else 0,
        is_mandatory=structure.is_mandatory,
        fee_category_id=structure.fee_category_id,
        fee_category_name=structure.fee_category.name if structure.fee_category else None,
    )


@router.get("/structures/{structure_id}", response_model=FeeStructureResponse)
async def get_structure(
    structure_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a fee structure by ID.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view fee structures",
        )

    result = await db.execute(
        select(FeeStructure)
        .where(FeeStructure.id == structure_id)
        .options(
            selectinload(FeeStructure.academic_term),
            selectinload(FeeStructure.fee_category),
        )
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with id {structure_id} not found",
        )

    return FeeStructureResponse(
        id=structure.id,
        name=structure.name,
        academic_term_id=structure.academic_term_id,
        academic_term_name=structure.academic_term.name if structure.academic_term else None,
        amount=float(structure.amount),
        due_date=structure.due_date,
        late_fee_per_day=float(structure.late_fee_per_day) if structure.late_fee_per_day else 0,
        is_mandatory=structure.is_mandatory,
        fee_category_id=structure.fee_category_id,
        fee_category_name=structure.fee_category.name if structure.fee_category else None,
    )


@router.put("/structures/{structure_id}", response_model=FeeStructureResponse)
async def update_structure(
    structure_id: int,
    structure_data: FeeStructureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a fee structure.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update fee structures",
        )

    result = await db.execute(
        select(FeeStructure)
        .where(FeeStructure.id == structure_id)
        .options(
            selectinload(FeeStructure.academic_term),
            selectinload(FeeStructure.fee_category),
        )
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with id {structure_id} not found",
        )

    # Validate fee category if being updated
    if structure_data.fee_category_id is not None:
        if structure_data.fee_category_id > 0:
            result = await db.execute(
                select(FeeCategory).where(FeeCategory.id == structure_data.fee_category_id)
            )
            fee_category = result.scalar_one_or_none()
            if not fee_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Fee category with id {structure_data.fee_category_id} not found",
                )
        # If 0 or None, we're clearing it

    # Update fields
    if structure_data.name is not None:
        structure.name = structure_data.name
    if structure_data.amount is not None:
        structure.amount = structure_data.amount
    if structure_data.due_date is not None:
        structure.due_date = structure_data.due_date
    if structure_data.late_fee_per_day is not None:
        structure.late_fee_per_day = structure_data.late_fee_per_day
    if structure_data.is_mandatory is not None:
        structure.is_mandatory = structure_data.is_mandatory
    if structure_data.fee_category_id is not None:
        structure.fee_category_id = structure_data.fee_category_id if structure_data.fee_category_id > 0 else None

    await db.commit()
    await db.refresh(structure)

    return FeeStructureResponse(
        id=structure.id,
        name=structure.name,
        academic_term_id=structure.academic_term_id,
        academic_term_name=structure.academic_term.name if structure.academic_term else None,
        amount=float(structure.amount),
        due_date=structure.due_date,
        late_fee_per_day=float(structure.late_fee_per_day) if structure.late_fee_per_day else 0,
        is_mandatory=structure.is_mandatory,
        fee_category_id=structure.fee_category_id,
        fee_category_name=structure.fee_category.name if structure.fee_category else None,
    )


@router.delete("/structures/{structure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_structure(
    structure_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a fee structure.

    Requires admin authentication.
    Note: This will also delete all associated student fees.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete fee structures",
        )

    result = await db.execute(
        select(FeeStructure).where(FeeStructure.id == structure_id)
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with id {structure_id} not found",
        )

    await db.delete(structure)
    await db.commit()


@router.post("/structures/{structure_id}/assign", status_code=status.HTTP_201_CREATED)
async def assign_structure_to_students(
    structure_id: int,
    assign_data: FeeStructureAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a fee structure to students.

    Creates StudentFee records for each student. If a StudentFee already exists
    for the same student and structure, it will be skipped.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign fee structures",
        )

    # Get the fee structure
    result = await db.execute(
        select(FeeStructure).where(FeeStructure.id == structure_id)
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with id {structure_id} not found",
        )

    assigned_count = 0
    skipped_count = 0
    errors = []

    for student_id in assign_data.student_ids:
        # Check if student exists
        student = await get_student_with_enrollment(db, student_id)
        if not student:
            errors.append(f"Student with id {student_id} not found")
            continue

        # Check if already assigned
        result = await db.execute(
            select(StudentFee).where(
                and_(
                    StudentFee.student_id == student_id,
                    StudentFee.fee_structure_id == structure_id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            skipped_count += 1
            continue

        # Create student fee
        student_fee = StudentFee(
            student_id=student_id,
            fee_structure_id=structure_id,
            amount=structure.amount,
            discount_amount=assign_data.discount_amount or 0,
            paid_amount=0,
            status=FeePaymentStatus.PENDING,
            due_date=structure.due_date,
        )
        db.add(student_fee)
        assigned_count += 1

    await db.commit()

    return {
        "assigned": assigned_count,
        "skipped": skipped_count,
        "errors": errors,
    }


# ============================================================================
# Student Fees Endpoints
# ============================================================================


@router.get("/student/{student_id}", response_model=List[StudentFeeResponse])
async def get_student_fees(
    student_id: int,
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, partial, paid)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all fees for a student.

    Access:
    - Admins can view any student's fees
    - Students can view only their own fees
    """
    if not check_fee_access(current_user, student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this student's fees",
        )

    # Verify student exists
    student = await get_student_with_enrollment(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found",
        )

    query = (
        select(StudentFee)
        .where(StudentFee.student_id == student_id)
        .options(
            selectinload(StudentFee.student)
            .selectinload(Student.person),
            selectinload(StudentFee.fee_structure)
            .selectinload(FeeStructure.academic_term),
            selectinload(StudentFee.payments)
            .selectinload(Payment.received_by)
            .selectinload(Payment.received_by.person),
        )
    )

    if academic_term_id:
        query = query.join(StudentFee.fee_structure).where(
            FeeStructure.academic_term_id == academic_term_id
        )

    if status_filter:
        try:
            status_enum = FeePaymentStatus(status_filter.lower())
            query = query.where(StudentFee.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Must be one of: pending, partial, paid",
            )

    query = query.order_by(StudentFee.due_date.desc())

    result = await db.execute(query)
    student_fees = result.scalars().all()

    return [build_student_fee_response(sf) for sf in student_fees]


@router.post("/pay", response_model=StudentFeeResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record a payment for a student fee.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can record payments",
        )

    # Get the student fee
    student_fee = await get_student_fee_by_id(db, payment_data.student_fee_id)
    if not student_fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student fee with id {payment_data.student_fee_id} not found",
        )

    # Calculate the balance
    total_payable = float(student_fee.amount) - float(student_fee.discount_amount)
    remaining_balance = total_payable - float(student_fee.paid_amount)

    if payment_data.amount > remaining_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount ({payment_data.amount}) exceeds remaining balance ({remaining_balance})",
        )

    # Validate payment method
    valid_methods = ["cash", "card", "bank_transfer", "online"]
    if payment_data.payment_method not in valid_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method. Must be one of: {', '.join(valid_methods)}",
        )

    # Create payment record
    payment = Payment(
        student_fee_id=payment_data.student_fee_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        transaction_ref=payment_data.transaction_ref,
        received_by_id=current_user.person.teacher.id if current_user.person and current_user.person.teacher else None,
        collected_at=datetime.now().date(),
    )
    db.add(payment)

    # Update student fee
    student_fee.paid_amount = float(student_fee.paid_amount) + payment_data.amount

    # Update status
    new_balance = total_payable - student_fee.paid_amount
    if new_balance <= 0:
        student_fee.status = FeePaymentStatus.PAID
        student_fee.paid_at = datetime.now().date()
        student_fee.payment_method = payment_data.payment_method
        student_fee.transaction_id = payment_data.transaction_ref
    else:
        student_fee.status = FeePaymentStatus.PARTIAL

    await db.commit()

    # Refresh to get updated data
    await db.refresh(student_fee)
    result = await db.execute(
        select(StudentFee)
        .where(StudentFee.id == student_fee.id)
        .options(
            selectinload(StudentFee.student)
            .selectinload(Student.person),
            selectinload(StudentFee.fee_structure)
            .selectinload(FeeStructure.academic_term),
            selectinload(StudentFee.payments)
            .selectinload(Payment.received_by)
            .selectinload(Payment.received_by.person),
        )
    )
    student_fee = result.scalar_one()

    return build_student_fee_response(student_fee)


@router.get("/receipt/{payment_id}")
async def get_payment_receipt(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a payment receipt.

    Access:
    - Admins can view any receipt
    - Students can view receipts for their own payments
    """
    # Get payment with student fee info
    result = await db.execute(
        select(Payment)
        .where(Payment.id == payment_id)
        .options(
            selectinload(Payment.student_fee)
            .selectinload(StudentFee.student)
            .selectinload(Student.person),
            selectinload(Payment.student_fee)
            .selectinload(StudentFee.fee_structure)
            .selectinload(FeeStructure.academic_term),
            selectinload(Payment.received_by)
            .selectinload(Payment.received_by.person),
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with id {payment_id} not found",
        )

    # Check access
    student_fee = payment.student_fee
    if not check_fee_access(current_user, student_fee.student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this receipt",
        )

    # Build receipt
    student_name = ""
    if student_fee.student and student_fee.student.person:
        student_name = student_fee.student.person.full_name

    received_by_name = ""
    if payment.received_by and payment.received_by.person:
        received_by_name = payment.received_by.person.full_name

    fee_structure = student_fee.fee_structure
    academic_term_name = fee_structure.academic_term.name if fee_structure.academic_term else ""

    return {
        "receipt_number": f"RCP-{payment.id:06d}",
        "payment_id": payment.id,
        "student_id": student_fee.student_id,
        "student_name": student_name,
        "fee_structure_name": fee_structure.name,
        "academic_term": academic_term_name,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "transaction_ref": payment.transaction_ref,
        "collected_at": payment.collected_at,
        "received_by": received_by_name,
        "fee_status": student_fee.status.value if isinstance(student_fee.status, FeePaymentStatus) else student_fee.status,
        "total_fee": float(student_fee.amount),
        "discount": float(student_fee.discount_amount),
        "paid_amount": float(student_fee.paid_amount),
        "balance": float(student_fee.amount) - float(student_fee.discount_amount) - float(student_fee.paid_amount),
    }


# ============================================================================
# Reports Endpoints
# ============================================================================


@router.get("/reports/outstanding", response_model=OutstandingReport)
async def get_outstanding_report(
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    class_section_id: Optional[int] = Query(None, description="Filter by class section"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get outstanding fees report.

    Shows all students with unpaid or partially paid fees.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view outstanding reports",
        )

    # Build query for student fees with pending or partial status
    query = (
        select(StudentFee)
        .where(
            or_(
                StudentFee.status == FeePaymentStatus.PENDING,
                StudentFee.status == FeePaymentStatus.PARTIAL,
            )
        )
        .options(
            selectinload(StudentFee.student)
            .selectinload(Student.person),
            selectinload(StudentFee.student)
            .selectinload(Student.enrollments)
            .selectinload(Enrollment.class_section)
            .selectinload(ClassSection.grade_level),
            selectinload(StudentFee.fee_structure)
            .selectinload(FeeStructure.academic_term),
        )
    )

    if academic_term_id:
        query = query.join(StudentFee.fee_structure).where(
            FeeStructure.academic_term_id == academic_term_id
        )

    result = await db.execute(query)
    student_fees = result.scalars().all()

    # Group by student and calculate totals
    student_totals = {}
    for sf in student_fees:
        student_id = sf.student_id
        if student_id not in student_totals:
            student_name = sf.student.person.full_name if sf.student and sf.student.person else "Unknown"

            # Get current class section
            class_section = ""
            if sf.student and sf.student.enrollments:
                for enrollment in sf.student.enrollments:
                    if enrollment.class_section:
                        grade_level = enrollment.class_section.grade_level.name if enrollment.class_section.grade_level else ""
                        class_section = f"{grade_level}-{enrollment.class_section.name}"
                        break

            student_totals[student_id] = {
                "student_id": student_id,
                "student_name": student_name,
                "class_section": class_section,
                "total_fee": 0.0,
                "paid": 0.0,
                "outstanding": 0.0,
            }

        total_fee = float(sf.amount) - float(sf.discount_amount)
        paid = float(sf.paid_amount)
        outstanding = total_fee - paid

        student_totals[student_id]["total_fee"] += total_fee
        student_totals[student_id]["paid"] += paid
        student_totals[student_id]["outstanding"] += outstanding

    # Apply class section filter if specified
    students_list = list(student_totals.values())
    if class_section_id:
        students_list = [
            s for s in students_list
            if any(
                sf.student_id == s["student_id"]
                and sf.student
                and sf.student.enrollments
                and any(
                    e.class_section_id == class_section_id
                    for e in sf.student.enrollments
                    if e.class_section_id == class_section_id
                )
                for sf in student_fees
            )
        ]

    total_outstanding = sum(s["outstanding"] for s in students_list)

    return OutstandingReport(
        total_students=len(students_list),
        total_outstanding=total_outstanding,
        students=[
            StudentOutstanding(
                student_id=s["student_id"],
                student_name=s["student_name"],
                class_section=s["class_section"],
                total_fee=s["total_fee"],
                paid=s["paid"],
                outstanding=s["outstanding"],
            )
            for s in students_list
        ],
    )


@router.get("/reports/collection", response_model=CollectionReport)
async def get_collection_report(
    start_date: date = Query(..., description="Start date for the report"),
    end_date: date = Query(..., description="End date for the report"),
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get collection report.

    Shows all payments received within a date range.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view collection reports",
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date",
        )

    query = (
        select(Payment)
        .where(
            and_(
                Payment.collected_at >= start_date,
                Payment.collected_at <= end_date,
            )
        )
        .options(
            selectinload(Payment.received_by)
            .selectinload(Payment.received_by.person),
            selectinload(Payment.student_fee)
            .selectinload(StudentFee.fee_structure),
        )
    )

    if academic_term_id:
        query = query.join(Payment.student_fee).where(
            StudentFee.fee_structure_id.in_(
                select(FeeStructure.id).where(FeeStructure.academic_term_id == academic_term_id)
            )
        )

    if payment_method:
        query = query.where(Payment.payment_method == payment_method)

    query = query.order_by(Payment.collected_at.desc())

    result = await db.execute(query)
    payments = result.scalars().all()

    total_amount = sum(float(p.amount) for p in payments)

    return CollectionReport(
        total_amount=total_amount,
        total_transactions=len(payments),
        payments=[build_payment_info(p) for p in payments],
    )


@router.get("/reports/class/{class_section_id}", response_model=ClassFeeReport)
async def get_class_fee_report(
    class_section_id: int,
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get fee report for a specific class section.

    Requires admin authentication.
    """
    if not check_admin_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view class fee reports",
        )

    # Get class section info
    result = await db.execute(
        select(ClassSection)
        .where(ClassSection.id == class_section_id)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term),
        )
    )
    class_section = result.scalar_one_or_none()
    if not class_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class section with id {class_section_id} not found",
        )

    class_section_name = f"{class_section.grade_level.name}-{class_section.name}" if class_section.grade_level else class_section.name

    # Get enrollments for this class
    enrollment_query = (
        select(Enrollment)
        .where(Enrollment.class_section_id == class_section_id)
        .options(selectinload(Enrollment.academic_term))
    )

    if academic_term_id:
        enrollment_query = enrollment_query.where(Enrollment.academic_term_id == academic_term_id)

    enrollment_result = await db.execute(enrollment_query)
    enrollments = enrollment_result.scalars().all()

    student_ids = [e.student_id for e in enrollments]

    if not student_ids:
        return ClassFeeReport(
            class_section=class_section_name,
            total_students=0,
            total_fee=0.0,
            total_paid=0.0,
            total_outstanding=0.0,
            students=[],
        )

    # Get student fees for these students
    fees_query = (
        select(StudentFee)
        .where(StudentFee.student_id.in_(student_ids))
        .options(
            selectinload(StudentFee.student)
            .selectinload(Student.person),
            selectinload(StudentFee.fee_structure),
        )
    )

    if academic_term_id:
        fees_query = fees_query.join(StudentFee.fee_structure).where(
            FeeStructure.academic_term_id == academic_term_id
        )

    fees_result = await db.execute(fees_query)
    student_fees = fees_result.scalars().all()

    # Calculate totals per student
    student_totals = {}
    for sf in student_fees:
        student_id = sf.student_id
        if student_id not in student_totals:
            student_name = sf.student.person.full_name if sf.student and sf.student.person else "Unknown"
            student_totals[student_id] = {
                "student_id": student_id,
                "student_name": student_name,
                "total_fee": 0.0,
                "paid": 0.0,
                "outstanding": 0.0,
            }

        total_fee = float(sf.amount) - float(sf.discount_amount)
        paid = float(sf.paid_amount)
        outstanding = total_fee - paid

        student_totals[student_id]["total_fee"] += total_fee
        student_totals[student_id]["paid"] += paid
        student_totals[student_id]["outstanding"] += outstanding

    students_list = list(student_totals.values())
    total_fee_sum = sum(s["total_fee"] for s in students_list)
    total_paid_sum = sum(s["paid"] for s in students_list)
    total_outstanding_sum = sum(s["outstanding"] for s in students_list)

    return ClassFeeReport(
        class_section=class_section_name,
        total_students=len(students_list),
        total_fee=total_fee_sum,
        total_paid=total_paid_sum,
        total_outstanding=total_outstanding_sum,
        students=[
            StudentOutstanding(
                student_id=s["student_id"],
                student_name=s["student_name"],
                class_section=class_section_name,
                total_fee=s["total_fee"],
                paid=s["paid"],
                outstanding=s["outstanding"],
            )
            for s in students_list
        ],
    )

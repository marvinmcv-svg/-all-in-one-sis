"""Grades router - Comprehensive gradebook API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel

from ..database import get_db
from ..models.gradebook import GradingSystem, GradeScale, ExamType, Exam, ExamResult, GradeReport
from ..models.academic import AcademicTerm, ClassSection, Subject, GradeLevel
from ..models.student import Student, Enrollment
from ..models.teacher import Teacher, TeacherAssignment
from ..models.person import Person
from ..core.deps import get_current_user, get_current_admin, require_roles

router = APIRouter(prefix="/grades", tags=["Grades"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

class GradeScaleCreate(BaseModel):
    letter: str
    min_percentage: float
    max_percentage: float
    grade_point: Optional[float] = None


class GradeScaleResponse(BaseModel):
    id: int
    letter: str
    min_percentage: float
    max_percentage: float
    grade_point: Optional[float]

    class Config:
        from_attributes = True


class GradingSystemCreate(BaseModel):
    name: str
    grading_type: str = "letter"  # letter, percentage, gpa
    is_default: bool = False
    scales: List[GradeScaleCreate] = []


class GradingSystemUpdate(BaseModel):
    name: Optional[str] = None
    grading_type: Optional[str] = None
    is_default: Optional[bool] = None


class GradingSystemResponse(BaseModel):
    id: int
    name: str
    grading_type: str
    is_default: bool
    scales: List[GradeScaleResponse] = []

    class Config:
        from_attributes = True


class ExamCreate(BaseModel):
    academic_term_id: int
    class_section_id: int
    subject_id: int
    exam_type_id: int
    name: str
    max_marks: float
    exam_date: date
    duration_minutes: Optional[int] = 60
    is_published: bool = False


class ExamUpdate(BaseModel):
    name: Optional[str] = None
    max_marks: Optional[float] = None
    exam_date: Optional[date] = None
    duration_minutes: Optional[int] = None


class ExamResponse(BaseModel):
    id: int
    academic_term_id: int
    class_section_id: int
    subject_id: int
    exam_type_id: int
    name: str
    max_marks: float
    exam_date: date
    duration_minutes: int
    is_published: bool
    academic_term: Optional[str] = None
    class_section: Optional[str] = None
    subject: Optional[str] = None
    exam_type: Optional[str] = None

    class Config:
        from_attributes = True


class ExamResultSubmit(BaseModel):
    exam_id: int
    student_id: int
    marks_obtained: float
    remarks: Optional[str] = None


class BulkResultSubmit(BaseModel):
    exam_id: int
    results: List[ExamResultSubmit]


class ExamResultResponse(BaseModel):
    id: int
    exam_id: int
    student_id: int
    marks_obtained: float
    grade_id: Optional[int]
    remarks: Optional[str]
    graded_by_teacher_id: Optional[int]
    graded_at: Optional[date]
    percentage: Optional[float] = None
    grade_letter: Optional[str] = None

    class Config:
        from_attributes = True


class SubjectGrade(BaseModel):
    subject_id: int
    subject_name: str
    exam_type: str
    max_marks: float
    marks_obtained: float
    percentage: float
    grade: str
    grade_point: Optional[float]


class StudentGradeReport(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    academic_term: str
    subjects: List[SubjectGrade]
    cumulative_gpa: Optional[float]
    overall_percentage: Optional[float]
    rank: Optional[int]
    teacher_remarks: Optional[str]


class ClassSectionReport(BaseModel):
    class_section_id: int
    class_section_name: str
    academic_term: str
    students: List[StudentGradeReport]
    class_average: Optional[float]
    pass_percentage: Optional[float]


class ResultUpdate(BaseModel):
    marks_obtained: Optional[float] = None
    remarks: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_percentage(marks_obtained: float, max_marks: float) -> float:
    """Calculate percentage from marks."""
    if max_marks <= 0:
        return 0.0
    return round((marks_obtained / max_marks) * 100, 2)


async def get_grade_letter(
    db: AsyncSession,
    percentage: float,
    grading_system_id: int
) -> tuple[Optional[str], Optional[float]]:
    """Determine grade letter and grade point based on percentage and grading system."""
    result = await db.execute(
        select(GradeScale).where(
            and_(
                GradeScale.grading_system_id == grading_system_id,
                GradeScale.min_percentage <= percentage,
                GradeScale.max_percentage >= percentage
            )
        )
    )
    scale = result.scalar_one_or_none()
    if scale:
        return scale.letter, float(scale.grade_point) if scale.grade_point else None
    return None, None


async def get_student_grading_system(db: AsyncSession, school_id: int) -> Optional[GradingSystem]:
    """Get the default grading system for a school."""
    result = await db.execute(
        select(GradingSystem).where(
            and_(
                GradingSystem.school_id == school_id,
                GradingSystem.is_default == True
            )
        )
    )
    return result.scalar_one_or_none()


async def get_teacher_from_user(db: AsyncSession, user_id: int) -> Optional[Teacher]:
    """Get teacher record from user ID."""
    result = await db.execute(
        select(Person).where(Person.user_id == user_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        return None
    result = await db.execute(
        select(Teacher).where(Teacher.person_id == person.id)
    )
    return result.scalar_one_or_none()


async def get_student_from_user(db: AsyncSession, user_id: int) -> Optional[Student]:
    """Get student record from user ID."""
    result = await db.execute(
        select(Person).where(Person.user_id == user_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        return None
    result = await db.execute(
        select(Student).where(Student.person_id == person.id)
    )
    return result.scalar_one_or_none()


async def is_teacher_assigned_to_subject(
    db: AsyncSession,
    teacher_id: int,
    subject_id: int,
    class_section_id: int,
    academic_term_id: int
) -> bool:
    """Check if a teacher is assigned to a subject in a class section."""
    result = await db.execute(
        select(TeacherAssignment).where(
            and_(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.subject_id == subject_id,
                TeacherAssignment.class_section_id == class_section_id,
                TeacherAssignment.academic_term_id == academic_term_id
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def get_enrollment_for_student(
    db: AsyncSession,
    student_id: int,
    academic_term_id: int
) -> Optional[Enrollment]:
    """Get enrollment for a student in a specific academic term."""
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.academic_term_id == academic_term_id
            )
        )
    )
    return result.scalar_one_or_none()


# =============================================================================
# Grading Systems Endpoints
# =============================================================================

@router.get("/systems", response_model=List[GradingSystemResponse])
async def list_grading_systems(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all grading systems for the school."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(GradingSystem)
        .options(selectinload(GradingSystem.grade_scales))
        .where(GradingSystem.school_id == school_id)
        .offset(skip)
        .limit(limit)
    )
    systems = result.scalars().all()

    response = []
    for system in systems:
        scales = [
            GradeScaleResponse(
                id=scale.id,
                letter=scale.letter,
                min_percentage=float(scale.min_percentage),
                max_percentage=float(scale.max_percentage),
                grade_point=float(scale.grade_point) if scale.grade_point else None
            )
            for scale in system.grade_scales
        ]
        response.append(GradingSystemResponse(
            id=system.id,
            name=system.name,
            grading_type=system.grading_type,
            is_default=system.is_default,
            scales=scales
        ))

    return response


@router.post("/systems", response_model=GradingSystemResponse)
async def create_grading_system(
    data: GradingSystemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Create a new grading system with grade scales."""
    school_id = current_user.tenant_id

    # If setting as default, unset other defaults
    if data.is_default:
        await db.execute(
            update(GradingSystem)
            .where(GradingSystem.school_id == school_id)
            .values(is_default=False)
        )

    # Create grading system
    grading_system = GradingSystem(
        school_id=school_id,
        name=data.name,
        grading_type=data.grading_type,
        is_default=data.is_default
    )
    db.add(grading_system)
    await db.flush()

    # Create grade scales
    for scale_data in data.scales:
        scale = GradeScale(
            grading_system_id=grading_system.id,
            letter=scale_data.letter,
            min_percentage=Decimal(str(scale_data.min_percentage)),
            max_percentage=Decimal(str(scale_data.max_percentage)),
            grade_point=Decimal(str(scale_data.grade_point)) if scale_data.grade_point else None
        )
        db.add(scale)

    await db.commit()

    # Reload with scales
    result = await db.execute(
        select(GradingSystem)
        .options(selectinload(GradingSystem.grade_scales))
        .where(GradingSystem.id == grading_system.id)
    )
    system = result.scalar_one()

    scales = [
        GradeScaleResponse(
            id=scale.id,
            letter=scale.letter,
            min_percentage=float(scale.min_percentage),
            max_percentage=float(scale.max_percentage),
            grade_point=float(scale.grade_point) if scale.grade_point else None
        )
        for scale in system.grade_scales
    ]

    return GradingSystemResponse(
        id=system.id,
        name=system.name,
        grading_type=system.grading_type,
        is_default=system.is_default,
        scales=scales
    )


@router.get("/systems/{system_id}", response_model=GradingSystemResponse)
async def get_grading_system(
    system_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Get a grading system with its grade scales."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(GradingSystem)
        .options(selectinload(GradingSystem.grade_scales))
        .where(
            and_(
                GradingSystem.id == system_id,
                GradingSystem.school_id == school_id
            )
        )
    )
    system = result.scalar_one_or_none()

    if not system:
        raise HTTPException(status_code=404, detail="Grading system not found")

    scales = [
        GradeScaleResponse(
            id=scale.id,
            letter=scale.letter,
            min_percentage=float(scale.min_percentage),
            max_percentage=float(scale.max_percentage),
            grade_point=float(scale.grade_point) if scale.grade_point else None
        )
        for scale in system.grade_scales
    ]

    return GradingSystemResponse(
        id=system.id,
        name=system.name,
        grading_type=system.grading_type,
        is_default=system.is_default,
        scales=scales
    )


@router.put("/systems/{system_id}", response_model=GradingSystemResponse)
async def update_grading_system(
    system_id: int,
    data: GradingSystemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update a grading system."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(GradingSystem)
        .options(selectinload(GradingSystem.grade_scales))
        .where(
            and_(
                GradingSystem.id == system_id,
                GradingSystem.school_id == school_id
            )
        )
    )
    system = result.scalar_one_or_none()

    if not system:
        raise HTTPException(status_code=404, detail="Grading system not found")

    # If setting as default, unset other defaults
    if data.is_default is True:
        await db.execute(
            update(GradingSystem)
            .where(
                and_(
                    GradingSystem.school_id == school_id,
                    GradingSystem.id != system_id
                )
            )
            .values(is_default=False)
        )

    if data.name is not None:
        system.name = data.name
    if data.grading_type is not None:
        system.grading_type = data.grading_type
    if data.is_default is not None:
        system.is_default = data.is_default

    await db.commit()

    scales = [
        GradeScaleResponse(
            id=scale.id,
            letter=scale.letter,
            min_percentage=float(scale.min_percentage),
            max_percentage=float(scale.max_percentage),
            grade_point=float(scale.grade_point) if scale.grade_point else None
        )
        for scale in system.grade_scales
    ]

    return GradingSystemResponse(
        id=system.id,
        name=system.name,
        grading_type=system.grading_type,
        is_default=system.is_default,
        scales=scales
    )


# =============================================================================
# Exam Management Endpoints
# =============================================================================

@router.get("/exams", response_model=List[ExamResponse])
async def list_exams(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
    academic_term_id: Optional[int] = Query(None),
    class_section_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all exams (Admin sees all, Teacher sees assigned)."""
    school_id = current_user.tenant_id

    query = (
        select(Exam)
        .options(
            selectinload(Exam.academic_term),
            selectinload(Exam.class_section),
            selectinload(Exam.subject),
            selectinload(Exam.exam_type)
        )
        .join(AcademicTerm)
        .where(AcademicTerm.school_id == school_id)
    )

    if academic_term_id:
        query = query.where(Exam.academic_term_id == academic_term_id)
    if class_section_id:
        query = query.where(Exam.class_section_id == class_section_id)
    if subject_id:
        query = query.where(Exam.subject_id == subject_id)

    # If teacher, filter to their assigned subjects
    if current_user.role == "teacher":
        teacher = await get_teacher_from_user(db, current_user.id)
        if teacher:
            result = await db.execute(
                select(TeacherAssignment.subject_id, TeacherAssignment.class_section_id)
                .where(TeacherAssignment.teacher_id == teacher.id)
            )
            assignments = result.all()
            subject_section_pairs = [
                (a.subject_id, a.class_section_id) for a in assignments
            ]
            query = query.where(
                Exam.subject_id.in_([s for s, _ in subject_section_pairs])
            )

    query = query.order_by(desc(Exam.exam_date)).offset(skip).limit(limit)

    result = await db.execute(query)
    exams = result.scalars().all()

    return [
        ExamResponse(
            id=exam.id,
            academic_term_id=exam.academic_term_id,
            class_section_id=exam.class_section_id,
            subject_id=exam.subject_id,
            exam_type_id=exam.exam_type_id,
            name=exam.name,
            max_marks=float(exam.max_marks),
            exam_date=exam.exam_date,
            duration_minutes=exam.duration_minutes,
            is_published=exam.is_published,
            academic_term=exam.academic_term.name if exam.academic_term else None,
            class_section=exam.class_section.name if exam.class_section else None,
            subject=exam.subject.name if exam.subject else None,
            exam_type=exam.exam_type.name if exam.exam_type else None
        )
        for exam in exams
    ]


@router.post("/exams", response_model=ExamResponse)
async def create_exam(
    data: ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Create a new exam (Admin or Teacher who is assigned to the subject)."""
    school_id = current_user.tenant_id

    # Verify academic term exists and belongs to school
    result = await db.execute(
        select(AcademicTerm).where(
            and_(
                AcademicTerm.id == data.academic_term_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid academic term")

    # Verify class section exists
    result = await db.execute(
        select(ClassSection).where(
            and_(
                ClassSection.id == data.class_section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid class section")

    # Verify subject exists
    result = await db.execute(
        select(Subject).where(
            and_(
                Subject.id == data.subject_id,
                Subject.school_id == school_id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid subject")

    # Verify exam type exists
    result = await db.execute(
        select(ExamType).where(
            and_(
                ExamType.id == data.exam_type_id,
                ExamType.school_id == school_id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid exam type")

    # If teacher, verify they are assigned to this subject
    if current_user.role == "teacher":
        teacher = await get_teacher_from_user(db, current_user.id)
        if teacher:
            assigned = await is_teacher_assigned_to_subject(
                db, teacher.id, data.subject_id, data.class_section_id, data.academic_term_id
            )
            if not assigned:
                raise HTTPException(
                    status_code=403,
                    detail="You are not assigned to this subject in this class"
                )

    exam = Exam(
        academic_term_id=data.academic_term_id,
        class_section_id=data.class_section_id,
        subject_id=data.subject_id,
        exam_type_id=data.exam_type_id,
        name=data.name,
        max_marks=Decimal(str(data.max_marks)),
        exam_date=data.exam_date,
        duration_minutes=data.duration_minutes,
        is_published=data.is_published
    )
    db.add(exam)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Exam)
        .options(
            selectinload(Exam.academic_term),
            selectinload(Exam.class_section),
            selectinload(Exam.subject),
            selectinload(Exam.exam_type)
        )
        .where(Exam.id == exam.id)
    )
    exam = result.scalar_one()

    return ExamResponse(
        id=exam.id,
        academic_term_id=exam.academic_term_id,
        class_section_id=exam.class_section_id,
        subject_id=exam.subject_id,
        exam_type_id=exam.exam_type_id,
        name=exam.name,
        max_marks=float(exam.max_marks),
        exam_date=exam.exam_date,
        duration_minutes=exam.duration_minutes,
        is_published=exam.is_published,
        academic_term=exam.academic_term.name if exam.academic_term else None,
        class_section=exam.class_section.name if exam.class_section else None,
        subject=exam.subject.name if exam.subject else None,
        exam_type=exam.exam_type.name if exam.exam_type else None
    )


@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Get an exam with its details."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Exam)
        .options(
            selectinload(Exam.academic_term),
            selectinload(Exam.class_section),
            selectinload(Exam.subject),
            selectinload(Exam.exam_type)
        )
        .join(AcademicTerm)
        .where(
            and_(
                Exam.id == exam_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    return ExamResponse(
        id=exam.id,
        academic_term_id=exam.academic_term_id,
        class_section_id=exam.class_section_id,
        subject_id=exam.subject_id,
        exam_type_id=exam.exam_type_id,
        name=exam.name,
        max_marks=float(exam.max_marks),
        exam_date=exam.exam_date,
        duration_minutes=exam.duration_minutes,
        is_published=exam.is_published,
        academic_term=exam.academic_term.name if exam.academic_term else None,
        class_section=exam.class_section.name if exam.class_section else None,
        subject=exam.subject.name if exam.subject else None,
        exam_type=exam.exam_type.name if exam.exam_type else None
    )


@router.put("/exams/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    data: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update an exam (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Exam)
        .options(
            selectinload(Exam.academic_term),
            selectinload(Exam.class_section),
            selectinload(Exam.subject),
            selectinload(Exam.exam_type)
        )
        .join(AcademicTerm)
        .where(
            and_(
                Exam.id == exam_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if data.name is not None:
        exam.name = data.name
    if data.max_marks is not None:
        exam.max_marks = Decimal(str(data.max_marks))
    if data.exam_date is not None:
        exam.exam_date = data.exam_date
    if data.duration_minutes is not None:
        exam.duration_minutes = data.duration_minutes

    await db.commit()

    return ExamResponse(
        id=exam.id,
        academic_term_id=exam.academic_term_id,
        class_section_id=exam.class_section_id,
        subject_id=exam.subject_id,
        exam_type_id=exam.exam_type_id,
        name=exam.name,
        max_marks=float(exam.max_marks),
        exam_date=exam.exam_date,
        duration_minutes=exam.duration_minutes,
        is_published=exam.is_published,
        academic_term=exam.academic_term.name if exam.academic_term else None,
        class_section=exam.class_section.name if exam.class_section else None,
        subject=exam.subject.name if exam.subject else None,
        exam_type=exam.exam_type.name if exam.exam_type else None
    )


@router.delete("/exams/{exam_id}")
async def delete_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Delete an exam (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Exam)
        .join(AcademicTerm)
        .where(
            and_(
                Exam.id == exam_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    await db.delete(exam)
    await db.commit()

    return {"message": "Exam deleted successfully"}


@router.post("/exams/{exam_id}/publish")
async def publish_exam_results(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Publish exam results (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Exam).join(AcademicTerm).where(
            and_(
                Exam.id == exam_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam.is_published = True
    await db.commit()

    return {"message": "Exam results published successfully"}


# =============================================================================
# Results Endpoints
# =============================================================================

@router.post("/results", response_model=ExamResultResponse)
async def submit_result(
    data: ExamResultSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Submit a single exam result (Teacher must be assigned to the subject)."""
    teacher = await get_teacher_from_user(db, current_user.id)
    if not teacher:
        raise HTTPException(status_code=403, detail="Teacher profile not found")

    # Get exam with details
    result = await db.execute(
        select(Exam).where(Exam.id == data.exam_id)
    )
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Verify teacher is assigned to this subject
    assigned = await is_teacher_assigned_to_subject(
        db, teacher.id, exam.subject_id, exam.class_section_id, exam.academic_term_id
    )
    if current_user.role == "teacher" and not assigned:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this subject"
        )

    # Verify student is enrolled in this class
    enrollment = await get_enrollment_for_student(
        db, data.student_id, exam.academic_term_id
    )
    if not enrollment or enrollment.section_id != exam.class_section_id:
        raise HTTPException(
            status_code=400,
            detail="Student is not enrolled in this class section"
        )

    # Check if result already exists
    existing = await db.execute(
        select(ExamResult).where(
            and_(
                ExamResult.exam_id == data.exam_id,
                ExamResult.student_id == data.student_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Result already exists for this student and exam"
        )

    # Calculate percentage and grade
    percentage = calculate_percentage(data.marks_obtained, float(exam.max_marks))

    # Get grading system for the school
    grading_system = await get_student_grading_system(db, current_user.tenant_id)
    grade_letter = None
    grade_point = None
    grade_id = None

    if grading_system:
        grade_letter, grade_point = await get_grade_letter(
            db, percentage, grading_system.id
        )
        if grade_letter:
            scale_result = await db.execute(
                select(GradeScale).where(
                    and_(
                        GradeScale.grading_system_id == grading_system.id,
                        GradeScale.letter == grade_letter
                    )
                )
            )
            scale = scale_result.scalar_one_or_none()
            if scale:
                grade_id = scale.id

    # Create result
    exam_result = ExamResult(
        exam_id=data.exam_id,
        student_id=data.student_id,
        marks_obtained=Decimal(str(data.marks_obtained)),
        remarks=data.remarks,
        grade_id=grade_id,
        graded_by_teacher_id=teacher.id,
        graded_at=date.today()
    )
    db.add(exam_result)
    await db.commit()

    return ExamResultResponse(
        id=exam_result.id,
        exam_id=exam_result.exam_id,
        student_id=exam_result.student_id,
        marks_obtained=float(exam_result.marks_obtained),
        grade_id=exam_result.grade_id,
        remarks=exam_result.remarks,
        graded_by_teacher_id=exam_result.graded_by_teacher_id,
        graded_at=exam_result.graded_at,
        percentage=percentage,
        grade_letter=grade_letter
    )


@router.post("/results/bulk")
async def submit_bulk_results(
    data: BulkResultSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Bulk submit exam results (Teacher must be assigned to the subject)."""
    teacher = await get_teacher_from_user(db, current_user.id)
    if not teacher:
        raise HTTPException(status_code=403, detail="Teacher profile not found")

    # Get exam with details
    result = await db.execute(
        select(Exam).where(Exam.id == data.exam_id)
    )
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Verify teacher is assigned to this subject
    assigned = await is_teacher_assigned_to_subject(
        db, teacher.id, exam.subject_id, exam.class_section_id, exam.academic_term_id
    )
    if current_user.role == "teacher" and not assigned:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this subject"
        )

    # Get grading system
    grading_system = await get_student_grading_system(db, current_user.tenant_id)

    created_results = []
    errors = []

    for idx, res_data in enumerate(data.results):
        # Verify student is enrolled
        enrollment = await get_enrollment_for_student(
            db, res_data.student_id, exam.academic_term_id
        )
        if not enrollment or enrollment.section_id != exam.class_section_id:
            errors.append({
                "index": idx,
                "student_id": res_data.student_id,
                "error": "Student not enrolled in this class section"
            })
            continue

        # Check if result already exists
        existing = await db.execute(
            select(ExamResult).where(
                and_(
                    ExamResult.exam_id == data.exam_id,
                    ExamResult.student_id == res_data.student_id
                )
            )
        )
        if existing.scalar_one_or_none():
            errors.append({
                "index": idx,
                "student_id": res_data.student_id,
                "error": "Result already exists"
            })
            continue

        # Calculate percentage and grade
        percentage = calculate_percentage(res_data.marks_obtained, float(exam.max_marks))

        grade_letter = None
        grade_point = None
        grade_id = None

        if grading_system:
            grade_letter, grade_point = await get_grade_letter(
                db, percentage, grading_system.id
            )
            if grade_letter:
                scale_result = await db.execute(
                    select(GradeScale).where(
                        and_(
                            GradeScale.grading_system_id == grading_system.id,
                            GradeScale.letter == grade_letter
                        )
                    )
                )
                scale = scale_result.scalar_one_or_none()
                if scale:
                    grade_id = scale.id

        exam_result = ExamResult(
            exam_id=data.exam_id,
            student_id=res_data.student_id,
            marks_obtained=Decimal(str(res_data.marks_obtained)),
            remarks=res_data.remarks,
            grade_id=grade_id,
            graded_by_teacher_id=teacher.id,
            graded_at=date.today()
        )
        db.add(exam_result)
        created_results.append({
            "student_id": res_data.student_id,
            "marks_obtained": res_data.marks_obtained,
            "percentage": percentage,
            "grade_letter": grade_letter
        })

    await db.commit()

    return {
        "created": created_results,
        "errors": errors,
        "total_created": len(created_results),
        "total_errors": len(errors)
    }


@router.get("/results/exam/{exam_id}", response_model=List[ExamResultResponse])
async def get_exam_results(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Get all results for an exam (Admin or assigned Teacher)."""
    school_id = current_user.tenant_id

    # Verify exam exists and belongs to school
    result = await db.execute(
        select(Exam)
        .options(selectinload(Exam.academic_term))
        .join(AcademicTerm)
        .where(
            and_(
                Exam.id == exam_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # If teacher, verify they are assigned to this subject
    if current_user.role == "teacher":
        teacher = await get_teacher_from_user(db, current_user.id)
        if teacher:
            assigned = await is_teacher_assigned_to_subject(
                db, teacher.id, exam.subject_id, exam.class_section_id, exam.academic_term_id
            )
            if not assigned:
                raise HTTPException(
                    status_code=403,
                    detail="You are not assigned to this subject"
                )

    # Get results
    result = await db.execute(
        select(ExamResult)
        .options(selectinload(ExamResult.grade))
        .where(ExamResult.exam_id == exam_id)
    )
    results = result.scalars().all()

    return [
        ExamResultResponse(
            id=r.id,
            exam_id=r.exam_id,
            student_id=r.student_id,
            marks_obtained=float(r.marks_obtained),
            grade_id=r.grade_id,
            remarks=r.remarks,
            graded_by_teacher_id=r.graded_by_teacher_id,
            graded_at=r.graded_at,
            percentage=calculate_percentage(float(r.marks_obtained), float(exam.max_marks)),
            grade_letter=r.grade.letter if r.grade else None
        )
        for r in results
    ]


@router.put("/results/{result_id}", response_model=ExamResultResponse)
async def update_result(
    result_id: int,
    data: ResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Update an exam result (Teacher must be assigned to the subject)."""
    teacher = await get_teacher_from_user(db, current_user.id)
    if not teacher:
        raise HTTPException(status_code=403, detail="Teacher profile not found")

    result = await db.execute(
        select(ExamResult)
        .options(selectinload(ExamResult.exam))
        .where(ExamResult.id == result_id)
    )
    exam_result = result.scalar_one_or_none()

    if not exam_result:
        raise HTTPException(status_code=404, detail="Result not found")

    exam = exam_result.exam

    # If teacher, verify they are assigned to this subject
    if current_user.role == "teacher":
        assigned = await is_teacher_assigned_to_subject(
            db, teacher.id, exam.subject_id, exam.class_section_id, exam.academic_term_id
        )
        if not assigned:
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this subject"
            )

    if data.marks_obtained is not None:
        exam_result.marks_obtained = Decimal(str(data.marks_obtained))

        # Recalculate percentage and grade
        percentage = calculate_percentage(data.marks_obtained, float(exam.max_marks))

        grading_system = await get_student_grading_system(db, current_user.tenant_id)
        if grading_system:
            grade_letter, _ = await get_grade_letter(db, percentage, grading_system.id)
            if grade_letter:
                scale_result = await db.execute(
                    select(GradeScale).where(
                        and_(
                            GradeScale.grading_system_id == grading_system.id,
                            GradeScale.letter == grade_letter
                        )
                    )
                )
                scale = scale_result.scalar_one_or_none()
                if scale:
                    exam_result.grade_id = scale.id
            else:
                exam_result.grade_id = None

    if data.remarks is not None:
        exam_result.remarks = data.remarks

    exam_result.graded_by_teacher_id = teacher.id
    exam_result.graded_at = date.today()

    await db.commit()

    # Reload with grade
    result = await db.execute(
        select(ExamResult)
        .options(selectinload(ExamResult.grade))
        .where(ExamResult.id == result_id)
    )
    exam_result = result.scalar_one()

    return ExamResultResponse(
        id=exam_result.id,
        exam_id=exam_result.exam_id,
        student_id=exam_result.student_id,
        marks_obtained=float(exam_result.marks_obtained),
        grade_id=exam_result.grade_id,
        remarks=exam_result.remarks,
        graded_by_teacher_id=exam_result.graded_by_teacher_id,
        graded_at=exam_result.graded_at,
        percentage=calculate_percentage(float(exam_result.marks_obtained), float(exam.max_marks)),
        grade_letter=exam_result.grade.letter if exam_result.grade else None
    )


@router.get("/results/student/{student_id}", response_model=List[ExamResultResponse])
async def get_student_results(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher", "student", "parent"])),
    academic_term_id: Optional[int] = Query(None),
):
    """Get all results for a student (Admin, Teacher, Self, or Parent of student)."""
    school_id = current_user.tenant_id

    # Verify student exists and belongs to school
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.person))
        .join(Person)
        .where(
            and_(
                Student.id == student_id,
                Person.user_id != None  # Ensure person has user account
            )
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # If self (student), verify this is their own record
    if current_user.role == "student":
        current_student = await get_student_from_user(db, current_user.id)
        if not current_student or current_student.id != student_id:
            raise HTTPException(status_code=403, detail="Cannot view other student's results")

    # If parent, verify this is their child's record (simplified - actual implementation would check guardian relationship)
    if current_user.role == "parent":
        pass  # Simplified - would need to check guardian relationship

    # Build query
    query = (
        select(ExamResult)
        .options(
            selectinload(ExamResult.exam),
            selectinload(ExamResult.grade)
        )
        .join(Exam)
        .join(AcademicTerm)
        .where(
            and_(
                ExamResult.student_id == student_id,
                AcademicTerm.school_id == school_id
            )
        )
    )

    if academic_term_id:
        query = query.where(Exam.academic_term_id == academic_term_id)

    query = query.order_by(Exam.exam_date)

    result = await db.execute(query)
    results = result.scalars().all()

    return [
        ExamResultResponse(
            id=r.id,
            exam_id=r.exam_id,
            student_id=r.student_id,
            marks_obtained=float(r.marks_obtained),
            grade_id=r.grade_id,
            remarks=r.remarks,
            graded_by_teacher_id=r.graded_by_teacher_id,
            graded_at=r.graded_at,
            percentage=calculate_percentage(float(r.marks_obtained), float(r.exam.max_marks)),
            grade_letter=r.grade.letter if r.grade else None
        )
        for r in results
    ]


# =============================================================================
# Reports Endpoints
# =============================================================================

@router.get("/report/student/{student_id}", response_model=StudentGradeReport)
async def get_student_report(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher", "student", "parent"])),
    academic_term_id: Optional[int] = Query(None),
):
    """Generate a comprehensive grade report for a student."""
    school_id = current_user.tenant_id

    # Verify student exists
    result = await db.execute(
        select(Student)
        .options(
            selectinload(Student.person),
            selectinload(Student.enrollments)
        )
        .join(Person)
        .where(Person.user_id != None)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # If self (student), verify this is their own record
    if current_user.role == "student":
        current_student = await get_student_from_user(db, current_user.id)
        if not current_student or current_student.id != student_id:
            raise HTTPException(status_code=403, detail="Cannot view other student's report")

    # Get enrollment
    enrollment_query = select(Enrollment).where(Enrollment.student_id == student_id)
    if academic_term_id:
        enrollment_query = enrollment_query.where(Enrollment.academic_term_id == academic_term_id)
    else:
        enrollment_query = enrollment_query.where(Enrollment.status == "active")

    result = await db.execute(enrollment_query)
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Student not enrolled in any class")

    academic_term_id = enrollment.academic_term_id

    # Get academic term name
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    term_name = academic_term.name if academic_term else "Unknown"

    # Get grading system
    grading_system = await get_student_grading_system(db, school_id)

    # Get all exam results for this student in this term
    result = await db.execute(
        select(ExamResult)
        .options(
            selectinload(ExamResult.exam).selectinload(Exam.exam_type),
            selectinload(ExamResult.exam).selectinload(Exam.subject),
            selectinload(ExamResult.grade)
        )
        .join(Exam)
        .where(
            and_(
                ExamResult.student_id == student_id,
                Exam.academic_term_id == academic_term_id
            )
        )
    )
    exam_results = result.scalars().all()

    # Group by subject and exam type
    subject_grades: dict[tuple[int, int], SubjectGrade] = {}

    for er in exam_results:
        key = (er.exam.subject_id, er.exam.exam_type_id)
        percentage = calculate_percentage(float(er.marks_obtained), float(er.exam.max_marks))

        grade_letter = er.grade.letter if er.grade else None
        grade_point = float(er.grade.grade_point) if er.grade and er.grade.grade_point else None

        subject_grades[key] = SubjectGrade(
            subject_id=er.exam.subject_id,
            subject_name=er.exam.subject.name if er.exam.subject else "Unknown",
            exam_type=er.exam.exam_type.name if er.exam.exam_type else "Unknown",
            max_marks=float(er.exam.max_marks),
            marks_obtained=float(er.marks_obtained),
            percentage=percentage,
            grade=grade_letter or "N/A",
            grade_point=grade_point
        )

    subjects = list(subject_grades.values())

    # Calculate overall percentage
    overall_percentage = None
    if subjects:
        total_percentage = sum(s.percentage for s in subjects)
        overall_percentage = round(total_percentage / len(subjects), 2)

    # Calculate cumulative GPA
    cumulative_gpa = None
    if grading_system and subjects:
        grade_points = [s.grade_point for s in subjects if s.grade_point is not None]
        if grade_points:
            cumulative_gpa = round(sum(grade_points) / len(grade_points), 2)

    # Get rank within class section
    rank = None

    # Get all enrollments for this class section in this term
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.section_id == enrollment.section_id,
                Enrollment.academic_term_id == academic_term_id,
                Enrollment.status == "active"
            )
        )
    )
    all_enrollments = result.scalars().all()

    if len(all_enrollments) > 1:
        # Calculate total percentages for all students
        student_percentages = []

        for enr in all_enrollments:
            student_results = await db.execute(
                select(ExamResult)
                .options(selectinload(ExamResult.exam))
                .join(Exam)
                .where(
                    and_(
                        ExamResult.student_id == enr.student_id,
                        Exam.academic_term_id == academic_term_id
                    )
                )
            )
            results = student_results.scalars().all()

            if results:
                total_pct = sum(
                    calculate_percentage(float(r.marks_obtained), float(r.exam.max_marks))
                    for r in results
                )
                avg_pct = total_pct / len(results)
                student_percentages.append((enr.student_id, avg_pct))

        # Sort by percentage descending
        student_percentages.sort(key=lambda x: x[1], reverse=True)

        # Find rank of current student
        for idx, (sid, _) in enumerate(student_percentages):
            if sid == student_id:
                rank = idx + 1
                break

    # Get teacher's remarks from grade report if exists
    teacher_remarks = None
    result = await db.execute(
        select(GradeReport).where(
            and_(
                GradeReport.student_id == student_id,
                GradeReport.academic_term_id == academic_term_id
            )
        )
    )
    grade_report = result.scalar_one_or_none()
    if grade_report:
        teacher_remarks = grade_report.teacher_remarks

    # Get person for student name
    result = await db.execute(
        select(Person).where(Person.id == student.person_id)
    )
    person = result.scalar_one_or_none()
    student_name = f"{person.first_name} {person.last_name}" if person else "Unknown"

    return StudentGradeReport(
        student_id=student_id,
        student_name=student_name,
        roll_number=enrollment.roll_number or "N/A",
        academic_term=term_name,
        subjects=subjects,
        cumulative_gpa=cumulative_gpa,
        overall_percentage=overall_percentage,
        rank=rank,
        teacher_remarks=teacher_remarks
    )


@router.get("/report/class/{class_section_id}", response_model=ClassSectionReport)
async def get_class_report(
    class_section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
    academic_term_id: Optional[int] = Query(None),
):
    """Generate a comprehensive grade report for a class section (Admin only)."""
    school_id = current_user.tenant_id

    # Verify class section exists
    result = await db.execute(
        select(ClassSection)
        .options(selectinload(ClassSection.grade_level))
        .where(
            and_(
                ClassSection.id == class_section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    class_section = result.scalar_one_or_none()

    if not class_section:
        raise HTTPException(status_code=404, detail="Class section not found")

    # Get academic term
    if academic_term_id:
        result = await db.execute(
            select(AcademicTerm).where(AcademicTerm.id == academic_term_id)
        )
        academic_term = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(AcademicTerm).where(
                and_(
                    AcademicTerm.school_id == school_id,
                    AcademicTerm.is_current == True
                )
            )
        )
        academic_term = result.scalar_one_or_none()

    if not academic_term:
        raise HTTPException(status_code=404, detail="No academic term found")

    term_name = academic_term.name

    # Get all enrollments for this class section
    result = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.student).selectinload(Student.person))
        .where(
            and_(
                Enrollment.section_id == class_section_id,
                Enrollment.academic_term_id == academic_term.id,
                Enrollment.status == "active"
            )
        )
    )
    enrollments = result.scalars().all()

    # Get grading system
    grading_system = await get_student_grading_system(db, school_id)

    student_reports = []
    all_percentages = []
    pass_count = 0

    for enrollment in enrollments:
        student = enrollment.student
        student_id = student.id
        person = student.person
        student_name = f"{person.first_name} {person.last_name}" if person else "Unknown"

        # Get all exam results for this student
        result = await db.execute(
            select(ExamResult)
            .options(
                selectinload(ExamResult.exam).selectinload(Exam.exam_type),
                selectinload(ExamResult.exam).selectinload(Exam.subject),
                selectinload(ExamResult.grade)
            )
            .join(Exam)
            .where(
                and_(
                    ExamResult.student_id == student_id,
                    Exam.academic_term_id == academic_term.id
                )
            )
        )
        exam_results = result.scalars().all()

        # Build subject grades
        subject_grades = []
        for er in exam_results:
            percentage = calculate_percentage(float(er.marks_obtained), float(er.exam.max_marks))
            grade_letter = er.grade.letter if er.grade else None
            grade_point = float(er.grade.grade_point) if er.grade and er.grade.grade_point else None

            subject_grades.append(SubjectGrade(
                subject_id=er.exam.subject_id,
                subject_name=er.exam.subject.name if er.exam.subject else "Unknown",
                exam_type=er.exam.exam_type.name if er.exam.exam_type else "Unknown",
                max_marks=float(er.exam.max_marks),
                marks_obtained=float(er.marks_obtained),
                percentage=percentage,
                grade=grade_letter or "N/A",
                grade_point=grade_point
            ))

        # Calculate overall percentage
        overall_percentage = None
        if subject_grades:
            total_percentage = sum(s.percentage for s in subject_grades)
            overall_percentage = round(total_percentage / len(subject_grades), 2)
            all_percentages.append(overall_percentage)

            # Check if passing (assuming 40% is passing)
            if overall_percentage >= 40:
                pass_count += 1

        # Calculate GPA
        cumulative_gpa = None
        if grading_system and subject_grades:
            grade_points = [s.grade_point for s in subject_grades if s.grade_point is not None]
            if grade_points:
                cumulative_gpa = round(sum(grade_points) / len(grade_points), 2)

        # Get rank
        rank = None

        student_reports.append(StudentGradeReport(
            student_id=student_id,
            student_name=student_name,
            roll_number=enrollment.roll_number or "N/A",
            academic_term=term_name,
            subjects=subject_grades,
            cumulative_gpa=cumulative_gpa,
            overall_percentage=overall_percentage,
            rank=rank,
            teacher_remarks=None
        ))

    # Calculate class average
    class_average = None
    if all_percentages:
        class_average = round(sum(all_percentages) / len(all_percentages), 2)

    # Calculate pass percentage
    pass_percentage = None
    if enrollments:
        pass_percentage = round((pass_count / len(enrollments)) * 100, 2)

    # Sort students by percentage and assign ranks
    student_reports.sort(key=lambda x: x.overall_percentage or 0, reverse=True)
    for idx, report in enumerate(student_reports):
        report.rank = idx + 1

    class_section_name = class_section.name

    return ClassSectionReport(
        class_section_id=class_section_id,
        class_section_name=class_section_name,
        academic_term=term_name,
        students=student_reports,
        class_average=class_average,
        pass_percentage=pass_percentage
    )


@router.post("/report/finalize/{student_id}")
async def finalize_student_grades(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
    academic_term_id: Optional[int] = Query(None),
    remarks: Optional[str] = Query(None),
):
    """Finalize term grades for a student (Admin only)."""
    school_id = current_user.tenant_id

    # Get academic term
    if academic_term_id:
        result = await db.execute(
            select(AcademicTerm).where(AcademicTerm.id == academic_term_id)
        )
        academic_term = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(AcademicTerm).where(
                and_(
                    AcademicTerm.school_id == school_id,
                    AcademicTerm.is_current == True
                )
            )
        )
        academic_term = result.scalar_one_or_none()

    if not academic_term:
        raise HTTPException(status_code=404, detail="No academic term found")

    # Get enrollment
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.academic_term_id == academic_term.id
            )
        )
    )
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Student not enrolled in this term")

    # Get grading system
    grading_system = await get_student_grading_system(db, school_id)

    # Calculate overall percentage from all exams
    result = await db.execute(
        select(ExamResult)
        .options(selectinload(ExamResult.exam))
        .join(Exam)
        .where(
            and_(
                ExamResult.student_id == student_id,
                Exam.academic_term_id == academic_term.id
            )
        )
    )
    exam_results = result.scalars().all()

    overall_percentage = None
    cumulative_gpa = None

    if exam_results:
        percentages = [
            calculate_percentage(float(r.marks_obtained), float(r.exam.max_marks))
            for r in exam_results
        ]
        overall_percentage = round(sum(percentages) / len(percentages), 2)

        if grading_system:
            grade_points = []
            for pct in percentages:
                _, gp = await get_grade_letter(db, pct, grading_system.id)
                if gp is not None:
                    grade_points.append(gp)

            if grade_points:
                cumulative_gpa = round(sum(grade_points) / len(grade_points), 2)

    # Calculate rank
    rank = None
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.section_id == enrollment.section_id,
                Enrollment.academic_term_id == academic_term.id,
                Enrollment.status == "active"
            )
        )
    )
    all_enrollments = result.scalars().all()

    if len(all_enrollments) > 1:
        student_percentages = []

        for enr in all_enrollments:
            student_results = await db.execute(
                select(ExamResult)
                .options(selectinload(ExamResult.exam))
                .join(Exam)
                .where(
                    and_(
                        ExamResult.student_id == enr.student_id,
                        Exam.academic_term_id == academic_term.id
                    )
                )
            )
            results = student_results.scalars().all()

            if results:
                total_pct = sum(
                    calculate_percentage(float(r.marks_obtained), float(r.exam.max_marks))
                    for r in results
                )
                avg_pct = total_pct / len(results)
                student_percentages.append((enr.student_id, avg_pct))

        student_percentages.sort(key=lambda x: x[1], reverse=True)

        for idx, (sid, _) in enumerate(student_percentages):
            if sid == student_id:
                rank = idx + 1
                break

    # Check if grade report already exists
    result = await db.execute(
        select(GradeReport).where(
            and_(
                GradeReport.student_id == student_id,
                GradeReport.academic_term_id == academic_term.id
            )
        )
    )
    existing_report = result.scalar_one_or_none()

    if existing_report:
        # Update existing report
        existing_report.cumulative_gpa = Decimal(str(cumulative_gpa)) if cumulative_gpa else None
        existing_report.rank = rank
        existing_report.teacher_remarks = remarks
        existing_report.finalized_at = date.today()
        grade_report = existing_report
    else:
        # Create new report
        grade_report = GradeReport(
            student_id=student_id,
            academic_term_id=academic_term.id,
            cumulative_gpa=Decimal(str(cumulative_gpa)) if cumulative_gpa else None,
            rank=rank,
            teacher_remarks=remarks,
            finalized_at=date.today()
        )
        db.add(grade_report)

    await db.commit()

    return {
        "message": "Grades finalized successfully",
        "student_id": student_id,
        "academic_term": academic_term.name,
        "cumulative_gpa": cumulative_gpa,
        "overall_percentage": overall_percentage,
        "rank": rank
    }

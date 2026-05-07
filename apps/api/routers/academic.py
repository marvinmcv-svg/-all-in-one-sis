"""Academic Structure Management API - Terms, Grade Levels, Sections, Subjects."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from ..database import get_db
from ..models.academic import AcademicTerm, GradeLevel, ClassSection, Subject, ClassSubject
from ..models.student import Enrollment, Student
from ..models.teacher import Teacher, TeacherAssignment
from ..models.person import Person
from ..core.deps import get_current_user, get_current_admin, require_roles

router = APIRouter(prefix="/academic", tags=["Academic Structure"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

class AcademicTermCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicTermUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AcademicTermResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_current: bool

    class Config:
        from_attributes = True


class GradeLevelCreate(BaseModel):
    name: str
    code: str
    next_grade_id: Optional[int] = None
    sequence: int


class GradeLevelUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    next_grade_id: Optional[int] = None
    sequence: Optional[int] = None


class GradeLevelResponse(BaseModel):
    id: int
    name: str
    code: str
    next_grade_id: Optional[int]
    next_grade: Optional[str]
    sequence: int

    class Config:
        from_attributes = True


class ClassSectionCreate(BaseModel):
    name: str
    grade_level_id: int
    room_number: Optional[str] = None
    capacity: Optional[int] = 40
    academic_term_id: int


class ClassSectionUpdate(BaseModel):
    name: Optional[str] = None
    grade_level_id: Optional[int] = None
    room_number: Optional[str] = None
    capacity: Optional[int] = None
    academic_term_id: Optional[int] = None


class ClassSectionResponse(BaseModel):
    id: int
    name: str
    grade_level: str
    room_number: Optional[str]
    capacity: int
    academic_term: str
    student_count: int

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    credit_hours: Optional[float] = 0
    subject_type: str = "theory"


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    credit_hours: Optional[float] = None
    subject_type: Optional[str] = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    credit_hours: float
    subject_type: str

    class Config:
        from_attributes = True


class ClassSubjectCreate(BaseModel):
    class_section_id: int
    subject_id: int
    teacher_id: int


class ClassSubjectUpdate(BaseModel):
    teacher_id: Optional[int] = None
    is_active: Optional[bool] = None


class ClassSubjectResponse(BaseModel):
    id: int
    class_section: ClassSectionResponse
    subject: SubjectResponse
    teacher: str

    class Config:
        from_attributes = True


# =============================================================================
# Helper Functions
# =============================================================================

async def get_teacher_name(db: AsyncSession, teacher_id: int) -> str:
    """Get teacher full name from teacher ID."""
    result = await db.execute(
        select(Person).join(Teacher).where(Teacher.id == teacher_id)
    )
    person = result.scalar_one_or_none()
    if person:
        return f"{person.first_name} {person.last_name}"
    return "Unknown"


async def get_enrollment_count(db: AsyncSession, section_id: int) -> int:
    """Get active enrollment count for a class section."""
    result = await db.execute(
        select(func.count(Enrollment.id)).where(
            and_(
                Enrollment.section_id == section_id,
                Enrollment.status == "active"
            )
        )
    )
    return result.scalar() or 0


async def check_grade_has_students(db: AsyncSession, grade_level_id: int) -> bool:
    """Check if grade level has any enrolled students."""
    result = await db.execute(
        select(func.count(Enrollment.id)).where(
            and_(
                Enrollment.grade_level_id == grade_level_id,
                Enrollment.status == "active"
            )
        )
    )
    return (result.scalar() or 0) > 0


async def check_section_has_students(db: AsyncSession, section_id: int) -> bool:
    """Check if section has any enrolled students."""
    result = await db.execute(
        select(func.count(Enrollment.id)).where(
            and_(
                Enrollment.section_id == section_id,
                Enrollment.status == "active"
            )
        )
    )
    return (result.scalar() or 0) > 0


# =============================================================================
# Academic Terms Endpoints
# =============================================================================

@router.get("/terms", response_model=List[AcademicTermResponse])
async def list_terms(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all academic terms for the school."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(AcademicTerm)
        .where(AcademicTerm.school_id == school_id)
        .order_by(AcademicTerm.start_date.desc())
        .offset(skip)
        .limit(limit)
    )
    terms = result.scalars().all()

    return [
        AcademicTermResponse(
            id=term.id,
            name=term.name,
            start_date=term.start_date,
            end_date=term.end_date,
            is_current=term.is_current
        )
        for term in terms
    ]


@router.post("/terms", response_model=AcademicTermResponse)
async def create_term(
    data: AcademicTermCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Create a new academic term (Admin only)."""
    school_id = current_user.tenant_id

    # Validate dates
    if data.end_date <= data.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    # If setting as current, unset other current terms
    if data.is_current:
        await db.execute(
            update(AcademicTerm)
            .where(
                and_(
                    AcademicTerm.school_id == school_id,
                    AcademicTerm.is_current == True
                )
            )
            .values(is_current=False)
        )

    term = AcademicTerm(
        school_id=school_id,
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        is_current=data.is_current
    )
    db.add(term)
    await db.commit()

    return AcademicTermResponse(
        id=term.id,
        name=term.name,
        start_date=term.start_date,
        end_date=term.end_date,
        is_current=term.is_current
    )


@router.get("/terms/{term_id}", response_model=AcademicTermResponse)
async def get_term(
    term_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get academic term details."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(AcademicTerm).where(
            and_(
                AcademicTerm.id == term_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="Academic term not found")

    return AcademicTermResponse(
        id=term.id,
        name=term.name,
        start_date=term.start_date,
        end_date=term.end_date,
        is_current=term.is_current
    )


@router.put("/terms/{term_id}", response_model=AcademicTermResponse)
async def update_term(
    term_id: int,
    data: AcademicTermUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update an academic term (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(AcademicTerm).where(
            and_(
                AcademicTerm.id == term_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="Academic term not found")

    # Validate dates if both provided
    start_date = data.start_date if data.start_date else term.start_date
    end_date = data.end_date if data.end_date else term.end_date
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    if data.name is not None:
        term.name = data.name
    if data.start_date is not None:
        term.start_date = data.start_date
    if data.end_date is not None:
        term.end_date = data.end_date

    await db.commit()

    return AcademicTermResponse(
        id=term.id,
        name=term.name,
        start_date=term.start_date,
        end_date=term.end_date,
        is_current=term.is_current
    )


@router.post("/terms/{term_id}/set-current", response_model=AcademicTermResponse)
async def set_current_term(
    term_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Set an academic term as current (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(AcademicTerm).where(
            and_(
                AcademicTerm.id == term_id,
                AcademicTerm.school_id == school_id
            )
        )
    )
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="Academic term not found")

    # Unset all other current terms
    await db.execute(
        update(AcademicTerm)
        .where(
            and_(
                AcademicTerm.school_id == school_id,
                AcademicTerm.is_current == True
            )
        )
        .values(is_current=False)
    )

    # Set this term as current
    term.is_current = True
    await db.commit()

    return AcademicTermResponse(
        id=term.id,
        name=term.name,
        start_date=term.start_date,
        end_date=term.end_date,
        is_current=term.is_current
    )


# =============================================================================
# Grade Levels Endpoints
# =============================================================================

@router.get("/grade-levels", response_model=List[GradeLevelResponse])
async def list_grade_levels(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all grade levels for the school."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(GradeLevel)
        .options(selectinload(GradeLevel.next_grade))
        .where(GradeLevel.school_id == school_id)
        .order_by(GradeLevel.sequence)
        .offset(skip)
        .limit(limit)
    )
    levels = result.scalars().all()

    return [
        GradeLevelResponse(
            id=level.id,
            name=level.name,
            code=level.code,
            next_grade_id=level.next_grade_id,
            next_grade=level.next_grade.name if level.next_grade else None,
            sequence=level.sequence
        )
        for level in levels
    ]


@router.post("/grade-levels", response_model=GradeLevelResponse)
async def create_grade_level(
    data: GradeLevelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Create a new grade level (Admin only)."""
    school_id = current_user.tenant_id

    # Check if code already exists
    result = await db.execute(
        select(GradeLevel).where(
            and_(
                GradeLevel.school_id == school_id,
                GradeLevel.code == data.code
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Grade level code already exists")

    # Verify next_grade_id if provided
    if data.next_grade_id:
        result = await db.execute(
            select(GradeLevel).where(
                and_(
                    GradeLevel.id == data.next_grade_id,
                    GradeLevel.school_id == school_id
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid next grade level")

    grade_level = GradeLevel(
        school_id=school_id,
        name=data.name,
        code=data.code,
        next_grade_id=data.next_grade_id,
        sequence=data.sequence
    )
    db.add(grade_level)
    await db.commit()

    # Reload with next_grade relationship
    result = await db.execute(
        select(GradeLevel)
        .options(selectinload(GradeLevel.next_grade))
        .where(GradeLevel.id == grade_level.id)
    )
    level = result.scalar_one()

    return GradeLevelResponse(
        id=level.id,
        name=level.name,
        code=level.code,
        next_grade_id=level.next_grade_id,
        next_grade=level.next_grade.name if level.next_grade else None,
        sequence=level.sequence
    )


@router.put("/grade-levels/{grade_id}", response_model=GradeLevelResponse)
async def update_grade_level(
    grade_id: int,
    data: GradeLevelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update a grade level (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(GradeLevel)
        .options(selectinload(GradeLevel.next_grade))
        .where(
            and_(
                GradeLevel.id == grade_id,
                GradeLevel.school_id == school_id
            )
        )
    )
    level = result.scalar_one_or_none()

    if not level:
        raise HTTPException(status_code=404, detail="Grade level not found")

    # Check code uniqueness if changing
    if data.code and data.code != level.code:
        result = await db.execute(
            select(GradeLevel).where(
                and_(
                    GradeLevel.school_id == school_id,
                    GradeLevel.code == data.code,
                    GradeLevel.id != grade_id
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Grade level code already exists")

    # Verify next_grade_id if provided
    if data.next_grade_id:
        result = await db.execute(
            select(GradeLevel).where(
                and_(
                    GradeLevel.id == data.next_grade_id,
                    GradeLevel.school_id == school_id
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid next grade level")

    if data.name is not None:
        level.name = data.name
    if data.code is not None:
        level.code = data.code
    if data.next_grade_id is not None:
        level.next_grade_id = data.next_grade_id
    if data.sequence is not None:
        level.sequence = data.sequence

    await db.commit()

    return GradeLevelResponse(
        id=level.id,
        name=level.name,
        code=level.code,
        next_grade_id=level.next_grade_id,
        next_grade=level.next_grade.name if level.next_grade else None,
        sequence=level.sequence
    )


@router.delete("/grade-levels/{grade_id}")
async def delete_grade_level(
    grade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Delete a grade level (Admin only). Cannot delete if students are enrolled."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(GradeLevel).where(
            and_(
                GradeLevel.id == grade_id,
                GradeLevel.school_id == school_id
            )
        )
    )
    level = result.scalar_one_or_none()

    if not level:
        raise HTTPException(status_code=404, detail="Grade level not found")

    # Check for enrolled students
    has_students = await check_grade_has_students(db, grade_id)
    if has_students:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete grade level with enrolled students"
        )

    await db.delete(level)
    await db.commit()

    return {"message": "Grade level deleted successfully"}


# =============================================================================
# Class Sections Endpoints
# =============================================================================

@router.get("/sections", response_model=List[ClassSectionResponse])
async def list_sections(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
    academic_term_id: Optional[int] = Query(None),
    grade_level_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all class sections for the school."""
    school_id = current_user.tenant_id

    query = (
        select(ClassSection)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term)
        )
        .where(ClassSection.school_id == school_id)
    )

    if academic_term_id:
        query = query.where(ClassSection.academic_term_id == academic_term_id)
    if grade_level_id:
        query = query.where(ClassSection.grade_level_id == grade_level_id)

    query = query.order_by(ClassSection.name).offset(skip).limit(limit)

    result = await db.execute(query)
    sections = result.scalars().all()

    response = []
    for section in sections:
        student_count = await get_enrollment_count(db, section.id)
        response.append(ClassSectionResponse(
            id=section.id,
            name=section.name,
            grade_level=section.grade_level.name if section.grade_level else "Unknown",
            room_number=section.room_number,
            capacity=section.capacity,
            academic_term=section.academic_term.name if section.academic_term else "Unknown",
            student_count=student_count
        ))

    return response


@router.post("/sections", response_model=ClassSectionResponse)
async def create_section(
    data: ClassSectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Create a new class section (Admin only)."""
    school_id = current_user.tenant_id

    # Verify academic term exists
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

    # Verify grade level exists
    result = await db.execute(
        select(GradeLevel).where(
            and_(
                GradeLevel.id == data.grade_level_id,
                GradeLevel.school_id == school_id
            )
        )
    )
    grade_level = result.scalar_one_or_none()
    if not grade_level:
        raise HTTPException(status_code=400, detail="Invalid grade level")

    section = ClassSection(
        school_id=school_id,
        name=data.name,
        grade_level_id=data.grade_level_id,
        room_number=data.room_number,
        capacity=data.capacity or 40,
        academic_term_id=data.academic_term_id
    )
    db.add(section)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ClassSection)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term)
        )
        .where(ClassSection.id == section.id)
    )
    section = result.scalar_one()

    return ClassSectionResponse(
        id=section.id,
        name=section.name,
        grade_level=section.grade_level.name if section.grade_level else "Unknown",
        room_number=section.room_number,
        capacity=section.capacity,
        academic_term=section.academic_term.name if section.academic_term else "Unknown",
        student_count=0
    )


@router.get("/sections/{section_id}", response_model=ClassSectionResponse)
async def get_section(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Get class section details."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(ClassSection)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term)
        )
        .where(
            and_(
                ClassSection.id == section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Class section not found")

    student_count = await get_enrollment_count(db, section_id)

    return ClassSectionResponse(
        id=section.id,
        name=section.name,
        grade_level=section.grade_level.name if section.grade_level else "Unknown",
        room_number=section.room_number,
        capacity=section.capacity,
        academic_term=section.academic_term.name if section.academic_term else "Unknown",
        student_count=student_count
    )


@router.put("/sections/{section_id}", response_model=ClassSectionResponse)
async def update_section(
    section_id: int,
    data: ClassSectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update a class section (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(ClassSection)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term)
        )
        .where(
            and_(
                ClassSection.id == section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Class section not found")

    # Verify academic term if changing
    if data.academic_term_id:
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
        section.academic_term_id = data.academic_term_id

    # Verify grade level if changing
    if data.grade_level_id:
        result = await db.execute(
            select(GradeLevel).where(
                and_(
                    GradeLevel.id == data.grade_level_id,
                    GradeLevel.school_id == school_id
                )
            )
        )
        grade_level = result.scalar_one_or_none()
        if not grade_level:
            raise HTTPException(status_code=400, detail="Invalid grade level")
        section.grade_level_id = data.grade_level_id

    if data.name is not None:
        section.name = data.name
    if data.room_number is not None:
        section.room_number = data.room_number
    if data.capacity is not None:
        section.capacity = data.capacity

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ClassSection)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term)
        )
        .where(ClassSection.id == section_id)
    )
    section = result.scalar_one()

    student_count = await get_enrollment_count(db, section_id)

    return ClassSectionResponse(
        id=section.id,
        name=section.name,
        grade_level=section.grade_level.name if section.grade_level else "Unknown",
        room_number=section.room_number,
        capacity=section.capacity,
        academic_term=section.academic_term.name if section.academic_term else "Unknown",
        student_count=student_count
    )


@router.delete("/sections/{section_id}")
async def delete_section(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Delete a class section (Admin only). Cannot delete if students are enrolled."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(ClassSection).where(
            and_(
                ClassSection.id == section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Class section not found")

    # Check for enrolled students
    has_students = await check_section_has_students(db, section_id)
    if has_students:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete class section with enrolled students"
        )

    await db.delete(section)
    await db.commit()

    return {"message": "Class section deleted successfully"}


@router.get("/sections/{section_id}/students", response_model=List[dict])
async def get_section_students(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Get all students enrolled in a class section."""
    school_id = current_user.tenant_id

    # Verify section exists
    result = await db.execute(
        select(ClassSection).where(
            and_(
                ClassSection.id == section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Class section not found")

    # Get enrollments
    result = await db.execute(
        select(Enrollment)
        .options(
            selectinload(Enrollment.student).selectinload(Student.person)
        )
        .where(
            and_(
                Enrollment.section_id == section_id,
                Enrollment.status == "active"
            )
        )
        .offset(skip)
        .limit(limit)
    )
    enrollments = result.scalars().all()

    return [
        {
            "enrollment_id": enr.id,
            "student_id": enr.student.id,
            "student_code": enr.student.student_id,
            "roll_number": enr.roll_number,
            "name": f"{enr.student.person.first_name} {enr.student.person.last_name}" if enr.student.person else "Unknown",
            "status": enr.status
        }
        for enr in enrollments
    ]


@router.get("/sections/{section_id}/subjects", response_model=List[dict])
async def get_section_subjects(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
):
    """Get all subjects assigned to a class section."""
    school_id = current_user.tenant_id

    # Verify section exists
    result = await db.execute(
        select(ClassSection).where(
            and_(
                ClassSection.id == section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Class section not found")

    # Get class subjects with their assignments
    result = await db.execute(
        select(ClassSubject)
        .options(
            selectinload(ClassSubject.subject),
            selectinload(ClassSubject.teacher_assignment).selectinload(TeacherAssignment.teacher).selectinload(Teacher.person)
        )
        .where(
            and_(
                ClassSubject.class_section_id == section_id,
                ClassSubject.is_active == True
            )
        )
    )
    class_subjects = result.scalars().all()

    return [
        {
            "id": cs.id,
            "subject_id": cs.subject.id,
            "subject_name": cs.subject.name,
            "subject_code": cs.subject.code,
            "subject_type": cs.subject.subject_type.value if cs.subject.subject_type else "theory",
            "credit_hours": cs.subject.credit_hours,
            "teacher_id": cs.teacher_assignment.teacher.id if cs.teacher_assignment and cs.teacher_assignment.teacher else None,
            "teacher_name": f"{cs.teacher_assignment.teacher.person.first_name} {cs.teacher_assignment.teacher.person.last_name}" if cs.teacher_assignment and cs.teacher_assignment.teacher and cs.teacher_assignment.teacher.person else None,
            "is_active": cs.is_active
        }
        for cs in class_subjects
    ]


# =============================================================================
# Subjects Endpoints
# =============================================================================

@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all subjects for the school."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Subject)
        .where(Subject.school_id == school_id)
        .order_by(Subject.name)
        .offset(skip)
        .limit(limit)
    )
    subjects = result.scalars().all()

    return [
        SubjectResponse(
            id=subject.id,
            name=subject.name,
            code=subject.code,
            description=subject.description,
            credit_hours=float(subject.credit_hours) if subject.credit_hours else 0,
            subject_type=subject.subject_type.value if subject.subject_type else "theory"
        )
        for subject in subjects
    ]


@router.post("/subjects", response_model=SubjectResponse)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Create a new subject (Admin only)."""
    school_id = current_user.tenant_id

    # Check if code already exists
    result = await db.execute(
        select(Subject).where(
            and_(
                Subject.school_id == school_id,
                Subject.code == data.code
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject code already exists")

    subject = Subject(
        school_id=school_id,
        name=data.name,
        code=data.code,
        description=data.description,
        credit_hours=int(data.credit_hours) if data.credit_hours else 0,
        subject_type=data.subject_type
    )
    db.add(subject)
    await db.commit()

    return SubjectResponse(
        id=subject.id,
        name=subject.name,
        code=subject.code,
        description=subject.description,
        credit_hours=float(subject.credit_hours) if subject.credit_hours else 0,
        subject_type=subject.subject_type.value if subject.subject_type else "theory"
    )


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update a subject (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Subject).where(
            and_(
                Subject.id == subject_id,
                Subject.school_id == school_id
            )
        )
    )
    subject = result.scalar_one_or_none()

    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check code uniqueness if changing
    if data.code and data.code != subject.code:
        result = await db.execute(
            select(Subject).where(
                and_(
                    Subject.school_id == school_id,
                    Subject.code == data.code,
                    Subject.id != subject_id
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Subject code already exists")

    if data.name is not None:
        subject.name = data.name
    if data.code is not None:
        subject.code = data.code
    if data.description is not None:
        subject.description = data.description
    if data.credit_hours is not None:
        subject.credit_hours = int(data.credit_hours)
    if data.subject_type is not None:
        subject.subject_type = data.subject_type

    await db.commit()

    return SubjectResponse(
        id=subject.id,
        name=subject.name,
        code=subject.code,
        description=subject.description,
        credit_hours=float(subject.credit_hours) if subject.credit_hours else 0,
        subject_type=subject.subject_type.value if subject.subject_type else "theory"
    )


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Delete a subject (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(Subject).where(
            and_(
                Subject.id == subject_id,
                Subject.school_id == school_id
            )
        )
    )
    subject = result.scalar_one_or_none()

    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    await db.delete(subject)
    await db.commit()

    return {"message": "Subject deleted successfully"}


# =============================================================================
# Class Subjects (Assignments) Endpoints
# =============================================================================

@router.get("/class-subjects", response_model=List[ClassSubjectResponse])
async def list_class_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(["admin", "teacher"])),
    class_section_id: Optional[int] = Query(None),
    academic_term_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all class-subject assignments."""
    school_id = current_user.tenant_id

    query = (
        select(ClassSubject)
        .options(
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.grade_level),
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.academic_term),
            selectinload(ClassSubject.subject),
            selectinload(ClassSubject.teacher_assignment)
        )
        .join(ClassSection)
        .where(ClassSection.school_id == school_id)
    )

    if class_section_id:
        query = query.where(ClassSubject.class_section_id == class_section_id)
    if academic_term_id:
        query = query.where(ClassSection.academic_term_id == academic_term_id)

    query = query.where(ClassSubject.is_active == True).offset(skip).limit(limit)

    result = await db.execute(query)
    class_subjects = result.scalars().all()

    response = []
    for cs in class_subjects:
        section = cs.class_section
        teacher_name = "Unassigned"
        if cs.teacher_assignment and cs.teacher_assignment.teacher:
            teacher = cs.teacher_assignment.teacher
            if teacher.person:
                teacher_name = f"{teacher.person.first_name} {teacher.person.last_name}"

        student_count = await get_enrollment_count(db, section.id)

        response.append(ClassSubjectResponse(
            id=cs.id,
            class_section=ClassSectionResponse(
                id=section.id,
                name=section.name,
                grade_level=section.grade_level.name if section.grade_level else "Unknown",
                room_number=section.room_number,
                capacity=section.capacity,
                academic_term=section.academic_term.name if section.academic_term else "Unknown",
                student_count=student_count
            ),
            subject=SubjectResponse(
                id=cs.subject.id,
                name=cs.subject.name,
                code=cs.subject.code,
                description=cs.subject.description,
                credit_hours=float(cs.subject.credit_hours) if cs.subject.credit_hours else 0,
                subject_type=cs.subject.subject_type.value if cs.subject.subject_type else "theory"
            ),
            teacher=teacher_name
        ))

    return response


@router.post("/class-subjects", response_model=ClassSubjectResponse)
async def create_class_subject(
    data: ClassSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Assign a subject to a class section (Admin only)."""
    school_id = current_user.tenant_id

    # Verify class section exists
    result = await db.execute(
        select(ClassSection)
        .options(
            selectinload(ClassSection.grade_level),
            selectinload(ClassSection.academic_term)
        )
        .where(
            and_(
                ClassSection.id == data.class_section_id,
                ClassSection.school_id == school_id
            )
        )
    )
    section = result.scalar_one_or_none()
    if not section:
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
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=400, detail="Invalid subject")

    # Verify teacher exists
    result = await db.execute(
        select(Teacher).where(Teacher.id == data.teacher_id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=400, detail="Invalid teacher")

    # Check if assignment already exists
    result = await db.execute(
        select(ClassSubject).where(
            and_(
                ClassSubject.class_section_id == data.class_section_id,
                ClassSubject.subject_id == data.subject_id,
                ClassSubject.is_active == True
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject already assigned to this section")

    # Create or get teacher assignment
    teacher_assignment = TeacherAssignment(
        teacher_id=data.teacher_id,
        subject_id=data.subject_id,
        class_section_id=data.class_section_id,
        academic_term_id=section.academic_term_id
    )
    db.add(teacher_assignment)
    await db.flush()

    # Create class subject
    class_subject = ClassSubject(
        class_section_id=data.class_section_id,
        subject_id=data.subject_id,
        teacher_assignment_id=teacher_assignment.id,
        is_active=True
    )
    db.add(class_subject)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ClassSubject)
        .options(
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.grade_level),
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.academic_term),
            selectinload(ClassSubject.subject),
            selectinload(ClassSubject.teacher_assignment).selectinload(TeacherAssignment.teacher).selectinload(Teacher.person)
        )
        .where(ClassSubject.id == class_subject.id)
    )
    cs = result.scalar_one()

    section = cs.class_section
    teacher_name = "Unassigned"
    if cs.teacher_assignment and cs.teacher_assignment.teacher and cs.teacher_assignment.teacher.person:
        teacher_name = f"{cs.teacher_assignment.teacher.person.first_name} {cs.teacher_assignment.teacher.person.last_name}"

    student_count = await get_enrollment_count(db, section.id)

    return ClassSubjectResponse(
        id=cs.id,
        class_section=ClassSectionResponse(
            id=section.id,
            name=section.name,
            grade_level=section.grade_level.name if section.grade_level else "Unknown",
            room_number=section.room_number,
            capacity=section.capacity,
            academic_term=section.academic_term.name if section.academic_term else "Unknown",
            student_count=student_count
        ),
        subject=SubjectResponse(
            id=cs.subject.id,
            name=cs.subject.name,
            code=cs.subject.code,
            description=cs.subject.description,
            credit_hours=float(cs.subject.credit_hours) if cs.subject.credit_hours else 0,
            subject_type=cs.subject.subject_type.value if cs.subject.subject_type else "theory"
        ),
        teacher=teacher_name
    )


@router.put("/class-subjects/{class_subject_id}", response_model=ClassSubjectResponse)
async def update_class_subject(
    class_subject_id: int,
    data: ClassSubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Update a class-subject assignment (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(ClassSubject)
        .options(
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.grade_level),
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.academic_term),
            selectinload(ClassSubject.subject),
            selectinload(ClassSubject.teacher_assignment).selectinload(TeacherAssignment.teacher).selectinload(Teacher.person)
        )
        .where(ClassSubject.id == class_subject_id)
    )
    cs = result.scalar_one_or_none()

    if not cs:
        raise HTTPException(status_code=404, detail="Class subject assignment not found")

    if data.is_active is not None:
        cs.is_active = data.is_active

    if data.teacher_id is not None:
        # Verify new teacher exists
        result = await db.execute(
            select(Teacher).where(Teacher.id == data.teacher_id)
        )
        new_teacher = result.scalar_one_or_none()
        if not new_teacher:
            raise HTTPException(status_code=400, detail="Invalid teacher")

        # Update teacher assignment
        if cs.teacher_assignment:
            cs.teacher_assignment.teacher_id = data.teacher_id
        else:
            # Create new teacher assignment
            teacher_assignment = TeacherAssignment(
                teacher_id=data.teacher_id,
                subject_id=cs.subject_id,
                class_section_id=cs.class_section_id,
                academic_term_id=cs.class_section.academic_term_id
            )
            db.add(teacher_assignment)
            await db.flush()
            cs.teacher_assignment_id = teacher_assignment.id

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ClassSubject)
        .options(
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.grade_level),
            selectinload(ClassSubject.class_section)
            .selectinload(ClassSection.academic_term),
            selectinload(ClassSubject.subject),
            selectinload(ClassSubject.teacher_assignment).selectinload(TeacherAssignment.teacher).selectinload(Teacher.person)
        )
        .where(ClassSubject.id == class_subject_id)
    )
    cs = result.scalar_one()

    section = cs.class_section
    teacher_name = "Unassigned"
    if cs.teacher_assignment and cs.teacher_assignment.teacher and cs.teacher_assignment.teacher.person:
        teacher_name = f"{cs.teacher_assignment.teacher.person.first_name} {cs.teacher_assignment.teacher.person.last_name}"

    student_count = await get_enrollment_count(db, section.id)

    return ClassSubjectResponse(
        id=cs.id,
        class_section=ClassSectionResponse(
            id=section.id,
            name=section.name,
            grade_level=section.grade_level.name if section.grade_level else "Unknown",
            room_number=section.room_number,
            capacity=section.capacity,
            academic_term=section.academic_term.name if section.academic_term else "Unknown",
            student_count=student_count
        ),
        subject=SubjectResponse(
            id=cs.subject.id,
            name=cs.subject.name,
            code=cs.subject.code,
            description=cs.subject.description,
            credit_hours=float(cs.subject.credit_hours) if cs.subject.credit_hours else 0,
            subject_type=cs.subject.subject_type.value if cs.subject.subject_type else "theory"
        ),
        teacher=teacher_name
    )


@router.delete("/class-subjects/{class_subject_id}")
async def delete_class_subject(
    class_subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    """Remove a subject assignment from a class (Admin only)."""
    school_id = current_user.tenant_id

    result = await db.execute(
        select(ClassSubject)
        .join(ClassSection)
        .where(
            and_(
                ClassSubject.id == class_subject_id,
                ClassSection.school_id == school_id
            )
        )
    )
    cs = result.scalar_one_or_none()

    if not cs:
        raise HTTPException(status_code=404, detail="Class subject assignment not found")

    # Soft delete by setting is_active to False
    cs.is_active = False
    await db.commit()

    return {"message": "Subject assignment removed successfully"}

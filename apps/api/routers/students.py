"""Students router - Full CRUD API for student management."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime
import csv
import io

from ..database import get_db
from ..models.student import Student, Enrollment, StudentStatus
from ..models.person import Person, User, UserRole
from ..models.academic import AcademicTerm, GradeLevel, ClassSection
from ..models.attendance import AttendanceRecord, AttendanceStatus
from ..models.gradebook import ExamResult, GradeReport
from pydantic import BaseModel

from ..core.deps import get_current_user
from ..core.security import get_password_hash

router = APIRouter(prefix="/students", tags=["Students"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PersonInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    gender: Optional[str]
    dob: Optional[date]
    phone: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class EnrollmentInfo(BaseModel):
    id: int
    academic_term: str
    grade_level: str
    section: str
    roll_number: Optional[str]
    status: str

    model_config = {"from_attributes": True}


class StudentResponse(BaseModel):
    id: int
    student_id: str  # admission number
    person: PersonInfo
    status: str
    father_name: Optional[str]
    mother_name: Optional[str]
    admission_date: date
    enrollments: List[EnrollmentInfo]

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: date
    phone: Optional[str] = None
    address: Optional[str] = None
    email: str
    password: str
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    grade_level_id: int
    section_id: int
    academic_term_id: int


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    status: Optional[str] = None


class EnrollmentCreate(BaseModel):
    academic_term_id: int
    grade_level_id: int
    section_id: int
    roll_number: Optional[str] = None


class AttendanceInfo(BaseModel):
    id: int
    date: date
    status: str
    class_section: str
    academic_term: str

    model_config = {"from_attributes": True}


class GradeInfo(BaseModel):
    id: int
    exam_name: str
    subject: str
    marks_obtained: float
    max_marks: float
    grade_letter: Optional[str]
    academic_term: str

    model_config = {"from_attributes": True}


class PaginationResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[StudentResponse]


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_student_id(db: AsyncSession) -> str:
    """Generate a unique student ID (e.g., STU-2026-00001)."""
    year = datetime.now().year
    # Get the latest student ID for this year
    result = await db.execute(
        select(func.max(Student.id))
    )
    max_id = result.scalar() or 0
    new_number = max_id + 1
    return f"STU-{year}-{new_number:05d}"


async def get_student_by_id(db: AsyncSession, student_id: int) -> Optional[Student]:
    """Fetch a student by their primary key ID with all relationships."""
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.person),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.academic_term),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.grade_level),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.class_section)
        )
    )
    return result.scalar_one_or_none()


def check_student_access(current_user: User, student: Student) -> bool:
    """Check if current user has access to student data."""
    if current_user.role in [UserRole.ADMIN, UserRole.TEACHER]:
        return True
    # Check if user is the student themselves
    if current_user.role == UserRole.STUDENT and current_user.person and current_user.person.student:
        return current_user.person.student.id == student.id
    return False


def build_enrollment_info(enrollment: Enrollment) -> EnrollmentInfo:
    """Build EnrollmentInfo from Enrollment model."""
    return EnrollmentInfo(
        id=enrollment.id,
        academic_term=enrollment.academic_term.name if enrollment.academic_term else "",
        grade_level=enrollment.grade_level.name if enrollment.grade_level else "",
        section=enrollment.class_section.name if enrollment.class_section else "",
        roll_number=enrollment.roll_number,
        status=enrollment.status
    )


def build_student_response(student: Student, email: Optional[str] = None) -> StudentResponse:
    """Build StudentResponse from Student model."""
    enrollments = [build_enrollment_info(e) for e in student.enrollments] if student.enrollments else []
    
    person_info = PersonInfo(
        id=student.person.id,
        first_name=student.person.first_name,
        last_name=student.person.last_name,
        gender=student.person.gender,
        dob=student.person.dob.date() if student.person.dob else None,
        phone=student.person.phone,
        address=student.person.address,
        emergency_contact=student.person.emergency_contact,
        emergency_phone=student.person.emergency_phone,
        email=email
    )
    
    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        person=person_info,
        status=student.status.value if isinstance(student.status, StudentStatus) else student.status,
        father_name=student.father_name,
        mother_name=student.mother_name,
        admission_date=student.admission_date,
        enrollments=enrollments
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=PaginationResponse)
async def list_students(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive, graduated, transferred, expelled)"),
    grade_level_id: Optional[int] = Query(None, description="Filter by grade level"),
    section_id: Optional[int] = Query(None, description="Filter by section"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all students with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (1-100)
    - **status**: Filter by student status
    - **grade_level_id**: Filter by grade level
    - **section_id**: Filter by section
    - **search**: Search by student name or email
    """
    # Only admin can list all students
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list all students"
        )
    
    # Build base query
    query = (
        select(Student)
        .options(
            selectinload(Student.person),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.academic_term),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.grade_level),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.class_section)
        )
    )
    count_query = select(func.count(Student.id))
    
    # Apply filters
    filters = []
    
    if status:
        try:
            status_enum = StudentStatus(status.lower())
            filters.append(Student.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Must be one of: active, inactive, graduated, transferred, expelled"
            )
    
    if grade_level_id:
        filters.append(Enrollment.grade_level_id == grade_level_id)
        query = query.join(Student.enrollments)
        count_query = count_query.join(Student.enrollments)
    
    if section_id:
        filters.append(Enrollment.section_id == section_id)
    
    if search:
        search_filter = or_(
            Person.first_name.ilike(f"%{search}%"),
            Person.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        filters.append(search_filter)
        query = query.join(Student.person).join(Person.user)
        count_query = count_query.join(Student.person).join(Person.user)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(Student.id.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Get emails for students
    student_ids = [s.id for s in students]
    emails_query = (
        select(Person.id, User.email)
        .join(User, Person.user_id == User.id)
        .where(Person.id.in_([s.person_id for s in students]))
    )
    emails_result = await db.execute(emails_query)
    emails_map = {row[0]: row[1] for row in emails_result.all()}
    
    # Build response
    data = [build_student_response(s, emails_map.get(s.person_id)) for s in students]
    
    return PaginationResponse(total=total, skip=skip, limit=limit, data=data)


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new student.
    
    Creates:
    - Person record with personal info
    - User account for login (role: student)
    - Student record with admission number
    - Initial enrollment in specified grade/section/term
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create students"
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == student_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate grade_level exists
    result = await db.execute(
        select(GradeLevel).where(GradeLevel.id == student_data.grade_level_id)
    )
    grade_level = result.scalar_one_or_none()
    if not grade_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grade level with id {student_data.grade_level_id} not found"
        )
    
    # Validate section exists
    result = await db.execute(
        select(ClassSection).where(ClassSection.id == student_data.section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with id {student_data.section_id} not found"
        )
    
    # Validate academic term exists
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == student_data.academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    if not academic_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic term with id {student_data.academic_term_id} not found"
        )
    
    # Generate student ID
    student_id = await generate_student_id(db)
    
    # Get tenant_id from current user
    tenant_id = current_user.tenant_id
    
    # Create user account
    user = User(
        email=student_data.email,
        password_hash=get_password_hash(student_data.password),
        role=UserRole.STUDENT,
        is_active=True,
        tenant_id=tenant_id
    )
    db.add(user)
    await db.flush()
    
    # Create person
    person = Person(
        user_id=user.id,
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        gender=student_data.gender,
        dob=datetime.combine(student_data.dob, datetime.min.time()),
        phone=student_data.phone,
        address=student_data.address,
        emergency_contact=student_data.emergency_contact,
        emergency_phone=student_data.emergency_phone
    )
    db.add(person)
    await db.flush()
    
    # Create student
    student = Student(
        person_id=person.id,
        student_id=student_id,
        admission_date=datetime.now().date(),
        status=StudentStatus.ACTIVE,
        father_name=student_data.father_name,
        mother_name=student_data.mother_name
    )
    db.add(student)
    await db.flush()
    
    # Create initial enrollment
    enrollment = Enrollment(
        student_id=student.id,
        academic_term_id=academic_term.id,
        grade_level_id=grade_level.id,
        section_id=section.id,
        status="active"
    )
    db.add(enrollment)
    
    await db.commit()
    
    # Refresh to load relationships
    await db.refresh(student)
    
    # Load relationships
    result = await db.execute(
        select(Student)
        .where(Student.id == student.id)
        .options(
            selectinload(Student.person),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.academic_term),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.grade_level),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.class_section)
        )
    )
    student = result.scalar_one()
    
    return build_student_response(student, student_data.email)


@router.get("/search", response_model=List[StudentResponse])
async def search_students(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search students by name or email.
    
    - **q**: Search query (minimum 2 characters)
    - **limit**: Maximum number of results (1-50)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and teachers can search students"
        )
    
    query = (
        select(Student)
        .join(Student.person)
        .join(Person.user)
        .where(
            or_(
                Person.first_name.ilike(f"%{q}%"),
                Person.last_name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                Student.student_id.ilike(f"%{q}%")
            )
        )
        .options(
            selectinload(Student.person),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.academic_term),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.grade_level),
            selectinload(Student.enrollments)
            .selectinload(Enrollment.class_section)
        )
        .limit(limit)
    )
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Get emails
    student_ids = [s.id for s in students]
    emails_query = (
        select(Person.id, User.email)
        .join(User, Person.user_id == User.id)
        .where(Person.id.in_([s.person_id for s in students]))
    )
    emails_result = await db.execute(emails_query)
    emails_map = {row[0]: row[1] for row in emails_result.all()}
    
    return [build_student_response(s, emails_map.get(s.person_id)) for s in students]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a student by ID.
    
    Access:
    - Admins can view any student
    - Teachers can view any student
    - Students can view only their own record
    """
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Check access
    if not check_student_access(current_user, student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this student"
        )
    
    # Get email
    email = None
    if student.person and student.person.user_id:
        result = await db.execute(select(User.email).where(User.id == student.person.user_id))
        email = result.scalar_one_or_none()
    
    return build_student_response(student, email)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a student.
    
    Only administrators can update student information.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update students"
        )
    
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Update person fields
    if student_data.first_name:
        student.person.first_name = student_data.first_name
    if student_data.last_name:
        student.person.last_name = student_data.last_name
    if student_data.gender:
        student.person.gender = student_data.gender
    if student_data.dob:
        student.person.dob = datetime.combine(student_data.dob, datetime.min.time())
    if student_data.phone:
        student.person.phone = student_data.phone
    if student_data.address:
        student.person.address = student_data.address
    if student_data.emergency_contact:
        student.person.emergency_contact = student_data.emergency_contact
    if student_data.emergency_phone:
        student.person.emergency_phone = student_data.emergency_phone
    
    # Update student fields
    if student_data.father_name:
        student.father_name = student_data.father_name
    if student_data.mother_name:
        student.mother_name = student_data.mother_name
    if student_data.status:
        try:
            student.status = StudentStatus(student_data.status.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {student_data.status}"
            )
    
    await db.commit()
    await db.refresh(student)
    
    # Get email
    email = None
    if student.person and student.person.user_id:
        result = await db.execute(select(User.email).where(User.id == student.person.user_id))
        email = result.scalar_one_or_none()
    
    return build_student_response(student, email)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a student (soft delete - sets status to inactive).
    
    Only administrators can delete students.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete students"
        )
    
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Soft delete - set status to inactive
    student.status = StudentStatus.INACTIVE
    await db.commit()


@router.get("/{student_id}/enrollments", response_model=List[EnrollmentInfo])
async def get_student_enrollments(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all enrollments for a student.
    
    Access:
    - Admins can view any student's enrollments
    - Students can view only their own enrollments
    """
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Check access
    if not check_student_access(current_user, student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this student's enrollments"
        )
    
    # Load enrollments with relationships
    result = await db.execute(
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .options(
            selectinload(Enrollment.academic_term),
            selectinload(Enrollment.grade_level),
            selectinload(Enrollment.class_section)
        )
    )
    enrollments = result.scalars().all()
    
    return [build_enrollment_info(e) for e in enrollments]


@router.post("/{student_id}/enroll", response_model=EnrollmentInfo, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    student_id: int,
    enrollment_data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll a student in a new academic term.
    
    Only administrators can enroll students.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can enroll students"
        )
    
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Validate grade_level exists
    result = await db.execute(
        select(GradeLevel).where(GradeLevel.id == enrollment_data.grade_level_id)
    )
    grade_level = result.scalar_one_or_none()
    if not grade_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grade level with id {enrollment_data.grade_level_id} not found"
        )
    
    # Validate section exists
    result = await db.execute(
        select(ClassSection).where(ClassSection.id == enrollment_data.section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with id {enrollment_data.section_id} not found"
        )
    
    # Validate academic term exists
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == enrollment_data.academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    if not academic_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic term with id {enrollment_data.academic_term_id} not found"
        )
    
    # Check if already enrolled in this term/section
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.academic_term_id == enrollment_data.academic_term_id,
                Enrollment.section_id == enrollment_data.section_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this section for the specified term"
        )
    
    # Create enrollment
    enrollment = Enrollment(
        student_id=student_id,
        academic_term_id=academic_term.id,
        grade_level_id=grade_level.id,
        section_id=section.id,
        roll_number=enrollment_data.roll_number,
        status="active"
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    
    # Load relationships
    result = await db.execute(
        select(Enrollment)
        .where(Enrollment.id == enrollment.id)
        .options(
            selectinload(Enrollment.academic_term),
            selectinload(Enrollment.grade_level),
            selectinload(Enrollment.class_section)
        )
    )
    enrollment = result.scalar_one()
    
    return build_enrollment_info(enrollment)


@router.get("/{student_id}/attendance", response_model=List[AttendanceInfo])
async def get_student_attendance(
    student_id: int,
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get attendance records for a student.
    
    Access:
    - Admins can view any student's attendance
    - Teachers can view any student's attendance
    - Students can view only their own attendance
    """
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Check access
    if not check_student_access(current_user, student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this student's attendance"
        )
    
    # Build query
    query = (
        select(AttendanceRecord)
        .where(AttendanceRecord.student_id == student_id)
        .options(
            selectinload(AttendanceRecord.class_section),
            selectinload(AttendanceRecord.academic_term)
        )
    )
    
    if academic_term_id:
        query = query.where(AttendanceRecord.academic_term_id == academic_term_id)
    
    if start_date:
        query = query.where(AttendanceRecord.date >= start_date)
    
    if end_date:
        query = query.where(AttendanceRecord.date <= end_date)
    
    query = query.order_by(AttendanceRecord.date.desc())
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    return [
        AttendanceInfo(
            id=r.id,
            date=r.date,
            status=r.status.value if hasattr(r.status, 'value') else r.status,
            class_section=r.class_section.name if r.class_section else "",
            academic_term=r.academic_term.name if r.academic_term else ""
        )
        for r in records
    ]


@router.get("/{student_id}/grades", response_model=List[GradeInfo])
async def get_student_grades(
    student_id: int,
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get grade/exam results for a student.
    
    Access:
    - Admins can view any student's grades
    - Teachers can view any student's grades
    - Students can view only their own grades
    """
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )
    
    # Check access
    if not check_student_access(current_user, student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this student's grades"
        )
    
    # Build query
    query = (
        select(ExamResult)
        .where(ExamResult.student_id == student_id)
        .options(
            selectinload(ExamResult.exam)
            .selectinload(ExamResult.exam.subject),
            selectinload(ExamResult.exam)
            .selectinload(ExamResult.exam.academic_term),
            selectinload(ExamResult.grade)
        )
    )
    
    if academic_term_id:
        query = query.join(ExamResult.exam).where(Exam.exam_id == academic_term_id)
    
    query = query.order_by(ExamResult.graded_at.desc())
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    grades = []
    for r in results:
        exam = r.exam
        grades.append(GradeInfo(
            id=r.id,
            exam_name=exam.name if exam else "",
            subject=exam.subject.name if exam and exam.subject else "",
            marks_obtained=float(r.marks_obtained) if r.marks_obtained else 0.0,
            max_marks=float(exam.max_marks) if exam and exam.max_marks else 0.0,
            grade_letter=r.grade.letter if r.grade else None,
            academic_term=exam.academic_term.name if exam and exam.academic_term else ""
        ))
    
    return grades


@router.post("/bulk-import", status_code=status.HTTP_201_CREATED)
async def bulk_import_students(
    file_content: str = Query(..., description="CSV file content"),
    grade_level_id: int = Query(..., description="Default grade level ID for imported students"),
    section_id: int = Query(..., description="Default section ID for imported students"),
    academic_term_id: int = Query(..., description="Academic term ID for enrollment"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import students from CSV.
    
    CSV format (header required):
    first_name,last_name,gender,dob,email,password,phone,address,father_name,mother_name
    
    Only administrators can import students.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can import students"
        )
    
    # Validate grade_level
    result = await db.execute(
        select(GradeLevel).where(GradeLevel.id == grade_level_id)
    )
    grade_level = result.scalar_one_or_none()
    if not grade_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grade level with id {grade_level_id} not found"
        )
    
    # Validate section
    result = await db.execute(
        select(ClassSection).where(ClassSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with id {section_id} not found"
        )
    
    # Validate academic term
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    if not academic_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic term with id {academic_term_id} not found"
        )
    
    # Parse CSV
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {str(e)}"
        )
    
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty"
        )
    
    # Required fields
    required_fields = ["first_name", "last_name", "gender", "dob", "email", "password"]
    for field in required_fields:
        if field not in rows[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    imported = 0
    errors = []
    tenant_id = current_user.tenant_id
    
    for i, row in enumerate(rows):
        try:
            # Check if email exists
            result = await db.execute(select(User).where(User.email == row["email"]))
            if result.scalar_one_or_none():
                errors.append(f"Row {i+2}: Email {row['email']} already registered")
                continue
            
            # Parse date
            try:
                dob = datetime.strptime(row["dob"], "%Y-%m-%d").date()
            except ValueError:
                try:
                    dob = datetime.strptime(row["dob"], "%d/%m/%Y").date()
                except ValueError:
                    errors.append(f"Row {i+2}: Invalid date format for dob")
                    continue
            
            # Generate student ID
            student_id = await generate_student_id(db)
            
            # Create user
            user = User(
                email=row["email"],
                password_hash=get_password_hash(row["password"]),
                role=UserRole.STUDENT,
                is_active=True,
                tenant_id=tenant_id
            )
            db.add(user)
            await db.flush()
            
            # Create person
            person = Person(
                user_id=user.id,
                first_name=row["first_name"],
                last_name=row["last_name"],
                gender=row["gender"],
                dob=datetime.combine(dob, datetime.min.time()),
                phone=row.get("phone"),
                address=row.get("address"),
                emergency_contact=row.get("father_name"),
                emergency_phone=row.get("mother_name")
            )
            db.add(person)
            await db.flush()
            
            # Create student
            student = Student(
                person_id=person.id,
                student_id=student_id,
                admission_date=datetime.now().date(),
                status=StudentStatus.ACTIVE,
                father_name=row.get("father_name"),
                mother_name=row.get("mother_name")
            )
            db.add(student)
            await db.flush()
            
            # Create enrollment
            enrollment = Enrollment(
                student_id=student.id,
                academic_term_id=academic_term_id,
                grade_level_id=grade_level_id,
                section_id=section_id,
                status="active"
            )
            db.add(enrollment)
            
            imported += 1
            
        except Exception as e:
            errors.append(f"Row {i+2}: {str(e)}")
    
    await db.commit()
    
    return {
        "imported": imported,
        "errors": errors,
        "total_rows": len(rows)
    }

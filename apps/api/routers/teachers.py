"""Teachers router with full CRUD operations."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime

from ..database import get_db
from ..models.teacher import Teacher, TeacherAssignment
from ..models.person import Person, User, UserRole
from ..models.academic import Department, Subject, ClassSection, AcademicTerm
from ..models.scheduling import Schedule
from ..core.deps import get_current_user, require_roles
from ..core.security import get_password_hash

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# =============================================================================
# Pydantic Schemas (Pydantic v2)
# =============================================================================

from pydantic import BaseModel, EmailStr, ConfigDict


class PersonInfo(BaseModel):
    """Person information nested in teacher response."""
    model_config = {"from_attributes": True}
    
    id: int
    first_name: str
    last_name: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: str


class DepartmentInfo(BaseModel):
    """Department information in teacher response."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    head_teacher_id: Optional[int] = None


class TeacherResponse(BaseModel):
    """Full teacher response schema."""
    model_config = {"from_attributes": True}
    
    id: int
    employee_id: str
    designation: Optional[str] = None
    salary: Optional[int] = None
    hire_date: date
    is_active: bool
    person: PersonInfo
    department: Optional[DepartmentInfo] = None


class TeacherCreate(BaseModel):
    """Schema for creating a teacher."""
    first_name: str
    last_name: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: str
    password: str
    employee_id: Optional[str] = None
    department_id: Optional[int] = None
    designation: Optional[str] = None
    salary: Optional[int] = None
    hire_date: Optional[date] = None


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    department_id: Optional[int] = None
    designation: Optional[str] = None
    salary: Optional[int] = None
    is_active: Optional[bool] = None


class TeacherListResponse(BaseModel):
    """Paginated teacher list response."""
    model_config = {"from_attributes": True}
    
    id: int
    employee_id: str
    designation: Optional[str] = None
    is_active: bool
    person: PersonInfo
    department: Optional[DepartmentInfo] = None


class TeacherAssignmentResponse(BaseModel):
    """Teacher assignment response schema."""
    model_config = {"from_attributes": True}
    
    id: int
    teacher_id: int
    subject_id: int
    class_section_id: int
    academic_term_id: int
    subject_name: Optional[str] = None
    class_section_name: Optional[str] = None
    academic_term_name: Optional[str] = None


class TeacherAssignmentCreate(BaseModel):
    """Schema for creating a teacher assignment."""
    teacher_id: int
    subject_id: int
    class_section_id: int
    academic_term_id: int


class TeacherAssignmentUpdate(BaseModel):
    """Schema for updating a teacher assignment."""
    subject_id: Optional[int] = None
    class_section_id: Optional[int] = None
    academic_term_id: Optional[int] = None


class DepartmentResponse(BaseModel):
    """Department response schema."""
    model_config = {"from_attributes": True}
    
    id: int
    school_id: int
    name: str
    head_teacher_id: Optional[int] = None


class DepartmentCreate(BaseModel):
    """Schema for creating a department."""
    school_id: int
    name: str
    head_teacher_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    name: Optional[str] = None
    head_teacher_id: Optional[int] = None


class ScheduleResponse(BaseModel):
    """Schedule/timetable entry response."""
    model_config = {"from_attributes": True}
    
    id: int
    class_section_id: int
    subject_id: int
    teacher_id: int
    day_of_week: int
    period_number: int
    room_number: Optional[str] = None
    start_time: datetime
    end_time: datetime
    academic_term_id: int
    class_section_name: Optional[str] = None
    subject_name: Optional[str] = None


class PaginatedTeacherResponse(BaseModel):
    """Paginated response for teacher list."""
    items: List[TeacherListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Helper Functions
# =============================================================================

async def generate_employee_id(db: AsyncSession, school_id: Optional[int] = None) -> str:
    """Generate unique employee ID in format EMP-YYYY-NNNNN."""
    current_year = datetime.now().year
    
    # Get the latest employee_id to determine the sequence
    result = await db.execute(
        select(Teacher.employee_id).order_by(Teacher.id.desc()).limit(1)
    )
    last_employee_id = result.scalar_one_or_none()
    
    if last_employee_id:
        # Extract sequence number from last ID (format: EMP-YYYY-NNNNN)
        try:
            last_seq = int(last_employee_id.split("-")[-1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1
    
    return f"EMP-{current_year}-{new_seq:05d}"


async def get_teacher_by_user_id(db: AsyncSession, user_id: int) -> Optional[Teacher]:
    """Get teacher by user ID."""
    result = await db.execute(
        select(Teacher).join(Person).where(Person.user_id == user_id)
    )
    return result.scalar_one_or_none()


# =============================================================================
# Teacher Endpoints
# =============================================================================

@router.get("/", response_model=PaginatedTeacherResponse)
async def list_teachers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or employee ID"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """
    List all teachers with pagination and filtering.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **search**: Search by first name, last name, or employee ID
    - **department_id**: Filter by department
    - **is_active**: Filter by active status
    """
    # Build base query with joins
    query = (
        select(Teacher)
        .join(Person, Teacher.person_id == Person.id)
        .options(selectinload(Teacher.person), selectinload(Teacher.department))
    )
    count_query = select(func.count(Teacher.id)).join(Person, Teacher.person_id == Person.id)
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Person.first_name.ilike(search_filter)) |
            (Person.last_name.ilike(search_filter)) |
            (Teacher.employee_id.ilike(search_filter))
        )
        count_query = count_query.where(
            (Person.first_name.ilike(search_filter)) |
            (Person.last_name.ilike(search_filter)) |
            (Teacher.employee_id.ilike(search_filter))
        )
    
    if department_id is not None:
        query = query.where(Teacher.department_id == department_id)
        count_query = count_query.where(Teacher.department_id == department_id)
    
    if is_active is not None:
        query = query.where(Teacher.is_active == is_active)
        count_query = count_query.where(Teacher.is_active == is_active)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Teacher.id.desc())
    
    result = await db.execute(query)
    teachers = result.scalars().all()
    
    return PaginatedTeacherResponse(
        items=[TeacherListResponse(
            id=t.id,
            employee_id=t.employee_id,
            designation=t.designation,
            is_active=t.is_active,
            person=PersonInfo(
                id=t.person.id,
                first_name=t.person.first_name,
                last_name=t.person.last_name,
                gender=t.person.gender,
                dob=t.person.dob.date() if t.person.dob else None,
                phone=t.person.phone,
                address=t.person.address,
                email=t.person.user.email if t.person.user else ""
            ),
            department=DepartmentInfo(
                id=t.department.id,
                name=t.department.name,
                head_teacher_id=t.department.head_teacher_id
            ) if t.department else None
        ) for t in teachers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Create a new teacher with associated person and user accounts.
    
    - Creates Person record with personal information
    - Creates User account with 'teacher' role for login
    - Creates Teacher record linked to person
    - Auto-generates employee_id if not provided
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == teacher_data.email)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if department exists (if provided)
    if teacher_data.department_id:
        result = await db.execute(
            select(Department).where(Department.id == teacher_data.department_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    
    # Use provided employee_id or generate new one
    employee_id = teacher_data.employee_id
    if not employee_id:
        # Get school_id from department if available, otherwise from admin's tenant
        school_id = None
        if teacher_data.department_id:
            result = await db.execute(
                select(Department.school_id).where(Department.id == teacher_data.department_id)
            )
            school_id = result.scalar_one_or_none()
        employee_id = await generate_employee_id(db, school_id)
    else:
        # Check if employee_id already exists
        result = await db.execute(
            select(Teacher).where(Teacher.employee_id == employee_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
    
    # Use current user or default values
    hire_date = teacher_data.hire_date or date.today()
    
    try:
        # Create Person
        person = Person(
            first_name=teacher_data.first_name,
            last_name=teacher_data.last_name,
            gender=teacher_data.gender,
            dob=teacher_data.dob,
            phone=teacher_data.phone,
            address=teacher_data.address,
        )
        db.add(person)
        await db.flush()  # Get person.id
        
        # Create User account
        user = User(
            email=teacher_data.email,
            password_hash=get_password_hash(teacher_data.password),
            role=UserRole.TEACHER,
            tenant_id=current_user.tenant_id,
            is_active=True,
        )
        db.add(user)
        await db.flush()  # Get user.id
        
        # Link person to user
        person.user_id = user.id
        
        # Create Teacher
        teacher = Teacher(
            person_id=person.id,
            employee_id=employee_id,
            department_id=teacher_data.department_id,
            designation=teacher_data.designation,
            salary=teacher_data.salary,
            hire_date=hire_date,
            is_active=True,
        )
        db.add(teacher)
        await db.flush()
        
        # Refresh with relationships
        await db.refresh(teacher)
        await db.refresh(person)
        await db.refresh(user)
        
        return TeacherResponse(
            id=teacher.id,
            employee_id=teacher.employee_id,
            designation=teacher.designation,
            salary=teacher.salary,
            hire_date=teacher.hire_date,
            is_active=teacher.is_active,
            person=PersonInfo(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                gender=person.gender,
                dob=person.dob.date() if person.dob else None,
                phone=person.phone,
                address=person.address,
                email=user.email
            ),
            department=DepartmentInfo(
                id=teacher.department.id,
                name=teacher.department.name,
                head_teacher_id=teacher.department.head_teacher_id
            ) if teacher.department else None
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create teacher: {str(e)}"
        )


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get teacher by ID.
    
    - Admins can view any teacher
    - Teachers can view their own profile
    """
    # Check if user is admin or the teacher themselves
    if current_user.role != "admin":
        # Check if the current user is the teacher
        result = await db.execute(
            select(Teacher).join(Person).where(Person.user_id == current_user.id)
        )
        current_teacher = result.scalar_one_or_none()
        if not current_teacher or current_teacher.id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this teacher"
            )
    
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.person).selectinload(Person.user), selectinload(Teacher.department))
    )
    teacher = result.scalar_one_or_none()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return TeacherResponse(
        id=teacher.id,
        employee_id=teacher.employee_id,
        designation=teacher.designation,
        salary=teacher.salary,
        hire_date=teacher.hire_date,
        is_active=teacher.is_active,
        person=PersonInfo(
            id=teacher.person.id,
            first_name=teacher.person.first_name,
            last_name=teacher.person.last_name,
            gender=teacher.person.gender,
            dob=teacher.person.dob.date() if teacher.person.dob else None,
            phone=teacher.person.phone,
            address=teacher.person.address,
            email=teacher.person.user.email if teacher.person.user else ""
        ),
        department=DepartmentInfo(
            id=teacher.department.id,
            name=teacher.department.name,
            head_teacher_id=teacher.department.head_teacher_id
        ) if teacher.department else None
    )


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Update teacher information.
    
    - Only admins can update teachers
    - Partial updates supported (only provided fields are updated)
    """
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.person), selectinload(Teacher.department))
    )
    teacher = result.scalar_one_or_none()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Update person fields if provided
    person = teacher.person
    if teacher_data.first_name is not None:
        person.first_name = teacher_data.first_name
    if teacher_data.last_name is not None:
        person.last_name = teacher_data.last_name
    if teacher_data.gender is not None:
        person.gender = teacher_data.gender
    if teacher_data.dob is not None:
        person.dob = teacher_data.dob
    if teacher_data.phone is not None:
        person.phone = teacher_data.phone
    if teacher_data.address is not None:
        person.address = teacher_data.address
    
    # Update teacher fields if provided
    if teacher_data.department_id is not None:
        # Verify department exists
        result = await db.execute(
            select(Department).where(Department.id == teacher_data.department_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        teacher.department_id = teacher_data.department_id
    
    if teacher_data.designation is not None:
        teacher.designation = teacher_data.designation
    if teacher_data.salary is not None:
        teacher.salary = teacher_data.salary
    if teacher_data.is_active is not None:
        teacher.is_active = teacher_data.is_active
    
    await db.flush()
    await db.refresh(teacher)
    await db.refresh(person)
    
    # Reload department relationship
    await db.refresh(teacher.department)
    
    return TeacherResponse(
        id=teacher.id,
        employee_id=teacher.employee_id,
        designation=teacher.designation,
        salary=teacher.salary,
        hire_date=teacher.hire_date,
        is_active=teacher.is_active,
        person=PersonInfo(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            gender=person.gender,
            dob=person.dob.date() if person.dob else None,
            phone=person.phone,
            address=person.address,
            email=person.user.email if person.user else ""
        ),
        department=DepartmentInfo(
            id=teacher.department.id,
            name=teacher.department.name,
            head_teacher_id=teacher.department.head_teacher_id
        ) if teacher.department else None
    )


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Deactivate a teacher (soft delete).
    
    - Sets is_active to False
    - Does not delete associated records
    - Only admins can deactivate teachers
    """
    result = await db.execute(
        select(Teacher).where(Teacher.id == teacher_id)
    )
    teacher = result.scalar_one_or_none()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    teacher.is_active = False
    
    # Also deactivate the associated user account
    await db.refresh(teacher)
    if teacher.person and teacher.person.user:
        teacher.person.user.is_active = False
    
    await db.flush()


@router.get("/{teacher_id}/assignments", response_model=List[TeacherAssignmentResponse])
async def get_teacher_assignments(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
):
    """
    Get teaching assignments for a teacher.
    
    - Admins can view any teacher's assignments
    - Teachers can view their own assignments
    - Optionally filter by academic term
    """
    # Check permissions
    if current_user.role != "admin":
        result = await db.execute(
            select(Teacher).join(Person).where(Person.user_id == current_user.id)
        )
        current_teacher = result.scalar_one_or_none()
        if not current_teacher or current_teacher.id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these assignments"
            )
    
    # Verify teacher exists
    result = await db.execute(
        select(Teacher).where(Teacher.id == teacher_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Build query
    query = (
        select(TeacherAssignment)
        .where(TeacherAssignment.teacher_id == teacher_id)
        .options(
            selectinload(TeacherAssignment.subject),
            selectinload(TeacherAssignment.class_section),
            selectinload(TeacherAssignment.academic_term)
        )
    )
    
    if academic_term_id:
        query = query.where(TeacherAssignment.academic_term_id == academic_term_id)
    
    result = await db.execute(query)
    assignments = result.scalars().all()
    
    return [
        TeacherAssignmentResponse(
            id=a.id,
            teacher_id=a.teacher_id,
            subject_id=a.subject_id,
            class_section_id=a.class_section_id,
            academic_term_id=a.academic_term_id,
            subject_name=a.subject.name if a.subject else None,
            class_section_name=a.class_section.name if a.class_section else None,
            academic_term_name=a.academic_term.name if a.academic_term else None
        )
        for a in assignments
    ]


# =============================================================================
# Teacher Assignment Endpoints
# =============================================================================

@router.post("/assignments", response_model=TeacherAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: TeacherAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Assign a teacher to a subject in a class section for an academic term.
    
    - Validates teacher, subject, class section, and academic term exist
    - Checks for duplicate assignments
    """
    # Verify teacher exists
    result = await db.execute(
        select(Teacher).where(Teacher.id == assignment_data.teacher_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Verify subject exists
    result = await db.execute(
        select(Subject).where(Subject.id == assignment_data.subject_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Verify class section exists
    result = await db.execute(
        select(ClassSection).where(ClassSection.id == assignment_data.class_section_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class section not found"
        )
    
    # Verify academic term exists
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == assignment_data.academic_term_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic term not found"
        )
    
    # Check for duplicate assignment
    result = await db.execute(
        select(TeacherAssignment).where(
            and_(
                TeacherAssignment.teacher_id == assignment_data.teacher_id,
                TeacherAssignment.subject_id == assignment_data.subject_id,
                TeacherAssignment.class_section_id == assignment_data.class_section_id,
                TeacherAssignment.academic_term_id == assignment_data.academic_term_id
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already exists for this teacher, subject, class, and term"
        )
    
    # Create assignment
    assignment = TeacherAssignment(
        teacher_id=assignment_data.teacher_id,
        subject_id=assignment_data.subject_id,
        class_section_id=assignment_data.class_section_id,
        academic_term_id=assignment_data.academic_term_id,
    )
    db.add(assignment)
    await db.flush()
    
    # Load relationships for response
    await db.refresh(assignment)
    
    return TeacherAssignmentResponse(
        id=assignment.id,
        teacher_id=assignment.teacher_id,
        subject_id=assignment.subject_id,
        class_section_id=assignment.class_section_id,
        academic_term_id=assignment.academic_term_id,
        subject_name=assignment.subject.name if assignment.subject else None,
        class_section_name=assignment.class_section.name if assignment.class_section else None,
        academic_term_name=assignment.academic_term.name if assignment.academic_term else None
    )


@router.put("/assignments/{assignment_id}", response_model=TeacherAssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: TeacherAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Update a teacher assignment.
    
    - Only admins can update assignments
    - Partial updates supported
    """
    result = await db.execute(
        select(TeacherAssignment)
        .where(TeacherAssignment.id == assignment_id)
        .options(
            selectinload(TeacherAssignment.subject),
            selectinload(TeacherAssignment.class_section),
            selectinload(TeacherAssignment.academic_term)
        )
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Update fields if provided
    if assignment_data.subject_id is not None:
        result = await db.execute(
            select(Subject).where(Subject.id == assignment_data.subject_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        assignment.subject_id = assignment_data.subject_id
    
    if assignment_data.class_section_id is not None:
        result = await db.execute(
            select(ClassSection).where(ClassSection.id == assignment_data.class_section_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class section not found"
            )
        assignment.class_section_id = assignment_data.class_section_id
    
    if assignment_data.academic_term_id is not None:
        result = await db.execute(
            select(AcademicTerm).where(AcademicTerm.id == assignment_data.academic_term_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic term not found"
            )
        assignment.academic_term_id = assignment_data.academic_term_id
    
    await db.flush()
    await db.refresh(assignment)
    
    return TeacherAssignmentResponse(
        id=assignment.id,
        teacher_id=assignment.teacher_id,
        subject_id=assignment.subject_id,
        class_section_id=assignment.class_section_id,
        academic_term_id=assignment.academic_term_id,
        subject_name=assignment.subject.name if assignment.subject else None,
        class_section_name=assignment.class_section.name if assignment.class_section else None,
        academic_term_name=assignment.academic_term.name if assignment.academic_term else None
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Remove a teacher assignment.
    
    - Only admins can delete assignments
    """
    result = await db.execute(
        select(TeacherAssignment).where(TeacherAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    await db.delete(assignment)
    await db.flush()


# =============================================================================
# Department Endpoints
# =============================================================================

@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school_id: Optional[int] = Query(None, description="Filter by school"),
):
    """
    List all departments.
    
    - All authenticated users can view departments
    - Optionally filter by school
    """
    query = select(Department)
    if school_id:
        query = query.where(Department.school_id == school_id)
    
    result = await db.execute(query)
    departments = result.scalars().all()
    
    return [DepartmentResponse(
        id=d.id,
        school_id=d.school_id,
        name=d.name,
        head_teacher_id=d.head_teacher_id
    ) for d in departments]


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Create a new department.
    
    - Only admins can create departments
    """
    # Verify school exists
    from ..models.tenant import School
    result = await db.execute(
        select(School).where(School.id == department_data.school_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Verify head_teacher exists if provided
    if department_data.head_teacher_id:
        result = await db.execute(
            select(Teacher).where(Teacher.id == department_data.head_teacher_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Head teacher not found"
            )
    
    department = Department(
        school_id=department_data.school_id,
        name=department_data.name,
        head_teacher_id=department_data.head_teacher_id
    )
    db.add(department)
    await db.flush()
    await db.refresh(department)
    
    return DepartmentResponse(
        id=department.id,
        school_id=department.school_id,
        name=department.name,
        head_teacher_id=department.head_teacher_id
    )


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Update a department.
    
    - Only admins can update departments
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    if department_data.name is not None:
        department.name = department_data.name
    
    if department_data.head_teacher_id is not None:
        # Verify head_teacher exists
        result = await db.execute(
            select(Teacher).where(Teacher.id == department_data.head_teacher_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Head teacher not found"
            )
        department.head_teacher_id = department_data.head_teacher_id
    
    await db.flush()
    await db.refresh(department)
    
    return DepartmentResponse(
        id=department.id,
        school_id=department.school_id,
        name=department.name,
        head_teacher_id=department.head_teacher_id
    )


# =============================================================================
# Schedule/Timetable Endpoint
# =============================================================================

@router.get("/{teacher_id}/schedule", response_model=List[ScheduleResponse])
async def get_teacher_schedule(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    day_of_week: Optional[int] = Query(None, ge=0, le=6, description="Filter by day (0=Monday, 6=Sunday)"),
):
    """
    Get teacher's timetable/schedule.
    
    - Admins can view any teacher's schedule
    - Teachers can view their own schedule
    - Optionally filter by academic term and day of week
    """
    # Check permissions
    if current_user.role != "admin":
        result = await db.execute(
            select(Teacher).join(Person).where(Person.user_id == current_user.id)
        )
        current_teacher = result.scalar_one_or_none()
        if not current_teacher or current_teacher.id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this schedule"
            )
    
    # Verify teacher exists
    result = await db.execute(
        select(Teacher).where(Teacher.id == teacher_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Build query
    query = (
        select(Schedule)
        .where(Schedule.teacher_id == teacher_id)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject)
        )
    )
    
    if academic_term_id:
        query = query.where(Schedule.academic_term_id == academic_term_id)
    
    if day_of_week is not None:
        query = query.where(Schedule.day_of_week == day_of_week)
    
    query = query.order_by(Schedule.day_of_week, Schedule.period_number)
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    return [
        ScheduleResponse(
            id=s.id,
            class_section_id=s.class_section_id,
            subject_id=s.subject_id,
            teacher_id=s.teacher_id,
            day_of_week=s.day_of_week,
            period_number=s.period_number,
            room_number=s.room_number,
            start_time=s.start_time,
            end_time=s.end_time,
            academic_term_id=s.academic_term_id,
            class_section_name=s.class_section.name if s.class_section else None,
            subject_name=s.subject.name if s.subject else None
        )
        for s in schedules
    ]

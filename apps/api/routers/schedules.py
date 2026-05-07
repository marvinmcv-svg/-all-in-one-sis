"""Schedules router - Timetable Templates and Schedule Management API."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import time

from ..database import get_db
from ..models.user import User
from ..models.person import UserRole
from ..models.person import Person
from ..models.teacher import Teacher
from ..models.student import Student
from ..models.academic import ClassSection, Subject, AcademicTerm
from ..models.scheduling import Schedule, TimetableTemplate
from ..core.deps import get_current_user, require_roles

router = APIRouter(prefix="/schedules", tags=["Schedules"])

# Day name mapping
DAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}


# =============================================================================
# Pydantic Schemas
# =============================================================================

class ClassInfo(BaseModel):
    """Class section info for responses."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    room_number: Optional[str] = None


class SubjectInfo(BaseModel):
    """Subject info for responses."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    code: Optional[str] = None


class TeacherInfo(BaseModel):
    """Teacher info for responses."""
    model_config = {"from_attributes": True}
    
    id: int
    employee_id: str
    person_name: str


class TimetableTemplateCreate(BaseModel):
    """Schema for creating a timetable template."""
    name: str
    periods: List[dict]  # [{"number": 1, "start_time": "08:00", "end_time": "08:45"}]
    days: List[str]  # ["Monday", "Tuesday", ...]


class TimetableTemplateUpdate(BaseModel):
    """Schema for updating a timetable template."""
    name: Optional[str] = None
    periods: Optional[List[dict]] = None
    days: Optional[List[str]] = None


class TimetableTemplateResponse(BaseModel):
    """Timetable template response."""
    model_config = {"from_attributes": True}
    
    id: int
    school_id: int
    name: str
    periods: List[dict]
    days: List[str]


class ScheduleCreate(BaseModel):
    """Schema for creating a schedule entry."""
    class_section_id: int
    subject_id: int
    teacher_id: int
    day_of_week: int  # 0=Monday, 6=Sunday
    period_number: int
    room_number: Optional[str] = None
    start_time: str  # "08:00"
    end_time: str  # "08:45"
    academic_term_id: int


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule entry."""
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    day_of_week: Optional[int] = None
    period_number: Optional[int] = None
    room_number: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Full schedule entry response."""
    model_config = {"from_attributes": True}
    
    id: int
    class_section: ClassInfo
    subject: SubjectInfo
    teacher: TeacherInfo
    day_of_week: int
    day_name: str
    period_number: int
    room_number: Optional[str]
    start_time: str
    end_time: str
    academic_term_id: int


class ScheduleListResponse(BaseModel):
    """Schedule entry for list views."""
    model_config = {"from_attributes": True}
    
    id: int
    class_section_id: int
    class_section_name: str
    subject_id: int
    subject_name: str
    teacher_id: int
    teacher_name: str
    day_of_week: int
    day_name: str
    period_number: int
    room_number: Optional[str]
    start_time: str
    end_time: str
    academic_term_id: int


class ClassTimetableResponse(BaseModel):
    """Full class timetable response organized by day."""
    model_config = {"from_attributes": True}
    
    class_section: ClassInfo
    academic_term: str
    schedule: Dict[str, List[ScheduleResponse]]  # {"Monday": [...], "Tuesday": [...]}


class TeacherTimetableResponse(BaseModel):
    """Full teacher timetable response organized by day."""
    model_config = {"from_attributes": True}
    
    teacher: TeacherInfo
    academic_term: str
    schedule: Dict[str, List[ScheduleResponse]]


class ConflictCheckRequest(BaseModel):
    """Request to check for scheduling conflicts."""
    teacher_id: Optional[int] = None
    class_section_id: Optional[int] = None
    room_number: Optional[str] = None
    day_of_week: int
    period_number: int
    start_time: str
    end_time: str
    exclude_schedule_id: Optional[int] = None


class ConflictResult(BaseModel):
    """Result of conflict check."""
    has_conflicts: bool
    conflicts: List[dict]  # [{"type": "teacher", "id": 1, "message": "..."}]


class GenerateTimetableRequest(BaseModel):
    """Request to auto-generate timetable."""
    class_section_id: int
    academic_term_id: int
    template_id: Optional[int] = None


class GenerateTimetableResponse(BaseModel):
    """Response from timetable generation."""
    generated_count: int
    schedule_ids: List[int]


# =============================================================================
# Helper Functions
# =============================================================================

def time_str_to_obj(time_str: str) -> time:
    """Convert time string 'HH:MM' to time object."""
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def time_obj_to_str(t: time) -> str:
    """Convert time object to string 'HH:MM'."""
    return t.strftime("%H:%M")


def get_day_name(day_of_week: int) -> str:
    """Get day name from day number."""
    return DAY_NAMES.get(day_of_week, "Unknown")


async def get_teacher_from_user(db: AsyncSession, user: User) -> Teacher:
    """Get Teacher record from User."""
    result = await db.execute(
        select(Teacher).where(Teacher.person_id == user.person.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a teacher record"
        )
    return teacher


async def get_student_from_user(db: AsyncSession, user: User) -> Student:
    """Get Student record from User."""
    result = await db.execute(
        select(Student).where(Student.person_id == user.person.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a student record"
        )
    return student


async def check_schedule_conflicts(
    db: AsyncSession,
    teacher_id: Optional[int] = None,
    class_section_id: Optional[int] = None,
    room_number: Optional[str] = None,
    day_of_week: int = None,
    period_number: int = None,
    start_time: str = None,
    end_time: str = None,
    exclude_schedule_id: Optional[int] = None,
) -> List[dict]:
    """
    Check for scheduling conflicts.
    
    Conflicts occur when:
    - Same teacher, same day, same period
    - Same class, same day, same period
    - Same room, same day, same period (if room is specified)
    """
    conflicts = []
    
    if teacher_id and day_of_week is not None and period_number is not None:
        query = select(Schedule).where(
            and_(
                Schedule.teacher_id == teacher_id,
                Schedule.day_of_week == day_of_week,
                Schedule.period_number == period_number
            )
        )
        if exclude_schedule_id:
            query = query.where(Schedule.id != exclude_schedule_id)
        
        result = await db.execute(query)
        existing = result.scalars().all()
        
        for sched in existing:
            teacher_result = await db.execute(
                select(Teacher).where(Teacher.id == sched.teacher_id)
            )
            teacher = teacher_result.scalar_one_or_none()
            teacher_name = teacher.person.full_name if teacher and teacher.person else "Unknown"
            
            conflicts.append({
                "type": "teacher",
                "id": sched.teacher_id,
                "existing_schedule_id": sched.id,
                "message": f"Teacher {teacher_name} is already scheduled for period {sched.period_number} on {get_day_name(sched.day_of_week)}"
            })
    
    if class_section_id and day_of_week is not None and period_number is not None:
        query = select(Schedule).where(
            and_(
                Schedule.class_section_id == class_section_id,
                Schedule.day_of_week == day_of_week,
                Schedule.period_number == period_number
            )
        )
        if exclude_schedule_id:
            query = query.where(Schedule.id != exclude_schedule_id)
        
        result = await db.execute(query)
        existing = result.scalars().all()
        
        for sched in existing:
            class_result = await db.execute(
                select(ClassSection).where(ClassSection.id == sched.class_section_id)
            )
            class_section = class_result.scalar_one_or_none()
            class_name = class_section.name if class_section else "Unknown"
            
            conflicts.append({
                "type": "class",
                "id": sched.class_section_id,
                "existing_schedule_id": sched.id,
                "message": f"Class {class_name} already has {sched.subject.name if sched.subject else 'a subject'} scheduled for period {sched.period_number} on {get_day_name(sched.day_of_week)}"
            })
    
    if room_number and day_of_week is not None and period_number is not None:
        query = select(Schedule).where(
            and_(
                Schedule.room_number == room_number,
                Schedule.day_of_week == day_of_week,
                Schedule.period_number == period_number
            )
        )
        if exclude_schedule_id:
            query = query.where(Schedule.id != exclude_schedule_id)
        
        result = await db.execute(query)
        existing = result.scalars().all()
        
        for sched in existing:
            conflicts.append({
                "type": "room",
                "id": sched.id,
                "existing_schedule_id": sched.id,
                "message": f"Room {room_number} is already occupied for period {sched.period_number} on {get_day_name(sched.day_of_week)}"
            })
    
    return conflicts


# =============================================================================
# Timetable Template Endpoints
# =============================================================================

@router.get("/templates", response_model=List[TimetableTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
    school_id: Optional[int] = Query(None, description="Filter by school"),
):
    """
    List all timetable templates.
    - Admin only
    """
    query = select(TimetableTemplate)
    if school_id:
        query = query.where(TimetableTemplate.school_id == school_id)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        TimetableTemplateResponse(
            id=t.id,
            school_id=t.school_id,
            name=t.name,
            periods=t.periods,
            days=t.days
        )
        for t in templates
    ]


@router.post("/templates", response_model=TimetableTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TimetableTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Create a new timetable template.
    - Admin only
    """
    # Get school_id from current user's tenant
    school_id = current_user.tenant_id
    
    template = TimetableTemplate(
        school_id=school_id,
        name=template_data.name,
        periods=template_data.periods,
        days=template_data.days
    )
    
    db.add(template)
    await db.flush()
    await db.refresh(template)
    
    return TimetableTemplateResponse(
        id=template.id,
        school_id=template.school_id,
        name=template.name,
        periods=template.periods,
        days=template.days
    )


@router.get("/templates/{template_id}", response_model=TimetableTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Get timetable template details.
    - Admin only
    """
    result = await db.execute(
        select(TimetableTemplate).where(TimetableTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable template not found"
        )
    
    return TimetableTemplateResponse(
        id=template.id,
        school_id=template.school_id,
        name=template.name,
        periods=template.periods,
        days=template.days
    )


@router.put("/templates/{template_id}", response_model=TimetableTemplateResponse)
async def update_template(
    template_id: int,
    template_data: TimetableTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Update a timetable template.
    - Admin only
    """
    result = await db.execute(
        select(TimetableTemplate).where(TimetableTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable template not found"
        )
    
    if template_data.name is not None:
        template.name = template_data.name
    if template_data.periods is not None:
        template.periods = template_data.periods
    if template_data.days is not None:
        template.days = template_data.days
    
    await db.flush()
    await db.refresh(template)
    
    return TimetableTemplateResponse(
        id=template.id,
        school_id=template.school_id,
        name=template.name,
        periods=template.periods,
        days=template.days
    )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a timetable template.
    - Admin only
    """
    result = await db.execute(
        select(TimetableTemplate).where(TimetableTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable template not found"
        )
    
    await db.delete(template)
    await db.flush()


# =============================================================================
# Schedule CRUD Endpoints
# =============================================================================

@router.get("/", response_model=List[ScheduleListResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
    class_section_id: Optional[int] = Query(None, description="Filter by class section"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """
    List all schedules.
    - All authenticated users can view
    """
    query = (
        select(Schedule)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher).selectinload(Teacher.person)
        )
        .order_by(Schedule.day_of_week, Schedule.period_number)
        .offset(skip)
        .limit(limit)
    )
    
    if academic_term_id:
        query = query.where(Schedule.academic_term_id == academic_term_id)
    if class_section_id:
        query = query.where(Schedule.class_section_id == class_section_id)
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    return [
        ScheduleListResponse(
            id=s.id,
            class_section_id=s.class_section_id,
            class_section_name=s.class_section.name if s.class_section else "Unknown",
            subject_id=s.subject_id,
            subject_name=s.subject.name if s.subject else "Unknown",
            teacher_id=s.teacher_id,
            teacher_name=s.teacher.person.full_name if s.teacher and s.teacher.person else "Unknown",
            day_of_week=s.day_of_week,
            day_name=get_day_name(s.day_of_week),
            period_number=s.period_number,
            room_number=s.room_number,
            start_time=time_obj_to_str(s.start_time),
            end_time=time_obj_to_str(s.end_time),
            academic_term_id=s.academic_term_id
        )
        for s in schedules
    ]


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Create a new schedule entry.
    - Admin only
    - Checks for conflicts before creation
    """
    # Verify class_section exists
    result = await db.execute(
        select(ClassSection).where(ClassSection.id == schedule_data.class_section_id)
    )
    class_section = result.scalar_one_or_none()
    if not class_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class section not found"
        )
    
    # Verify subject exists
    result = await db.execute(
        select(Subject).where(Subject.id == schedule_data.subject_id)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Verify teacher exists
    result = await db.execute(
        select(Teacher).where(Teacher.id == schedule_data.teacher_id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Verify academic_term exists
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == schedule_data.academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    if not academic_term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic term not found"
        )
    
    # Check for conflicts
    conflicts = await check_schedule_conflicts(
        db,
        teacher_id=schedule_data.teacher_id,
        class_section_id=schedule_data.class_section_id,
        room_number=schedule_data.room_number,
        day_of_week=schedule_data.day_of_week,
        period_number=schedule_data.period_number,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time
    )
    
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Scheduling conflicts detected", "conflicts": conflicts}
        )
    
    # Create schedule
    schedule = Schedule(
        class_section_id=schedule_data.class_section_id,
        subject_id=schedule_data.subject_id,
        teacher_id=schedule_data.teacher_id,
        day_of_week=schedule_data.day_of_week,
        period_number=schedule_data.period_number,
        room_number=schedule_data.room_number,
        start_time=time_str_to_obj(schedule_data.start_time),
        end_time=time_str_to_obj(schedule_data.end_time),
        academic_term_id=schedule_data.academic_term_id
    )
    
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    
    # Load relationships for response
    await db.refresh(schedule, ["class_section", "subject", "teacher"])
    
    return ScheduleResponse(
        id=schedule.id,
        class_section=ClassInfo(
            id=schedule.class_section.id,
            name=schedule.class_section.name,
            room_number=schedule.class_section.room_number
        ),
        subject=SubjectInfo(
            id=schedule.subject.id,
            name=schedule.subject.name,
            code=schedule.subject.code
        ),
        teacher=TeacherInfo(
            id=schedule.teacher.id,
            employee_id=schedule.teacher.employee_id,
            person_name=schedule.teacher.person.full_name if schedule.teacher.person else "Unknown"
        ),
        day_of_week=schedule.day_of_week,
        day_name=get_day_name(schedule.day_of_week),
        period_number=schedule.period_number,
        room_number=schedule.room_number,
        start_time=time_obj_to_str(schedule.start_time),
        end_time=time_obj_to_str(schedule.end_time),
        academic_term_id=schedule.academic_term_id
    )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Get schedule entry details.
    - Admin only
    """
    result = await db.execute(
        select(Schedule)
        .where(Schedule.id == schedule_id)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher).selectinload(Teacher.person)
        )
    )
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return ScheduleResponse(
        id=schedule.id,
        class_section=ClassInfo(
            id=schedule.class_section.id,
            name=schedule.class_section.name,
            room_number=schedule.class_section.room_number
        ),
        subject=SubjectInfo(
            id=schedule.subject.id,
            name=schedule.subject.name,
            code=schedule.subject.code
        ),
        teacher=TeacherInfo(
            id=schedule.teacher.id,
            employee_id=schedule.teacher.employee_id,
            person_name=schedule.teacher.person.full_name if schedule.teacher.person else "Unknown"
        ),
        day_of_week=schedule.day_of_week,
        day_name=get_day_name(schedule.day_of_week),
        period_number=schedule.period_number,
        room_number=schedule.room_number,
        start_time=time_obj_to_str(schedule.start_time),
        end_time=time_obj_to_str(schedule.end_time),
        academic_term_id=schedule.academic_term_id
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Update a schedule entry.
    - Admin only
    - Checks for conflicts before update
    """
    result = await db.execute(
        select(Schedule)
        .where(Schedule.id == schedule_id)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher).selectinload(Teacher.person)
        )
    )
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Get updated values
    teacher_id = schedule_data.teacher_id if schedule_data.teacher_id is not None else schedule.teacher_id
    class_section_id = schedule_data.class_section_id if schedule_data.class_section_id is not None else schedule.class_section_id
    day_of_week = schedule_data.day_of_week if schedule_data.day_of_week is not None else schedule.day_of_week
    period_number = schedule_data.period_number if schedule_data.period_number is not None else schedule.period_number
    room_number = schedule_data.room_number if schedule_data.room_number is not None else schedule.room_number
    start_time = schedule_data.start_time if schedule_data.start_time is not None else time_obj_to_str(schedule.start_time)
    end_time = schedule_data.end_time if schedule_data.end_time is not None else time_obj_to_str(schedule.end_time)
    
    # Verify subject if changing
    if schedule_data.subject_id is not None:
        result = await db.execute(
            select(Subject).where(Subject.id == schedule_data.subject_id)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        schedule.subject_id = schedule_data.subject_id
    
    # Verify teacher if changing
    if schedule_data.teacher_id is not None:
        result = await db.execute(
            select(Teacher).where(Teacher.id == schedule_data.teacher_id)
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        schedule.teacher_id = schedule_data.teacher_id
    
    # Check for conflicts with new values
    conflicts = await check_schedule_conflicts(
        db,
        teacher_id=teacher_id,
        class_section_id=class_section_id,
        room_number=room_number,
        day_of_week=day_of_week,
        period_number=period_number,
        start_time=start_time,
        end_time=end_time,
        exclude_schedule_id=schedule_id
    )
    
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Scheduling conflicts detected", "conflicts": conflicts}
        )
    
    # Update fields
    if schedule_data.day_of_week is not None:
        schedule.day_of_week = schedule_data.day_of_week
    if schedule_data.period_number is not None:
        schedule.period_number = schedule_data.period_number
    if schedule_data.room_number is not None:
        schedule.room_number = schedule_data.room_number
    if schedule_data.start_time is not None:
        schedule.start_time = time_str_to_obj(schedule_data.start_time)
    if schedule_data.end_time is not None:
        schedule.end_time = time_str_to_obj(schedule_data.end_time)
    
    await db.flush()
    await db.refresh(schedule)
    
    # Reload relationships
    result = await db.execute(
        select(Schedule)
        .where(Schedule.id == schedule_id)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher).selectinload(Teacher.person)
        )
    )
    schedule = result.scalar_one()
    
    return ScheduleResponse(
        id=schedule.id,
        class_section=ClassInfo(
            id=schedule.class_section.id,
            name=schedule.class_section.name,
            room_number=schedule.class_section.room_number
        ),
        subject=SubjectInfo(
            id=schedule.subject.id,
            name=schedule.subject.name,
            code=schedule.subject.code
        ),
        teacher=TeacherInfo(
            id=schedule.teacher.id,
            employee_id=schedule.teacher.employee_id,
            person_name=schedule.teacher.person.full_name if schedule.teacher.person else "Unknown"
        ),
        day_of_week=schedule.day_of_week,
        day_name=get_day_name(schedule.day_of_week),
        period_number=schedule.period_number,
        room_number=schedule.room_number,
        start_time=time_obj_to_str(schedule.start_time),
        end_time=time_obj_to_str(schedule.end_time),
        academic_term_id=schedule.academic_term_id
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a schedule entry.
    - Admin only
    """
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    await db.delete(schedule)
    await db.flush()


# =============================================================================
# Class and Teacher Timetable Endpoints
# =============================================================================

@router.get("/class/{class_section_id}", response_model=ClassTimetableResponse)
async def get_class_timetable(
    class_section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
):
    """
    Get class timetable organized by day.
    - Admin, Teacher, Student can access
    """
    # For students, verify enrollment in this class
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        enrollment_result = await db.execute(
            select(Student).where(Student.id == student.id)
            .options(selectinload(Student.enrollments))
        )
        student = enrollment_result.scalar_one_or_none()
        enrolled_section_ids = [e.section_id for e in student.enrollments if e.status == "active"]
        if class_section_id not in enrolled_section_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
    
    # Get class section
    result = await db.execute(
        select(ClassSection).where(ClassSection.id == class_section_id)
    )
    class_section = result.scalar_one_or_none()
    if not class_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class section not found"
        )
    
    # Get academic term
    academic_term_id_to_use = academic_term_id or class_section.academic_term_id
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == academic_term_id_to_use)
    )
    academic_term = result.scalar_one_or_none()
    
    # Get all schedules for this class
    query = (
        select(Schedule)
        .where(Schedule.class_section_id == class_section_id)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher).selectinload(Teacher.person)
        )
    )
    
    if academic_term_id_to_use:
        query = query.where(Schedule.academic_term_id == academic_term_id_to_use)
    
    query = query.order_by(Schedule.day_of_week, Schedule.period_number)
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    # Organize by day
    schedule_by_day: Dict[str, List[ScheduleResponse]] = {day: [] for day in DAY_NAMES.values()}
    
    for sched in schedules:
        schedule_by_day[get_day_name(sched.day_of_week)].append(
            ScheduleResponse(
                id=sched.id,
                class_section=ClassInfo(
                    id=sched.class_section.id,
                    name=sched.class_section.name,
                    room_number=sched.class_section.room_number
                ),
                subject=SubjectInfo(
                    id=sched.subject.id,
                    name=sched.subject.name,
                    code=sched.subject.code
                ),
                teacher=TeacherInfo(
                    id=sched.teacher.id,
                    employee_id=sched.teacher.employee_id,
                    person_name=sched.teacher.person.full_name if sched.teacher.person else "Unknown"
                ),
                day_of_week=sched.day_of_week,
                day_name=get_day_name(sched.day_of_week),
                period_number=sched.period_number,
                room_number=sched.room_number,
                start_time=time_obj_to_str(sched.start_time),
                end_time=time_obj_to_str(sched.end_time),
                academic_term_id=sched.academic_term_id
            )
        )
    
    return ClassTimetableResponse(
        class_section=ClassInfo(
            id=class_section.id,
            name=class_section.name,
            room_number=class_section.room_number
        ),
        academic_term=academic_term.name if academic_term else "Unknown",
        schedule=schedule_by_day
    )


@router.get("/teacher/{teacher_id}", response_model=TeacherTimetableResponse)
async def get_teacher_timetable(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_term_id: Optional[int] = Query(None, description="Filter by academic term"),
):
    """
    Get teacher timetable organized by day.
    - Admin, Teacher can access
    """
    # Teachers can only view their own timetable
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if teacher.id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own timetable"
            )
    
    # Get teacher
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.person))
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Get schedules
    query = (
        select(Schedule)
        .where(Schedule.teacher_id == teacher_id)
        .options(
            selectinload(Schedule.class_section),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher).selectinload(Teacher.person)
        )
    )
    
    if academic_term_id:
        query = query.where(Schedule.academic_term_id == academic_term_id)
    
    query = query.order_by(Schedule.day_of_week, Schedule.period_number)
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    # Get academic term name if schedules exist
    academic_term_name = "Unknown"
    if schedules:
        result = await db.execute(
            select(AcademicTerm).where(AcademicTerm.id == schedules[0].academic_term_id)
        )
        academic_term = result.scalar_one_or_none()
        if academic_term:
            academic_term_name = academic_term.name
    
    # Organize by day
    schedule_by_day: Dict[str, List[ScheduleResponse]] = {day: [] for day in DAY_NAMES.values()}
    
    for sched in schedules:
        schedule_by_day[get_day_name(sched.day_of_week)].append(
            ScheduleResponse(
                id=sched.id,
                class_section=ClassInfo(
                    id=sched.class_section.id,
                    name=sched.class_section.name,
                    room_number=sched.class_section.room_number
                ),
                subject=SubjectInfo(
                    id=sched.subject.id,
                    name=sched.subject.name,
                    code=sched.subject.code
                ),
                teacher=TeacherInfo(
                    id=sched.teacher.id,
                    employee_id=sched.teacher.employee_id,
                    person_name=sched.teacher.person.full_name if sched.teacher.person else "Unknown"
                ),
                day_of_week=sched.day_of_week,
                day_name=get_day_name(sched.day_of_week),
                period_number=sched.period_number,
                room_number=sched.room_number,
                start_time=time_obj_to_str(sched.start_time),
                end_time=time_obj_to_str(sched.end_time),
                academic_term_id=sched.academic_term_id
            )
        )
    
    return TeacherTimetableResponse(
        teacher=TeacherInfo(
            id=teacher.id,
            employee_id=teacher.employee_id,
            person_name=teacher.person.full_name if teacher.person else "Unknown"
        ),
        academic_term=academic_term_name,
        schedule=schedule_by_day
    )


# =============================================================================
# Conflict Check Endpoint
# =============================================================================

@router.post("/check-conflicts", response_model=ConflictResult)
async def check_conflicts(
    conflict_data: ConflictCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Check for scheduling conflicts.
    - Admin only
    """
    conflicts = await check_schedule_conflicts(
        db,
        teacher_id=conflict_data.teacher_id,
        class_section_id=conflict_data.class_section_id,
        room_number=conflict_data.room_number,
        day_of_week=conflict_data.day_of_week,
        period_number=conflict_data.period_number,
        start_time=conflict_data.start_time,
        end_time=conflict_data.end_time,
        exclude_schedule_id=conflict_data.exclude_schedule_id
    )
    
    return ConflictResult(
        has_conflicts=len(conflicts) > 0,
        conflicts=conflicts
    )


# =============================================================================
# Auto-Generate Timetable Endpoint
# =============================================================================

@router.post("/generate", response_model=GenerateTimetableResponse)
async def generate_timetable(
    generate_data: GenerateTimetableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Auto-generate timetable for a class based on assigned subjects and teachers.
    - Admin only
    """
    # Verify class section exists
    result = await db.execute(
        select(ClassSection)
        .where(ClassSection.id == generate_data.class_section_id)
        .options(selectinload(ClassSection.class_subjects))
    )
    class_section = result.scalar_one_or_none()
    if not class_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class section not found"
        )
    
    # Verify academic term exists
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.id == generate_data.academic_term_id)
    )
    academic_term = result.scalar_one_or_none()
    if not academic_term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic term not found"
        )
    
    # Get template if specified
    template = None
    if generate_data.template_id:
        result = await db.execute(
            select(TimetableTemplate).where(TimetableTemplate.id == generate_data.template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
    
    # Get class subjects with teacher assignments
    class_subjects_result = await db.execute(
        select(ClassSection)
        .where(ClassSection.id == generate_data.class_section_id)
        .options(
            selectinload(ClassSection.class_subjects)
            .selectinload(ClassSubject.teacher_assignment)
            .selectinload(TeacherAssignment.teacher)
            .selectinload(Teacher.person),
            selectinload(ClassSection.class_subjects)
            .selectinload(ClassSubject.subject)
        )
    )
    class_section = class_subjects_result.scalar_one_or_none()
    
    # Build list of subjects to schedule
    subjects_to_schedule = []
    for cs in class_section.class_subjects:
        if cs.teacher_assignment and cs.teacher_assignment.teacher:
            subjects_to_schedule.append({
                "subject_id": cs.subject_id,
                "teacher_id": cs.teacher_assignment.teacher_id,
                "subject_name": cs.subject.name if cs.subject else "Unknown"
            })
    
    if not subjects_to_schedule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subjects with assigned teachers found for this class"
        )
    
    # Determine timetable structure
    if template:
        periods = template.periods
        days = template.days
    else:
        # Default timetable structure: 8 periods, Monday-Friday
        periods = [
            {"number": 1, "start_time": "08:00", "end_time": "08:45"},
            {"number": 2, "start_time": "08:50", "end_time": "09:35"},
            {"number": 3, "start_time": "09:40", "end_time": "10:25"},
            {"number": 4, "start_time": "10:30", "end_time": "11:15"},
            {"number": 5, "start_time": "11:20", "end_time": "12:05"},
            {"number": 6, "start_time": "12:10", "end_time": "12:55"},
            {"number": 7, "start_time": "13:00", "end_time": "13:45"},
            {"number": 8, "start_time": "13:50", "end_time": "14:35"},
        ]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Map day names to numbers
    day_name_to_num = {name: num for num, name in DAY_NAMES.items()}
    
    # Generate schedule entries
    generated_ids = []
    subject_index = 0
    
    for day_name in days:
        day_num = day_name_to_num.get(day_name)
        if day_num is None:
            continue
            
        for period in periods:
            period_num = period["number"]
            start_time = period["start_time"]
            end_time = period["end_time"]
            
            # Skip if subject already scheduled for this class/day/period
            check_result = await db.execute(
                select(Schedule).where(
                    and_(
                        Schedule.class_section_id == generate_data.class_section_id,
                        Schedule.day_of_week == day_num,
                        Schedule.period_number == period_num,
                        Schedule.academic_term_id == generate_data.academic_term_id
                    )
                )
            )
            existing = check_result.scalar_one_or_none()
            if existing:
                continue
            
            # Get next subject (round-robin)
            subject_info = subjects_to_schedule[subject_index % len(subjects_to_schedule)]
            subject_index += 1
            
            # Create schedule entry
            schedule = Schedule(
                class_section_id=generate_data.class_section_id,
                subject_id=subject_info["subject_id"],
                teacher_id=subject_info["teacher_id"],
                day_of_week=day_num,
                period_number=period_num,
                room_number=None,
                start_time=time_str_to_obj(start_time),
                end_time=time_str_to_obj(end_time),
                academic_term_id=generate_data.academic_term_id
            )
            
            db.add(schedule)
            await db.flush()
            await db.refresh(schedule)
            generated_ids.append(schedule.id)
    
    return GenerateTimetableResponse(
        generated_count=len(generated_ids),
        schedule_ids=generated_ids
    )

"""Attendance router."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from ..database import get_db
from ..models.attendance import AttendanceRecord, AttendanceExcuse, AttendanceStatus, StaffAttendance, ExcuseStatus
from ..models.student import Student, Enrollment
from ..models.teacher import Teacher, TeacherAssignment
from ..models.person import Person, User, UserRole
from ..core.deps import get_current_user, require_roles

router = APIRouter(prefix="/attendance", tags=["Attendance"])


# ============= Pydantic Schemas =============

class AttendanceMark(BaseModel):
    student_id: int
    status: AttendanceStatus
    excuse_id: Optional[int] = None


class BulkAttendanceRequest(BaseModel):
    class_section_id: int
    academic_term_id: int
    date: date
    attendance: List[AttendanceMark]


class AttendanceRecordResponse(BaseModel):
    id: int
    student_id: int
    class_section_id: int
    academic_term_id: int
    date: date
    status: AttendanceStatus
    excuse_id: Optional[int] = None
    marked_by_teacher_id: Optional[int] = None

    class Config:
        from_attributes = True


class AttendanceExcuseRequest(BaseModel):
    student_id: int
    start_date: date
    end_date: date
    reason: str


class AttendanceExcuseResponse(BaseModel):
    id: int
    student_id: int
    start_date: date
    end_date: date
    reason: str
    status: ExcuseStatus
    approved_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class AttendanceReport(BaseModel):
    student_id: int
    student_name: str
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    excused_days: int
    attendance_percentage: float


class StaffAttendanceRequest(BaseModel):
    teacher_id: int
    date: date
    status: str  # present, absent, late


class StaffAttendanceResponse(BaseModel):
    id: int
    teacher_id: int
    date: date
    status: str
    marked_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class StaffAttendanceReport(BaseModel):
    teacher_id: int
    teacher_name: str
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    attendance_percentage: float


class ClassAttendanceReport(BaseModel):
    class_section_id: int
    class_name: str
    total_students: int
    date: date
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_percentage: float


# ============= Helper Functions =============

async def get_teacher_for_user(db: AsyncSession, user: User) -> Optional[Teacher]:
    """Get teacher record for authenticated user."""
    result = await db.execute(
        select(Teacher).where(Teacher.person_id == user.person_id)
    )
    return result.scalar_one_or_none()


async def get_student_for_user(db: AsyncSession, user: User) -> Optional[Student]:
    """Get student record for authenticated user."""
    result = await db.execute(
        select(Student).where(Student.person_id == user.person_id)
    )
    return result.scalar_one_or_none()


async def get_parent_for_user(db: AsyncSession, user: User) -> Optional[Parent]:
    """Get parent record for authenticated user."""
    from ..models.parent import Parent
    result = await db.execute(
        select(Parent).where(Parent.person_id == user.person_id)
    )
    return result.scalar_one_or_none()


async def is_teacher_assigned_to_class(
    db: AsyncSession, teacher_id: int, class_section_id: int, academic_term_id: int
) -> bool:
    """Check if a teacher is assigned to a specific class section."""
    result = await db.execute(
        select(TeacherAssignment).where(
            and_(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_section_id == class_section_id,
                TeacherAssignment.academic_term_id == academic_term_id
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def is_parent_of_student(
    db: AsyncSession, parent_id: int, student_id: int
) -> bool:
    """Check if a parent is the guardian of a student."""
    result = await db.execute(
        select(Student).where(
            and_(
                Student.id == student_id,
                Student.guardian_id == parent_id
            )
        )
    )
    return result.scalar_one_or_none() is not None


# ============= Student Attendance Endpoints =============

@router.post("/", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
async def mark_attendance(
    class_section_id: int,
    academic_term_id: int,
    date: date,
    attendance_mark: AttendanceMark,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher"]))
):
    """
    Mark attendance for a single student.
    
    Teachers can only mark attendance for their assigned classes.
    """
    teacher = await get_teacher_for_user(db, current_user)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher"
        )

    # Check if teacher is assigned to this class
    is_assigned = await is_teacher_assigned_to_class(
        db, teacher.id, class_section_id, academic_term_id
    )
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )

    # Verify student is enrolled in this class
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.student_id == attendance_mark.student_id,
                Enrollment.section_id == class_section_id,
                Enrollment.academic_term_id == academic_term_id
            )
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in this class"
        )

    # Check for existing attendance record
    existing = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == attendance_mark.student_id,
                AttendanceRecord.class_section_id == class_section_id,
                AttendanceRecord.date == date
            )
        )
    )
    existing_record = existing.scalar_one_or_none()

    if existing_record:
        # Update existing record
        existing_record.status = attendance_mark.status
        existing_record.excuse_id = attendance_mark.excuse_id
        existing_record.marked_by_teacher_id = teacher.id
        record = existing_record
    else:
        # Create new record
        record = AttendanceRecord(
            student_id=attendance_mark.student_id,
            class_section_id=class_section_id,
            academic_term_id=academic_term_id,
            date=date,
            status=attendance_mark.status,
            excuse_id=attendance_mark.excuse_id,
            marked_by_teacher_id=teacher.id
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return record


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_mark_attendance(
    request: BulkAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher"]))
):
    """
    Bulk mark attendance for all students in a class.
    
    Teachers can only mark attendance for their assigned classes.
    """
    teacher = await get_teacher_for_user(db, current_user)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a teacher"
        )

    # Check if teacher is assigned to this class
    is_assigned = await is_teacher_assigned_to_class(
        db, teacher.id, request.class_section_id, request.academic_term_id
    )
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )

    created_records = []
    updated_records = []

    for mark in request.attendance:
        # Check for existing record
        existing = await db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == mark.student_id,
                    AttendanceRecord.class_section_id == request.class_section_id,
                    AttendanceRecord.date == request.date
                )
            )
        )
        existing_record = existing.scalar_one_or_none()

        if existing_record:
            existing_record.status = mark.status
            existing_record.excuse_id = mark.excuse_id
            existing_record.marked_by_teacher_id = teacher.id
            updated_records.append(existing_record)
        else:
            record = AttendanceRecord(
                student_id=mark.student_id,
                class_section_id=request.class_section_id,
                academic_term_id=request.academic_term_id,
                date=request.date,
                status=mark.status,
                excuse_id=mark.excuse_id,
                marked_by_teacher_id=teacher.id
            )
            db.add(record)
            created_records.append(record)

    await db.commit()
    
    return {
        "created": len(created_records),
        "updated": len(updated_records),
        "total": len(request.attendance)
    }


@router.get("/student/{student_id}", response_model=List[AttendanceRecordResponse])
async def get_student_attendance(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    class_section_id: Optional[int] = Query(None)
):
    """
    Get attendance records for a specific student.
    
    - Admin/Teacher: Can view any student's attendance
    - Student: Can only view their own attendance
    """
    # Authorization check
    if current_user.role == UserRole.STUDENT:
        student = await get_student_for_user(db, current_user)
        if not student or student.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own attendance"
            )
    elif current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Build query
    query = select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
    
    if start_date:
        query = query.where(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.where(AttendanceRecord.date <= end_date)
    if class_section_id:
        query = query.where(AttendanceRecord.class_section_id == class_section_id)
    
    query = query.order_by(AttendanceRecord.date.desc())

    result = await db.execute(query)
    records = result.scalars().all()
    return records


@router.get("/class/{class_section_id}", response_model=List[AttendanceRecordResponse])
async def get_class_attendance(
    class_section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    academic_term_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get attendance records for a class section.
    
    Teachers can only view attendance for their assigned classes.
    """
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_for_user(db, current_user)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a teacher"
            )
        
        # Check if teacher is assigned to this class
        if academic_term_id:
            is_assigned = await is_teacher_assigned_to_class(
                db, teacher.id, class_section_id, academic_term_id
            )
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this class"
                )

    query = select(AttendanceRecord).where(
        AttendanceRecord.class_section_id == class_section_id
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
    return records


@router.get("/class/{class_section_id}/date/{date}", response_model=List[AttendanceRecordResponse])
async def get_class_attendance_by_date(
    class_section_id: int,
    date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    academic_term_id: Optional[int] = Query(None)
):
    """
    Get attendance records for a specific class on a specific date.
    
    Teachers can only view attendance for their assigned classes.
    """
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_for_user(db, current_user)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a teacher"
            )
        
        if academic_term_id:
            is_assigned = await is_teacher_assigned_to_class(
                db, teacher.id, class_section_id, academic_term_id
            )
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this class"
                )

    query = select(AttendanceRecord).where(
        and_(
            AttendanceRecord.class_section_id == class_section_id,
            AttendanceRecord.date == date
        )
    )

    if academic_term_id:
        query = query.where(AttendanceRecord.academic_term_id == academic_term_id)

    result = await db.execute(query)
    records = result.scalars().all()
    return records


@router.get("/report/student/{student_id}", response_model=AttendanceReport)
async def get_student_attendance_report(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    academic_term_id: Optional[int] = Query(None)
):
    """
    Get attendance report for a specific student.
    
    - Admin/Teacher: Can view any student's report
    - Student: Can only view their own report
    """
    # Authorization check
    if current_user.role == UserRole.STUDENT:
        student = await get_student_for_user(db, current_user)
        if not student or student.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own attendance report"
            )
    elif current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Get student info
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Get student person info for name
    person_result = await db.execute(select(Person).where(Person.id == student.person_id))
    person = person_result.scalar_one_or_none()
    student_name = person.full_name if person else "Unknown"

    # Build query for attendance records
    query = select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
    
    if start_date:
        query = query.where(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.where(AttendanceRecord.date <= end_date)
    if academic_term_id:
        query = query.where(AttendanceRecord.academic_term_id == academic_term_id)

    result = await db.execute(query)
    records = result.scalars().all()

    # Calculate statistics
    total_days = len(records)
    present_days = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent_days = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    late_days = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    excused_days = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

    # Calculate attendance percentage (present + late + excused / total)
    if total_days > 0:
        attendance_percentage = round(((present_days + late_days + excused_days) / total_days) * 100, 2)
    else:
        attendance_percentage = 0.0

    return AttendanceReport(
        student_id=student_id,
        student_name=student_name,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        excused_days=excused_days,
        attendance_percentage=attendance_percentage
    )


@router.get("/report/class/{class_section_id}", response_model=List[AttendanceReport])
async def get_class_attendance_report(
    class_section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    academic_term_id: Optional[int] = Query(None)
):
    """
    Get attendance report for all students in a class.
    
    Admin only.
    """
    # Get enrolled students
    enrollments_query = select(Enrollment).where(
        and_(
            Enrollment.section_id == class_section_id,
            Enrollment.status == "active"
        )
    )
    if academic_term_id:
        enrollments_query = enrollments_query.where(Enrollment.academic_term_id == academic_term_id)

    result = await db.execute(enrollments_query)
    enrollments = result.scalars().all()

    reports = []
    for enrollment in enrollments:
        student_id = enrollment.student_id

        # Get student info
        student_result = await db.execute(select(Student).where(Student.id == student_id))
        student = student_result.scalar_one_or_none()
        if not student:
            continue

        person_result = await db.execute(select(Person).where(Person.id == student.person_id))
        person = person_result.scalar_one_or_none()
        student_name = person.full_name if person else "Unknown"

        # Get attendance records
        query = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.class_section_id == class_section_id
            )
        )

        if start_date:
            query = query.where(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.where(AttendanceRecord.date <= end_date)
        if academic_term_id:
            query = query.where(AttendanceRecord.academic_term_id == academic_term_id)

        records_result = await db.execute(query)
        records = records_result.scalars().all()

        total_days = len(records)
        present_days = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        absent_days = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        late_days = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        excused_days = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

        if total_days > 0:
            attendance_percentage = round(((present_days + late_days + excused_days) / total_days) * 100, 2)
        else:
            attendance_percentage = 0.0

        reports.append(AttendanceReport(
            student_id=student_id,
            student_name=student_name,
            total_days=total_days,
            present_days=present_days,
            absent_days=absent_days,
            late_days=late_days,
            excused_days=excused_days,
            attendance_percentage=attendance_percentage
        ))

    return reports


@router.get("/report/perfect", response_model=List[AttendanceReport])
async def get_perfect_attendance_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
    academic_term_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    class_section_id: Optional[int] = Query(None)
):
    """
    Get students with perfect attendance (100%).
    
    Admin only.
    """
    # Get all active enrollments
    query = select(Enrollment).where(Enrollment.status == "active")
    
    if class_section_id:
        query = query.where(Enrollment.section_id == class_section_id)
    if academic_term_id:
        query = query.where(Enrollment.academic_term_id == academic_term_id)

    result = await db.execute(query)
    enrollments = result.scalars().all()

    perfect_students = []

    for enrollment in enrollments:
        student_id = enrollment.student_id

        # Get student info
        student_result = await db.execute(select(Student).where(Student.id == student_id))
        student = student_result.scalar_one_or_none()
        if not student:
            continue

        person_result = await db.execute(select(Person).where(Person.id == student.person_id))
        person = person_result.scalar_one_or_none()
        student_name = person.full_name if person else "Unknown"

        # Get attendance records
        attendance_query = select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id
        )

        if start_date:
            attendance_query = attendance_query.where(AttendanceRecord.date >= start_date)
        if end_date:
            attendance_query = attendance_query.where(AttendanceRecord.date <= end_date)
        if academic_term_id:
            attendance_query = attendance_query.where(AttendanceRecord.academic_term_id == academic_term_id)
        if class_section_id:
            attendance_query = attendance_query.where(AttendanceRecord.class_section_id == class_section_id)

        records_result = await db.execute(attendance_query)
        records = records_result.scalars().all()

        total_days = len(records)
        if total_days == 0:
            continue

        present_days = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        late_days = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        excused_days = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

        # Check for perfect attendance (no absences)
        absent_days = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        
        if absent_days == 0 and (present_days + late_days + excused_days) == total_days:
            perfect_students.append(AttendanceReport(
                student_id=student_id,
                student_name=student_name,
                total_days=total_days,
                present_days=present_days,
                absent_days=0,
                late_days=late_days,
                excused_days=excused_days,
                attendance_percentage=100.0
            ))

    return perfect_students


# ============= Excuse Endpoints =============

@router.post("/excuse", response_model=AttendanceExcuseResponse, status_code=status.HTTP_201_CREATED)
async def request_excuse(
    request: AttendanceExcuseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["student", "parent"]))
):
    """
    Request an attendance excuse.
    
    - Students can request excuses for themselves
    - Parents can request excuses for their children
    """
    if current_user.role == UserRole.STUDENT:
        student = await get_student_for_user(db, current_user)
        if not student or student.id != request.student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only request excuses for yourself"
            )
    elif current_user.role == UserRole.PARENT:
        parent = await get_parent_for_user(db, current_user)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a parent"
            )
        is_parent = await is_parent_of_student(db, parent.id, request.student_id)
        if not is_parent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only request excuses for your children"
            )

    # Validate dates
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )

    # Create excuse request
    excuse = AttendanceExcuse(
        student_id=request.student_id,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
        status=ExcuseStatus.PENDING
    )
    db.add(excuse)
    await db.commit()
    await db.refresh(excuse)

    return excuse


@router.get("/excuse/{excuse_id}", response_model=AttendanceExcuseResponse)
async def get_excuse(
    excuse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get an excuse by ID.
    
    - Admin can view any excuse
    - Requester (student or parent) can view their own excuse
    """
    result = await db.execute(
        select(AttendanceExcuse).where(AttendanceExcuse.id == excuse_id)
    )
    excuse = result.scalar_one_or_none()
    
    if not excuse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excuse not found"
        )

    # Authorization check
    if current_user.role == UserRole.ADMIN:
        return excuse

    if current_user.role == UserRole.STUDENT:
        student = await get_student_for_user(db, current_user)
        if student and student.id == excuse.student_id:
            return excuse

    if current_user.role == UserRole.PARENT:
        parent = await get_parent_for_user(db, current_user)
        if parent:
            is_parent = await is_parent_of_student(db, parent.id, excuse.student_id)
            if is_parent:
                return excuse

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only view your own excuses"
    )


@router.put("/excuse/{excuse_id}", response_model=AttendanceExcuseResponse)
async def approve_or_reject_excuse(
    excuse_id: int,
    status: ExcuseStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Approve or reject an attendance excuse.
    
    Admin only.
    """
    result = await db.execute(
        select(AttendanceExcuse).where(AttendanceExcuse.id == excuse_id)
    )
    excuse = result.scalar_one_or_none()
    
    if not excuse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excuse not found"
        )

    if status not in [ExcuseStatus.APPROVED, ExcuseStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'approved' or 'rejected'"
        )

    # Get teacher record for admin user
    teacher = await get_teacher_for_user(db, current_user)
    
    excuse.status = status
    excuse.approved_by_id = teacher.id if teacher else None

    await db.commit()
    await db.refresh(excuse)

    return excuse


@router.get("/excuse/student/{student_id}", response_model=List[AttendanceExcuseResponse])
async def get_student_excuses(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
    status: Optional[ExcuseStatus] = Query(None)
):
    """
    Get all excuses for a specific student.
    
    Admin only.
    """
    query = select(AttendanceExcuse).where(
        AttendanceExcuse.student_id == student_id
    )

    if status:
        query = query.where(AttendanceExcuse.status == status)

    query = query.order_by(AttendanceExcuse.created_at.desc())

    result = await db.execute(query)
    excuses = result.scalars().all()

    return excuses


# ============= Staff Attendance Endpoints =============

@router.post("/staff", response_model=StaffAttendanceResponse, status_code=status.HTTP_201_CREATED)
async def mark_staff_attendance(
    request: StaffAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Mark attendance for a staff member (teacher).
    
    Admin only.
    """
    # Verify teacher exists
    result = await db.execute(
        select(Teacher).where(Teacher.id == request.teacher_id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )

    # Check for existing record
    existing = await db.execute(
        select(StaffAttendance).where(
            and_(
                StaffAttendance.teacher_id == request.teacher_id,
                StaffAttendance.date == request.date
            )
        )
    )
    existing_record = existing.scalar_one_or_none()

    # Get admin's teacher record (for marked_by)
    admin_teacher = await get_teacher_for_user(db, current_user)

    if existing_record:
        existing_record.status = request.status
        existing_record.marked_by_id = admin_teacher.id if admin_teacher else None
        record = existing_record
    else:
        record = StaffAttendance(
            teacher_id=request.teacher_id,
            date=request.date,
            status=request.status,
            marked_by_id=admin_teacher.id if admin_teacher else None
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)

    return record


@router.get("/staff/teacher/{teacher_id}", response_model=List[StaffAttendanceResponse])
async def get_teacher_attendance(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get attendance records for a specific teacher.
    
    - Admin can view any teacher's attendance
    - Teacher can only view their own attendance
    """
    # Authorization check
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_for_user(db, current_user)
        if not teacher or teacher.id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own attendance"
            )
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    query = select(StaffAttendance).where(
        StaffAttendance.teacher_id == teacher_id
    )

    if start_date:
        query = query.where(StaffAttendance.date >= start_date)
    if end_date:
        query = query.where(StaffAttendance.date <= end_date)

    query = query.order_by(StaffAttendance.date.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    return records


@router.get("/staff/report", response_model=List[StaffAttendanceReport])
async def get_staff_attendance_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    teacher_id: Optional[int] = Query(None)
):
    """
    Get attendance report for all teachers or a specific teacher.
    
    Admin only.
    """
    query = select(Teacher).where(Teacher.is_active == True)

    if teacher_id:
        query = query.where(Teacher.id == teacher_id)

    result = await db.execute(query)
    teachers = result.scalars().all()

    reports = []

    for teacher in teachers:
        # Get teacher person info for name
        person_result = await db.execute(select(Person).where(Person.id == teacher.person_id))
        person = person_result.scalar_one_or_none()
        teacher_name = person.full_name if person else "Unknown"

        # Get attendance records
        attendance_query = select(StaffAttendance).where(
            StaffAttendance.teacher_id == teacher.id
        )

        if start_date:
            attendance_query = attendance_query.where(StaffAttendance.date >= start_date)
        if end_date:
            attendance_query = attendance_query.where(StaffAttendance.date <= end_date)

        records_result = await db.execute(attendance_query)
        records = records_result.scalars().all()

        total_days = len(records)
        present_days = sum(1 for r in records if r.status == "present")
        absent_days = sum(1 for r in records if r.status == "absent")
        late_days = sum(1 for r in records if r.status == "late")

        if total_days > 0:
            attendance_percentage = round(((present_days + late_days) / total_days) * 100, 2)
        else:
            attendance_percentage = 0.0

        reports.append(StaffAttendanceReport(
            teacher_id=teacher.id,
            teacher_name=teacher_name,
            total_days=total_days,
            present_days=present_days,
            absent_days=absent_days,
            late_days=late_days,
            attendance_percentage=attendance_percentage
        ))

    return reports

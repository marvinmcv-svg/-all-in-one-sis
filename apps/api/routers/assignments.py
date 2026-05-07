"""Assignments router - Assignment and Submission Management API."""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
import boto3
from botocore.exceptions import ClientError
import uuid
import logging

from ..core.deps import get_current_user, require_roles
from ..database import get_db
from ..models.user import User
from ..models.person import UserRole
from ..models.lms import (
    Course, Assignment, AssignmentSubmission, CourseEnrollment
)
from ..models.teacher import Teacher
from ..models.student import Student
from ..config import get_settings

router = APIRouter(prefix="/assignments", tags=["Assignments"])
logger = logging.getLogger(__name__)
settings = get_settings()


# ============ S3 Helper Functions ============

def get_s3_client():
    """Get S3/MinIO client for file uploads."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


async def upload_file_to_s3(file: UploadFile, folder: str = "assignments") -> str:
    """Upload file to S3/MinIO and return the URL."""
    if not file:
        return None
    
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}" if file_extension else f"{folder}/{uuid.uuid4()}"
    
    try:
        s3_client = get_s3_client()
        s3_client.upload_fileobj(
            file.file,
            settings.S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{unique_filename}"
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


# ============ Helper Functions ============

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


async def check_course_enrollment(
    db: AsyncSession, course_id: int, student_id: int
) -> Optional[CourseEnrollment]:
    """Check if a student is enrolled in a course."""
    result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.student_id == student_id
            )
        )
    )
    return result.scalar_one_or_none()


async def check_teacher_owns_course(
    db: AsyncSession, teacher: Teacher, course_id: int
) -> bool:
    """Check if a teacher owns a specific course."""
    result = await db.execute(
        select(Course).where(
            and_(Course.id == course_id, Course.teacher_id == teacher.id)
        )
    )
    return result.scalar_one_or_none() is not None


async def check_teacher_owns_assignment(
    db: AsyncSession, teacher: Teacher, assignment_id: int
) -> bool:
    """Check if a teacher owns a specific assignment (via course)."""
    result = await db.execute(
        select(Assignment)
        .join(Course)
        .where(
            and_(
                Assignment.id == assignment_id,
                Course.teacher_id == teacher.id
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def get_assignment_with_course(
    db: AsyncSession, assignment_id: int
) -> Optional[Assignment]:
    """Get assignment with its course loaded."""
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.course))
        .where(Assignment.id == assignment_id)
    )
    return result.scalar_one_or_none()


# ============ Request Models ============

class AssignmentCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: datetime
    max_marks: float = Field(..., gt=0)
    submission_type: str = "file"  # file, text, both
    allowed_extensions: Optional[List[str]] = None  # e.g., [".pdf", ".docx"]

    class Config:
        from_attributes = True


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[datetime] = None
    max_marks: Optional[float] = Field(None, gt=0)

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    file_url: Optional[str] = None
    text_content: Optional[str] = None

    class Config:
        from_attributes = True


class SubmissionGrade(BaseModel):
    marks_obtained: float = Field(..., ge=0)
    feedback: Optional[str] = Field(None, max_length=1000)

    class Config:
        from_attributes = True


# ============ Response Models ============

class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    due_date: datetime
    max_marks: float
    submission_type: str
    allowed_extensions: Optional[List[str]]
    is_submitted: bool  # for current user
    submission_id: Optional[int]

    class Config:
        from_attributes = True


class AssignmentDetailResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    due_date: datetime
    max_marks: float
    submission_type: str
    allowed_extensions: Optional[List[str]]
    is_submitted: bool
    submission_id: Optional[int]
    course_name: str
    teacher_name: str

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    student_name: str
    file_url: Optional[str]
    text_content: Optional[str]
    submitted_at: datetime
    marks_obtained: Optional[float]
    feedback: Optional[str]
    graded_by_id: Optional[int]
    graded_at: Optional[datetime]
    is_late: bool

    class Config:
        from_attributes = True


class SubmissionDetailResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    student_name: str
    file_url: Optional[str]
    text_content: Optional[str]
    submitted_at: datetime
    marks_obtained: Optional[float]
    feedback: Optional[str]
    graded_by_id: Optional[int]
    graded_at: Optional[datetime]
    is_late: bool
    assignment_title: str
    course_name: str
    max_marks: float

    class Config:
        from_attributes = True


# ============ Assignment Endpoints ============

@router.get("/", response_model=List[AssignmentResponse])
async def list_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List assignments.
    - Admin/Teacher: See all assignments (optionally filtered by course)
    - Student: Only see assignments for enrolled courses
    """
    query = select(Assignment).options(
        selectinload(Assignment.course).selectinload(Course.teacher).selectinload(Teacher.person),
        selectinload(Assignment.submissions)
    )
    
    # Role-based filtering
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        
        # Students can only see assignments from enrolled courses
        enrolled_courses_subquery = (
            select(CourseEnrollment.course_id)
            .where(CourseEnrollment.student_id == student.id)
        )
        query = query.where(
            and_(
                Assignment.course_id.in_(enrolled_courses_subquery),
                Course.id.in_(enrolled_courses_subquery)
            )
        )
        
        # Also filter by course if specified
        if course_id:
            query = query.where(Assignment.course_id == course_id)
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        # Teachers see assignments for their courses
        teacher_courses_subquery = (
            select(Course.id).where(Course.teacher_id == teacher.id)
        )
        query = query.where(Assignment.course_id.in_(teacher_courses_subquery))
        
        if course_id:
            # Verify teacher owns this course
            if not await check_teacher_owns_course(db, teacher, course_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view assignments for your own courses"
                )
            query = query.where(Assignment.course_id == course_id)
    else:
        # Admin sees all
        if course_id:
            query = query.where(Assignment.course_id == course_id)
    
    query = query.order_by(Assignment.due_date.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    assignments = result.scalars().all()
    
    # Build response with submission status for current user
    student_id = None
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        student_id = student.id
    
    response = []
    for assignment in assignments:
        is_submitted = False
        submission_id = None
        if student_id:
            for submission in assignment.submissions:
                if submission.student_id == student_id:
                    is_submitted = True
                    submission_id = submission.id
                    break
        
        response.append(AssignmentResponse(
            id=assignment.id,
            course_id=assignment.course_id,
            title=assignment.title,
            description=assignment.description,
            due_date=assignment.due_date,
            max_marks=assignment.max_marks,
            submission_type=assignment.submission_type,
            allowed_extensions=assignment.allowed_extensions,
            is_submitted=is_submitted,
            submission_id=submission_id
        ))
    
    return response


@router.post("/", response_model=AssignmentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Create a new assignment.
    - Admin: Can create for any course
    - Teacher: Can only create for their own courses
    """
    # Verify course exists
    result = await db.execute(
        select(Course).where(Course.id == assignment_data.course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create assignments for your own courses"
            )
    
    # Create assignment
    assignment = Assignment(
        course_id=assignment_data.course_id,
        title=assignment_data.title,
        description=assignment_data.description,
        due_date=assignment_data.due_date,
        max_marks=int(assignment_data.max_marks),
        submission_type=assignment_data.submission_type,
        allowed_extensions=assignment_data.allowed_extensions
    )
    
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    
    # Load course with teacher
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.teacher).selectinload(Teacher.person))
        .where(Course.id == assignment_data.course_id)
    )
    course = result.scalar_one()
    
    teacher_name = course.teacher.person.full_name if course.teacher and course.teacher.person else "Unknown"
    
    return AssignmentDetailResponse(
        id=assignment.id,
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        max_marks=assignment.max_marks,
        submission_type=assignment.submission_type,
        allowed_extensions=assignment.allowed_extensions,
        is_submitted=False,
        submission_id=None,
        course_name=course.name,
        teacher_name=teacher_name
    )


@router.get("/{assignment_id}", response_model=AssignmentDetailResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get assignment details.
    - Admin/Teacher: Full access
    - Enrolled Student: Can view assignment details
    """
    assignment = await get_assignment_with_course(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    course = assignment.course
    
    # Check access
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        enrollment = await check_course_enrollment(db, course.id, student.id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view assignments for your own courses"
            )
    
    # Get submission status if user is a student
    is_submitted = False
    submission_id = None
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        result = await db.execute(
            select(AssignmentSubmission).where(
                and_(
                    AssignmentSubmission.assignment_id == assignment_id,
                    AssignmentSubmission.student_id == student.id
                )
            )
        )
        submission = result.scalar_one_or_none()
        if submission:
            is_submitted = True
            submission_id = submission.id
    
    teacher_name = course.teacher.person.full_name if course.teacher and course.teacher.person else "Unknown"
    
    return AssignmentDetailResponse(
        id=assignment.id,
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        max_marks=assignment.max_marks,
        submission_type=assignment.submission_type,
        allowed_extensions=assignment.allowed_extensions,
        is_submitted=is_submitted,
        submission_id=submission_id,
        course_name=course.name,
        teacher_name=teacher_name
    )


@router.put("/{assignment_id}", response_model=AssignmentDetailResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Update an assignment.
    - Admin: Can update any assignment
    - Teacher: Can only update their own course assignments
    """
    assignment = await get_assignment_with_course(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    course = assignment.course
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update assignments for your own courses"
            )
    
    # Update fields
    if assignment_data.title is not None:
        assignment.title = assignment_data.title
    if assignment_data.description is not None:
        assignment.description = assignment_data.description
    if assignment_data.due_date is not None:
        assignment.due_date = assignment_data.due_date
    if assignment_data.max_marks is not None:
        assignment.max_marks = int(assignment_data.max_marks)
    
    await db.flush()
    await db.refresh(assignment)
    
    # Reload course with teacher
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.teacher).selectinload(Teacher.person))
        .where(Course.id == assignment.course_id)
    )
    course = result.scalar_one()
    
    teacher_name = course.teacher.person.full_name if course.teacher and course.teacher.person else "Unknown"
    
    return AssignmentDetailResponse(
        id=assignment.id,
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        max_marks=assignment.max_marks,
        submission_type=assignment.submission_type,
        allowed_extensions=assignment.allowed_extensions,
        is_submitted=False,
        submission_id=None,
        course_name=course.name,
        teacher_name=teacher_name
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete an assignment.
    - Admin only
    """
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    await db.delete(assignment)
    await db.flush()


# ============ Submission Endpoints ============

@router.post("/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["student"])),
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Query(None, max_length=5000),
):
    """
    Submit an assignment.
    - Student: Must be enrolled in the course
    - Checks for late submission (after due_date)
    - Validates file extensions if specified
    """
    assignment = await get_assignment_with_course(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    student = await get_student_from_user(db, current_user)
    
    # Check enrollment
    enrollment = await check_course_enrollment(db, assignment.course_id, student.id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
    
    # Check if student already submitted
    result = await db.execute(
        select(AssignmentSubmission).where(
            and_(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student.id
            )
        )
    )
    existing_submission = result.scalar_one_or_none()
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted this assignment"
        )
    
    # Validate submission type
    file_url = None
    if assignment.submission_type in ["file", "both"]:
        if not file and not existing_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is required for this assignment"
            )
    if assignment.submission_type in ["text", "both"]:
        if not text_content and not existing_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required for this assignment"
            )
    
    # Upload file if provided
    if file:
        # Validate file extension if restrictions are set
        if assignment.allowed_extensions:
            file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
            if file_ext not in assignment.allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File extension {file_ext} not allowed. Allowed: {assignment.allowed_extensions}"
                )
        file_url = await upload_file_to_s3(file, f"assignments/{assignment_id}")
    
    # Check if late
    is_late = datetime.utcnow() > assignment.due_date
    
    # Create submission
    submission = AssignmentSubmission(
        assignment_id=assignment_id,
        student_id=student.id,
        file_url=file_url,
        submitted_at=datetime.utcnow(),
        is_late=is_late
    )
    
    # Note: text_content would need a column added to the model
    # For now, we'll skip it since the model doesn't have it
    
    db.add(submission)
    await db.flush()
    await db.refresh(submission)
    
    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=f"{student.person.first_name} {student.person.last_name}" if student.person else "Unknown",
        file_url=submission.file_url,
        text_content=None,  # Model doesn't have this field yet
        submitted_at=submission.submitted_at,
        marks_obtained=submission.marks_obtained,
        feedback=submission.feedback,
        graded_by_id=submission.graded_by_id,
        graded_at=submission.graded_at,
        is_late=submission.is_late
    )


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def list_submissions(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List all submissions for an assignment.
    - Admin: Can view all submissions
    - Teacher: Can only view submissions for their courses
    """
    assignment = await get_assignment_with_course(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    course = assignment.course
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view submissions for your own courses"
            )
    
    # Get submissions with student info
    result = await db.execute(
        select(AssignmentSubmission)
        .options(
            selectinload(AssignmentSubmission.student).selectinload(Student.person)
        )
        .where(AssignmentSubmission.assignment_id == assignment_id)
        .offset(skip)
        .limit(limit)
    )
    submissions = result.scalars().all()
    
    return [
        SubmissionResponse(
            id=s.id,
            assignment_id=s.assignment_id,
            student_id=s.student_id,
            student_name=f"{s.student.person.first_name} {s.student.person.last_name}" if s.student and s.student.person else "Unknown",
            file_url=s.file_url,
            text_content=None,  # Model doesn't have this field yet
            submitted_at=s.submitted_at,
            marks_obtained=s.marks_obtained,
            feedback=s.feedback,
            graded_by_id=s.graded_by_id,
            graded_at=s.graded_at,
            is_late=s.is_late
        )
        for s in submissions
    ]


@router.put("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    submission_id: int,
    grade_data: SubmissionGrade,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Grade a submission.
    - Admin: Can grade any submission
    - Teacher: Can only grade submissions for their courses
    """
    result = await db.execute(
        select(AssignmentSubmission)
        .options(
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course)
        )
        .where(AssignmentSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    assignment = submission.assignment
    course = assignment.course
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grade submissions for your own courses"
            )
    
    # Validate marks don't exceed max
    if grade_data.marks_obtained > assignment.max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Marks cannot exceed max marks ({assignment.max_marks})"
        )
    
    # Update submission
    submission.marks_obtained = int(grade_data.marks_obtained)
    submission.feedback = grade_data.feedback
    submission.graded_by_id = teacher.id if current_user.role == UserRole.TEACHER else None
    submission.graded_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(submission)
    
    # Get student name
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.person))
        .where(Student.id == submission.student_id)
    )
    student = result.scalar_one_or_none()
    
    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=f"{student.person.first_name} {student.person.last_name}" if student and student.person else "Unknown",
        file_url=submission.file_url,
        text_content=None,
        submitted_at=submission.submitted_at,
        marks_obtained=submission.marks_obtained,
        feedback=submission.feedback,
        graded_by_id=submission.graded_by_id,
        graded_at=submission.graded_at,
        is_late=submission.is_late
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific submission.
    - Admin/Teacher: Full access
    - Student: Can only view their own submission
    """
    result = await db.execute(
        select(AssignmentSubmission)
        .options(
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course),
            selectinload(AssignmentSubmission.student).selectinload(Student.person)
        )
        .where(AssignmentSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    assignment = submission.assignment
    course = assignment.course
    student = submission.student
    
    # Check access for students
    if current_user.role == UserRole.STUDENT:
        current_student = await get_student_from_user(db, current_user)
        if submission.student_id != current_student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own submissions"
            )
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view submissions for your own courses"
            )
    
    teacher_name = course.teacher.person.full_name if course.teacher and course.teacher.person else "Unknown"
    
    return SubmissionDetailResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=f"{student.person.first_name} {student.person.last_name}" if student and student.person else "Unknown",
        file_url=submission.file_url,
        text_content=None,
        submitted_at=submission.submitted_at,
        marks_obtained=submission.marks_obtained,
        feedback=submission.feedback,
        graded_by_id=submission.graded_by_id,
        graded_at=submission.graded_at,
        is_late=submission.is_late,
        assignment_title=assignment.title,
        course_name=course.name,
        max_marks=assignment.max_marks
    )

"""Courses router - LMS Course Management API."""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum

from ..core.deps import get_current_user, require_roles
from ..database import get_db
from ..models.user import User
from ..models.person import UserRole
from ..models.lms import (
    Course, Chapter, Lesson, CourseEnrollment, LessonProgress,
    Assignment, Quiz
)
from ..models.teacher import Teacher
from ..models.student import Student
from ..config import get_settings
import boto3
from botocore.exceptions import ClientError
import uuid
import logging

router = APIRouter(prefix="/courses", tags=["Courses"])
logger = logging.getLogger(__name__)
settings = get_settings()


# Enums
class EnrollmentType(str, Enum):
    OPEN = "open"
    APPROVAL = "approval"
    CLOSED = "closed"


class ContentType(str, Enum):
    VIDEO = "video"
    TEXT = "text"
    PDF = "pdf"
    EMBED = "embed"


# ============ Request Models ============

class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    subject_id: Optional[int] = None
    enrollment_type: EnrollmentType = EnrollmentType.OPEN
    is_published: bool = False

    class Config:
        from_attributes = True


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    subject_id: Optional[int] = None
    enrollment_type: Optional[EnrollmentType] = None
    is_published: Optional[bool] = None

    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    order_index: int = Field(..., ge=0)

    class Config:
        from_attributes = True


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    order_index: Optional[int] = Field(None, ge=0)

    class Config:
        from_attributes = True


class LessonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content_type: ContentType
    content_url: Optional[str] = Field(None, max_length=500)
    content_text: Optional[str] = None
    duration_minutes: int = Field(default=0, ge=0)
    order_index: int = Field(..., ge=0)
    is_preview: bool = False

    class Config:
        from_attributes = True


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content_type: Optional[ContentType] = None
    content_url: Optional[str] = Field(None, max_length=500)
    content_text: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    order_index: Optional[int] = Field(None, ge=0)
    is_preview: Optional[bool] = None

    class Config:
        from_attributes = True


# ============ Response Models ============

class LessonResponse(BaseModel):
    id: int
    title: str
    content_type: str
    content_url: Optional[str]
    duration_minutes: int
    order_index: int
    is_preview: bool
    progress: Optional[float] = None

    class Config:
        from_attributes = True


class ChapterWithLessons(BaseModel):
    id: int
    title: str
    description: Optional[str]
    order_index: int
    lessons: List[LessonResponse]

    class Config:
        from_attributes = True


class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    teacher_id: int
    subject_id: Optional[int]
    is_published: bool
    enrollment_type: str
    enrollment_count: int
    chapters: List[ChapterWithLessons]
    is_enrolled: bool = False
    progress_percentage: Optional[float] = None

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    teacher_id: int
    is_published: bool
    enrollment_type: str
    enrollment_count: int
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    is_enrolled: bool = False

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    id: int
    student_id: str
    person_first_name: str
    person_last_name: str
    enrolled_at: datetime
    progress_percentage: int

    class Config:
        from_attributes = True


class EnrollmentResponse(BaseModel):
    id: int
    course_id: int
    student_id: int
    enrolled_at: datetime
    completed_at: Optional[datetime]
    progress_percentage: int

    class Config:
        from_attributes = True


# ============ Helper Functions ============

def get_s3_client():
    """Get S3/MinIO client for file uploads."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


async def upload_file_to_s3(file: UploadFile, folder: str = "courses") -> str:
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
        
        # Return the URL
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{unique_filename}"
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


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


async def calculate_course_progress(
    db: AsyncSession, course_id: int, student_id: int
) -> float:
    """Calculate the progress percentage for a student in a course."""
    # Get total lessons in the course
    total_result = await db.execute(
        select(func.count(Lesson.id))
        .join(Chapter)
        .where(Chapter.course_id == course_id)
    )
    total_lessons = total_result.scalar() or 0
    
    if total_lessons == 0:
        return 0.0
    
    # Get completed lessons for this student
    completed_result = await db.execute(
        select(func.count(LessonProgress.id))
        .join(Lesson)
        .join(Chapter)
        .where(
            and_(
                Chapter.course_id == course_id,
                LessonProgress.student_id == student_id,
                LessonProgress.completed_at.isnot(None)
            )
        )
    )
    completed_lessons = completed_result.scalar() or 0
    
    return round((completed_lessons / total_lessons) * 100, 2)


# ============ Course Endpoints ============

@router.get("/", response_model=List[CourseListResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search by course name"),
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List courses.
    - Admin/Teacher: See all courses in their school
    - Student: Only see enrolled courses or published open enrollment courses
    """
    # Build base query
    query = select(Course).options(
        selectinload(Course.subject),
        selectinload(Course.teacher).selectinload(Teacher.person),
        selectinload(Course.enrollments)
    )
    
    # Role-based filtering
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        # Students see: enrolled courses + published open enrollment courses
        query = query.where(
            or_(
                Course.is_published == True,
                Course.id.in_(
                    select(CourseEnrollment.course_id).where(
                        CourseEnrollment.student_id == student.id
                    )
                )
            )
        )
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        query = query.where(Course.teacher_id == teacher.id)
    # Admin sees all
    
    # Apply filters
    if search:
        query = query.where(Course.name.ilike(f"%{search}%"))
    if subject_id:
        query = query.where(Course.subject_id == subject_id)
    if is_published is not None:
        query = query.where(Course.is_published == is_published)
    
    # Ordering and pagination
    query = query.order_by(Course.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    courses = result.scalars().all()
    
    # Get student enrollment status if user is a student
    student_id = None
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        student_id = student.id
    
    response = []
    for course in courses:
        is_enrolled = False
        if student_id:
            enrollment = await check_course_enrollment(db, course.id, student_id)
            is_enrolled = enrollment is not None
        
        response.append(CourseListResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            teacher_id=course.teacher_id,
            is_published=course.is_published,
            enrollment_type=course.enrollment_type,
            enrollment_count=len(course.enrollments),
            subject_name=course.subject.name if course.subject else None,
            teacher_name=course.teacher.person.full_name if course.teacher and course.teacher.person else None,
            is_enrolled=is_enrolled
        ))
    
    return response


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Create a new course.
    - Admin: Can create for any teacher
    - Teacher: Can create their own course (teacher_id will be their own)
    """
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        teacher_id = teacher.id
    else:
        # Admin must specify teacher_id or use their own
        # For now, we'll require admin to create through a specific flow
        # If no specific teacher, we'll need to handle this
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin must specify teacher_id for course creation"
        )
    
    # Verify subject belongs to same school if specified
    if course_data.subject_id:
        from ..models.academic import Subject
        result = await db.execute(
            select(Subject).where(Subject.id == course_data.subject_id)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
    
    # Create course
    course = Course(
        school_id=teacher.person.tenant_id,  # Use tenant as school for now
        teacher_id=teacher_id,
        name=course_data.name,
        description=course_data.description,
        subject_id=course_data.subject_id,
        enrollment_type=course_data.enrollment_type.value,
        is_published=course_data.is_published,
    )
    
    db.add(course)
    await db.flush()
    await db.refresh(course)
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        description=course.description,
        teacher_id=course.teacher_id,
        subject_id=course.subject_id,
        is_published=course.is_published,
        enrollment_type=course.enrollment_type,
        enrollment_count=0,
        chapters=[],
        is_enrolled=False
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get course details with chapters and lessons.
    - Admin/Teacher (owner): Full access
    - Enrolled Student: Full access
    - Other Students: Only preview lessons (is_preview=True)
    """
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.chapters).selectinload(Chapter.lessons),
            selectinload(Course.teacher).selectinload(Teacher.person),
            selectinload(Course.enrollments),
            selectinload(Course.subject)
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check access
    is_enrolled = False
    progress_percentage = None
    
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        enrollment = await check_course_enrollment(db, course_id, student.id)
        
        if not enrollment and not course.is_published:
            # Check if user is the teacher
            if current_user.role != UserRole.TEACHER:
                teacher = await get_teacher_from_user(db, current_user)
                if course.teacher_id != teacher.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not enrolled in this course"
                    )
        else:
            is_enrolled = enrollment is not None
            if is_enrolled:
                progress_percentage = await calculate_course_progress(db, course_id, student.id)
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own courses"
            )
    
    # Build chapters with lessons
    chapters_response = []
    for chapter in course.chapters:
        lessons_response = []
        for lesson in chapter.lessons:
            lesson_progress = None
            if current_user.role == UserRole.STUDENT and is_enrolled:
                student = await get_student_from_user(db, current_user)
                progress_result = await db.execute(
                    select(LessonProgress).where(
                        and_(
                            LessonProgress.lesson_id == lesson.id,
                            LessonProgress.student_id == student.id
                        )
                    )
                )
                progress_record = progress_result.scalar_one_or_none()
                if progress_record and progress_record.completed_at:
                    lesson_progress = 100.0
                else:
                    lesson_progress = 0.0
            
            # Hide content for non-enrolled students (except previews)
            content_url = lesson.content_url
            if current_user.role == UserRole.STUDENT and not is_enrolled and not lesson.is_preview:
                content_url = None
            
            lessons_response.append(LessonResponse(
                id=lesson.id,
                title=lesson.title,
                content_type=lesson.content_type,
                content_url=content_url,
                duration_minutes=lesson.duration_minutes,
                order_index=lesson.order_index,
                is_preview=lesson.is_preview,
                progress=lesson_progress
            ))
        
        chapters_response.append(ChapterWithLessons(
            id=chapter.id,
            title=chapter.title,
            description=chapter.description,
            order_index=chapter.order_index,
            lessons=lessons_response
        ))
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        description=course.description,
        teacher_id=course.teacher_id,
        subject_id=course.subject_id,
        is_published=course.is_published,
        enrollment_type=course.enrollment_type,
        enrollment_count=len(course.enrollments),
        chapters=chapters_response,
        is_enrolled=is_enrolled,
        progress_percentage=progress_percentage
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Update a course.
    - Admin: Can update any course
    - Teacher: Can only update their own courses
    """
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.chapters).selectinload(Chapter.lessons))
        .where(Course.id == course_id)
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
                detail="You can only update your own courses"
            )
    
    # Update fields
    if course_data.name is not None:
        course.name = course_data.name
    if course_data.description is not None:
        course.description = course_data.description
    if course_data.subject_id is not None:
        course.subject_id = course_data.subject_id
    if course_data.enrollment_type is not None:
        course.enrollment_type = course_data.enrollment_type.value
    if course_data.is_published is not None:
        course.is_published = course_data.is_published
    
    await db.flush()
    await db.refresh(course)
    
    # Return updated course
    chapters_response = []
    for chapter in course.chapters:
        lessons_response = [
            LessonResponse(
                id=lesson.id,
                title=lesson.title,
                content_type=lesson.content_type,
                content_url=lesson.content_url,
                duration_minutes=lesson.duration_minutes,
                order_index=lesson.order_index,
                is_preview=lesson.is_preview
            )
            for lesson in chapter.lessons
        ]
        chapters_response.append(ChapterWithLessons(
            id=chapter.id,
            title=chapter.title,
            description=chapter.description,
            order_index=chapter.order_index,
            lessons=lessons_response
        ))
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        description=course.description,
        teacher_id=course.teacher_id,
        subject_id=course.subject_id,
        is_published=course.is_published,
        enrollment_type=course.enrollment_type,
        enrollment_count=len(course.enrollments),
        chapters=chapters_response
    )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a course.
    - Admin only
    """
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    await db.delete(course)
    await db.flush()


@router.post("/{course_id}/enroll", response_model=EnrollmentResponse)
async def enroll_in_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "student"])),
):
    """
    Enroll a student in a course.
    - Admin: Can enroll any student (requires student_id in body - future enhancement)
    - Student: Can enroll themselves in open enrollment courses
    """
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if not course.is_published and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course is not published"
        )
    
    if course.enrollment_type == EnrollmentType.CLOSED.value and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course is closed for enrollment"
        )
    
    # Get student
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        student_id = student.id
    else:
        # Admin would need to specify student_id - for now use first admin found or require it
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin must specify student_id for enrollment"
        )
    
    # Check if already enrolled
    existing = await check_course_enrollment(db, course_id, student_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this course"
        )
    
    # Create enrollment
    enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=student_id,
        enrolled_at=datetime.utcnow(),
        progress_percentage=0
    )
    
    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)
    
    return EnrollmentResponse(
        id=enrollment.id,
        course_id=enrollment.course_id,
        student_id=enrollment.student_id,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
        progress_percentage=enrollment.progress_percentage
    )


@router.get("/{course_id}/students", response_model=List[StudentResponse])
async def list_course_students(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List all students enrolled in a course.
    - Admin: Can view any course's students
    - Teacher: Can only view their own course's students
    """
    result = await db.execute(
        select(Course).where(Course.id == course_id)
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
                detail="You can only view students in your own courses"
            )
    
    # Get enrolled students
    query = (
        select(CourseEnrollment)
        .options(
            selectinload(CourseEnrollment.student).selectinload(Student.person)
        )
        .where(CourseEnrollment.course_id == course_id)
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    enrollments = result.scalars().all()
    
    return [
        StudentResponse(
            id=enrollment.student.id,
            student_id=enrollment.student.student_id,
            person_first_name=enrollment.student.person.first_name,
            person_last_name=enrollment.student.person.last_name,
            enrolled_at=enrollment.enrolled_at,
            progress_percentage=enrollment.progress_percentage
        )
        for enrollment in enrollments
    ]


# ============ Chapter Endpoints ============

@router.post("/{course_id}/chapter", response_model=ChapterWithLessons, status_code=status.HTTP_201_CREATED)
async def add_chapter(
    course_id: int,
    chapter_data: ChapterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Add a chapter to a course.
    - Admin: Can add to any course
    - Teacher: Can only add to their own courses
    """
    result = await db.execute(
        select(Course).where(Course.id == course_id)
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
                detail="You can only add chapters to your own courses"
            )
    
    # Create chapter
    chapter = Chapter(
        course_id=course_id,
        title=chapter_data.title,
        description=chapter_data.description,
        order_index=chapter_data.order_index
    )
    
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)
    
    return ChapterWithLessons(
        id=chapter.id,
        title=chapter.title,
        description=chapter.description,
        order_index=chapter.order_index,
        lessons=[]
    )


@router.put("/chapters/{chapter_id}", response_model=ChapterWithLessons)
async def update_chapter(
    chapter_id: int,
    chapter_data: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Update a chapter.
    - Admin: Can update any chapter
    - Teacher: Can only update chapters in their own courses
    """
    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.course))
        .where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if chapter.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update chapters in your own courses"
            )
    
    # Update fields
    if chapter_data.title is not None:
        chapter.title = chapter_data.title
    if chapter_data.description is not None:
        chapter.description = chapter_data.description
    if chapter_data.order_index is not None:
        chapter.order_index = chapter_data.order_index
    
    await db.flush()
    
    # Reload with lessons
    await db.refresh(chapter)
    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.lessons))
        .where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one()
    
    return ChapterWithLessons(
        id=chapter.id,
        title=chapter.title,
        description=chapter.description,
        order_index=chapter.order_index,
        lessons=[
            LessonResponse(
                id=lesson.id,
                title=lesson.title,
                content_type=lesson.content_type,
                content_url=lesson.content_url,
                duration_minutes=lesson.duration_minutes,
                order_index=lesson.order_index,
                is_preview=lesson.is_preview
            )
            for lesson in chapter.lessons
        ]
    )


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a chapter and all its lessons.
    - Admin only
    """
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    await db.delete(chapter)
    await db.flush()


# ============ Lesson Endpoints ============

@router.post("/chapters/{chapter_id}/lesson", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def add_lesson(
    chapter_id: int,
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    file: Optional[UploadFile] = File(None),
):
    """
    Add a lesson to a chapter.
    - Admin: Can add to any chapter
    - Teacher: Can only add to chapters in their own courses
    - If content_type is 'video' or 'pdf' and file is uploaded, it will be uploaded to S3
    """
    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.course))
        .where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if chapter.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add lessons to your own courses"
            )
    
    # Handle file upload if provided
    content_url = lesson_data.content_url
    if file and lesson_data.content_type in [ContentType.VIDEO, ContentType.PDF]:
        folder = "videos" if lesson_data.content_type == ContentType.VIDEO else "documents"
        content_url = await upload_file_to_s3(file, folder)
    
    # Create lesson
    lesson = Lesson(
        chapter_id=chapter_id,
        title=lesson_data.title,
        content_type=lesson_data.content_type.value,
        content_url=content_url,
        duration_minutes=lesson_data.duration_minutes,
        order_index=lesson_data.order_index,
        is_preview=lesson_data.is_preview
    )
    
    # Note: content_text would be stored if we add that column
    # For now, we'll skip it since the model doesn't have it
    
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)
    
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        content_type=lesson.content_type,
        content_url=lesson.content_url,
        duration_minutes=lesson.duration_minutes,
        order_index=lesson.order_index,
        is_preview=lesson.is_preview
    )


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    file: Optional[UploadFile] = File(None),
):
    """
    Update a lesson.
    - Admin: Can update any lesson
    - Teacher: Can only update lessons in their own courses
    """
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.chapter).selectinload(Chapter.course))
        .where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if lesson.chapter.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update lessons in your own courses"
            )
    
    # Update fields
    if lesson_data.title is not None:
        lesson.title = lesson_data.title
    if lesson_data.content_type is not None:
        lesson.content_type = lesson_data.content_type.value
    if lesson_data.content_url is not None:
        lesson.content_url = lesson_data.content_url
    if lesson_data.duration_minutes is not None:
        lesson.duration_minutes = lesson_data.duration_minutes
    if lesson_data.order_index is not None:
        lesson.order_index = lesson_data.order_index
    if lesson_data.is_preview is not None:
        lesson.is_preview = lesson_data.is_preview
    
    # Handle file upload if provided
    if file and lesson.content_type in [ContentType.VIDEO.value, ContentType.PDF.value]:
        folder = "videos" if lesson.content_type == ContentType.VIDEO.value else "documents"
        lesson.content_url = await upload_file_to_s3(file, folder)
    
    await db.flush()
    await db.refresh(lesson)
    
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        content_type=lesson.content_type,
        content_url=lesson.content_url,
        duration_minutes=lesson.duration_minutes,
        order_index=lesson.order_index,
        is_preview=lesson.is_preview
    )


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a lesson.
    - Admin only
    """
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    await db.delete(lesson)
    await db.flush()


@router.post("/lessons/{lesson_id}/complete", response_model=LessonResponse)
async def mark_lesson_complete(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["student"])),
):
    """
    Mark a lesson as complete for the current student.
    - Student only (must be enrolled in the course)
    """
    # Get the lesson and verify enrollment
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.chapter))
        .where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Get student
    student = await get_student_from_user(db, current_user)
    
    # Check enrollment
    enrollment = await check_course_enrollment(db, lesson.chapter.course_id, student.id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
    
    # Check if progress record exists
    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.student_id == student.id
            )
        )
    )
    progress = progress_result.scalar_one_or_none()
    
    if progress:
        # Update existing progress
        progress.completed_at = datetime.utcnow()
    else:
        # Create new progress record
        progress = LessonProgress(
            lesson_id=lesson_id,
            student_id=student.id,
            completed_at=datetime.utcnow()
        )
        db.add(progress)
    
    await db.flush()
    
    # Update course progress
    course_progress = await calculate_course_progress(db, lesson.chapter.course_id, student.id)
    enrollment.progress_percentage = int(course_progress)
    
    # Check if course is completed
    if course_progress == 100.0:
        enrollment.completed_at = datetime.utcnow()
    
    await db.flush()
    
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        content_type=lesson.content_type,
        content_url=lesson.content_url,
        duration_minutes=lesson.duration_minutes,
        order_index=lesson.order_index,
        is_preview=lesson.is_preview,
        progress=100.0 if progress.completed_at else 0.0
    )


# ============ Progress Endpoints ============

@router.get("/{course_id}/progress")
async def get_course_progress(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current student's progress in a course.
    - Enrolled student or course owner teacher
    """
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        enrollment = await check_course_enrollment(db, course_id, student.id)
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
        
        progress_percentage = await calculate_course_progress(db, course_id, student.id)
        
        return {
            "course_id": course_id,
            "student_id": student.id,
            "progress_percentage": progress_percentage,
            "completed_at": enrollment.completed_at
        }
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if course.teacher_id != teacher.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view progress for your own courses"
            )
        
        # Return aggregate stats for teachers
        total_students = len(course.enrollments)
        completed_students = sum(1 for e in course.enrollments if e.completed_at)
        
        return {
            "course_id": course_id,
            "total_students": total_students,
            "completed_students": completed_students,
            "completion_rate": round((completed_students / total_students * 100) if total_students > 0 else 0, 2)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and teachers can view course progress"
        )

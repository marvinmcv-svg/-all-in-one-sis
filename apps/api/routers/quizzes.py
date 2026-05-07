"""Quizzes router - Quiz Management API."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ..core.deps import get_current_user, require_roles
from ..database import get_db
from ..models.user import User
from ..models.person import UserRole
from ..models.lms import (
    Quiz, QuizQuestion, QuizAttempt, QuizResponse as QuizResponseModel,
    Course, CourseEnrollment
)
from ..models.teacher import Teacher
from ..models.student import Student

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


# ============ Request Models ============

class QuizCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1, max_length=200)
    time_limit_minutes: Optional[int] = 30
    max_attempts: int = 1
    passing_percentage: float = 60.0
    is_published: bool = False

    class Config:
        from_attributes = True


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    time_limit_minutes: Optional[int] = None
    max_attempts: Optional[int] = None
    passing_percentage: Optional[float] = None
    is_published: Optional[bool] = None

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = "multiple_choice"  # multiple_choice, true_false, short_answer
    options: Optional[List[dict]] = None  # [{"text": "A", "is_correct": true}]
    correct_answer: Optional[dict] = None  # {"type": "multiple_choice", "answer": 0}
    marks: float = 1.0
    order_index: int = 0

    class Config:
        from_attributes = True


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, min_length=1, max_length=1000)
    question_type: Optional[str] = None
    options: Optional[List[dict]] = None
    correct_answer: Optional[dict] = None
    marks: Optional[float] = None
    order_index: Optional[int] = None

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    answers: List[dict]  # [{"question_id": 1, "answer": {"type": "multiple_choice", "answer": 0}}]

    class Config:
        from_attributes = True


# ============ Response Models ============

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: str
    options: Optional[List[dict]]
    marks: float
    order_index: int

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: int
    course_id: int
    title: str
    time_limit_minutes: Optional[int]
    max_attempts: int
    passing_percentage: float
    is_published: bool
    questions_count: int
    is_attempted: bool
    best_score: Optional[float]

    class Config:
        from_attributes = True


class QuizDetailResponse(BaseModel):
    id: int
    course_id: int
    title: str
    time_limit_minutes: Optional[int]
    max_attempts: int
    passing_percentage: float
    is_published: bool
    questions: List[QuestionResponse]

    class Config:
        from_attributes = True


class AttemptStartResponse(BaseModel):
    attempt_id: int
    started_at: datetime
    time_limit_minutes: Optional[int]
    questions: List[QuestionResponse]

    class Config:
        from_attributes = True


class AttemptResult(BaseModel):
    attempt_id: int
    quiz_id: int
    student_id: int
    started_at: datetime
    submitted_at: Optional[datetime]
    score: Optional[float]
    total_marks: float
    percentage: Optional[float]
    passed: Optional[bool]
    is_time_up: bool
    answers: List[dict]

    class Config:
        from_attributes = True


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


async def get_course_with_quiz_access(
    db: AsyncSession, quiz_id: int, user: User
) -> tuple[Quiz, Course]:
    """Get quiz with access validation based on user role."""
    result = await db.execute(
        select(Quiz)
        .options(
            selectinload(Quiz.course),
            selectinload(Quiz.questions),
            selectinload(Quiz.attempts)
        )
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Check access based on role
    if user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, user)
        enrollment = await check_course_enrollment(db, quiz.course_id, student.id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
        if not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This quiz is not published"
            )
    elif user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, user)
        if quiz.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this quiz"
            )
    # Admin has full access
    
    return quiz, quiz.course


def auto_grade_question(question: QuizQuestion, answer: dict) -> tuple[bool, float]:
    """
    Auto-grade a question response.
    Returns (is_correct, marks_obtained).
    """
    if question.question_type == "short_answer":
        # Short answer requires manual grading
        return (None, None)
    
    if question.correct_answer is None:
        return (None, None)
    
    correct = question.correct_answer
    student_answer = answer.get("answer")
    
    if question.question_type == "multiple_choice":
        if correct.get("type") == "multiple_choice":
            correct_answer_idx = correct.get("answer")
            if student_answer == correct_answer_idx:
                return (True, question.marks)
            return (False, 0.0)
    
    elif question.question_type == "true_false":
        if correct.get("type") == "true_false":
            correct_answer_bool = correct.get("answer")
            if student_answer == correct_answer_bool:
                return (True, question.marks)
            return (False, 0.0)
    
    return (None, None)


# ============ Quiz Endpoints ============

@router.get("/", response_model=List[QuizResponse])
async def list_quizzes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    course_id: Optional[int] = Query(None, description="Filter by course"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List quizzes.
    - Admin/Teacher: See all quizzes in their courses
    - Student: Only see published quizzes in enrolled courses
    """
    query = select(Quiz).options(
        selectinload(Quiz.questions),
        selectinload(Quiz.attempts),
        selectinload(Quiz.course)
    )
    
    # Role-based filtering
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        # Students see only enrolled courses' published quizzes
        query = query.join(Course).where(
            and_(
                Quiz.is_published == True,
                Course.id.in_(
                    select(CourseEnrollment.course_id).where(
                        CourseEnrollment.student_id == student.id
                    )
                )
            )
        )
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        query = query.where(Quiz.course.has(teacher_id=teacher.id))
    
    # Apply filters
    if course_id:
        query = query.where(Quiz.course_id == course_id)
    if is_published is not None:
        query = query.where(Quiz.is_published == is_published)
    
    query = query.order_by(Quiz.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    quizzes = result.scalars().all()
    
    # Get student attempts info if user is a student
    student_id = None
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        student_id = student.id
    
    response = []
    for quiz in quizzes:
        is_attempted = False
        best_score = None
        
        if student_id:
            student_attempts = [a for a in quiz.attempts if a.student_id == student_id]
            if student_attempts:
                is_attempted = True
                best_score = max((a.score or 0) for a in student_attempts)
        
        response.append(QuizResponse(
            id=quiz.id,
            course_id=quiz.course_id,
            title=quiz.title,
            time_limit_minutes=quiz.time_limit_minutes,
            max_attempts=quiz.max_attempts,
            passing_percentage=quiz.passing_percentage,
            is_published=quiz.is_published,
            questions_count=len(quiz.questions),
            is_attempted=is_attempted,
            best_score=best_score
        ))
    
    return response


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Create a new quiz.
    - Admin: Can create for any course
    - Teacher: Can only create for their own courses
    """
    # Verify course exists
    result = await db.execute(
        select(Course).where(Course.id == quiz_data.course_id)
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
                detail="You can only create quizzes for your own courses"
            )
    
    # Create quiz
    quiz = Quiz(
        course_id=quiz_data.course_id,
        title=quiz_data.title,
        time_limit_minutes=quiz_data.time_limit_minutes or 30,
        max_attempts=quiz_data.max_attempts,
        passing_percentage=quiz_data.passing_percentage,
        is_published=quiz_data.is_published
    )
    
    db.add(quiz)
    await db.flush()
    await db.refresh(quiz)
    
    return QuizResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        passing_percentage=quiz.passing_percentage,
        is_published=quiz.is_published,
        questions_count=0,
        is_attempted=False,
        best_score=None
    )


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get quiz details with questions.
    - Admin/Teacher (owner): Full access
    - Enrolled students (if published): See questions without correct answers
    """
    quiz, course = await get_course_with_quiz_access(db, quiz_id, current_user)
    
    # For students, don't return correct answers
    questions_response = []
    for q in quiz.questions:
        q_model = QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            marks=q.marks,
            order_index=q.order_index
        )
        questions_response.append(q_model)
    
    return QuizDetailResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        passing_percentage=quiz.passing_percentage,
        is_published=quiz.is_published,
        questions=questions_response
    )


@router.put("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: int,
    quiz_data: QuizUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Update a quiz.
    - Admin: Can update any quiz
    - Teacher: Can only update their own quizzes
    """
    quiz, course = await get_course_with_quiz_access(db, quiz_id, current_user)
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if quiz.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own quizzes"
            )
    
    # Update fields
    if quiz_data.title is not None:
        quiz.title = quiz_data.title
    if quiz_data.time_limit_minutes is not None:
        quiz.time_limit_minutes = quiz_data.time_limit_minutes
    if quiz_data.max_attempts is not None:
        quiz.max_attempts = quiz_data.max_attempts
    if quiz_data.passing_percentage is not None:
        quiz.passing_percentage = quiz_data.passing_percentage
    if quiz_data.is_published is not None:
        quiz.is_published = quiz_data.is_published
    
    await db.flush()
    await db.refresh(quiz)
    
    # Get attempt info
    student_id = None
    is_attempted = False
    best_score = None
    
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        student_id = student.id
    
    if student_id:
        student_attempts = [a for a in quiz.attempts if a.student_id == student_id]
        if student_attempts:
            is_attempted = True
            best_score = max((a.score or 0) for a in student_attempts)
    
    return QuizResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        passing_percentage=quiz.passing_percentage,
        is_published=quiz.is_published,
        questions_count=len(quiz.questions),
        is_attempted=is_attempted,
        best_score=best_score
    )


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a quiz.
    - Admin only
    """
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    await db.delete(quiz)
    await db.flush()


@router.post("/{quiz_id}/publish", response_model=QuizResponse)
async def publish_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Publish a quiz.
    - Admin: Can publish any quiz
    - Teacher: Can only publish their own quizzes
    """
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions), selectinload(Quiz.attempts))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if quiz.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only publish your own quizzes"
            )
    
    quiz.is_published = True
    await db.flush()
    await db.refresh(quiz)
    
    return QuizResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        passing_percentage=quiz.passing_percentage,
        is_published=quiz.is_published,
        questions_count=len(quiz.questions),
        is_attempted=False,
        best_score=None
    )


# ============ Question Endpoints ============

@router.post("/{quiz_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    quiz_id: int,
    question_data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Add a question to a quiz.
    - Admin: Can add to any quiz
    - Teacher: Can only add to their own quizzes
    """
    quiz, course = await get_course_with_quiz_access(db, quiz_id, current_user)
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if quiz.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add questions to your own quizzes"
            )
    
    # Create question
    question = QuizQuestion(
        quiz_id=quiz_id,
        question_text=question_data.question_text,
        question_type=question_data.question_type,
        options=question_data.options,
        correct_answer=question_data.correct_answer,
        marks=question_data.marks,
        order_index=question_data.order_index
    )
    
    db.add(question)
    await db.flush()
    await db.refresh(question)
    
    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        question_type=question.question_type,
        options=question.options,
        marks=question.marks,
        order_index=question.order_index
    )


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
):
    """
    Update a question.
    - Admin: Can update any question
    - Teacher: Can only update questions in their own quizzes
    """
    result = await db.execute(
        select(QuizQuestion)
        .options(selectinload(QuizQuestion.quiz).selectinload(Course))
        .where(QuizQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check ownership for teachers
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if question.quiz.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update questions in your own quizzes"
            )
    
    # Update fields
    if question_data.question_text is not None:
        question.question_text = question_data.question_text
    if question_data.question_type is not None:
        question.question_type = question_data.question_type
    if question_data.options is not None:
        question.options = question_data.options
    if question_data.correct_answer is not None:
        question.correct_answer = question_data.correct_answer
    if question_data.marks is not None:
        question.marks = question_data.marks
    if question_data.order_index is not None:
        question.order_index = question_data.order_index
    
    await db.flush()
    await db.refresh(question)
    
    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        question_type=question.question_type,
        options=question.options,
        marks=question.marks,
        order_index=question.order_index
    )


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Delete a question.
    - Admin only
    """
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    await db.delete(question)
    await db.flush()


# ============ Attempt Endpoints ============

@router.post("/{quiz_id}/start", response_model=AttemptStartResponse)
async def start_quiz_attempt(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["student"])),
):
    """
    Start a quiz attempt.
    - Student only (must be enrolled in the course and quiz must be published)
    - Checks max attempts limit
    """
    quiz, course = await get_course_with_quiz_access(db, quiz_id, current_user)
    
    student = await get_student_from_user(db, current_user)
    
    # Count existing attempts
    result = await db.execute(
        select(func.count(QuizAttempt.id))
        .where(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student.id
            )
        )
    )
    attempt_count = result.scalar() or 0
    
    if attempt_count >= quiz.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum attempts ({quiz.max_attempts}) exceeded"
        )
    
    # Check for incomplete attempts
    incomplete_result = await db.execute(
        select(QuizAttempt).where(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student.id,
                QuizAttempt.submitted_at.is_(None)
            )
        )
    )
    incomplete_attempt = incomplete_result.scalar_one_or_none()
    
    if incomplete_attempt:
        # Return existing incomplete attempt
        questions_response = []
        for q in quiz.questions:
            questions_response.append(QuestionResponse(
                id=q.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                marks=q.marks,
                order_index=q.order_index
            ))
        
        return AttemptStartResponse(
            attempt_id=incomplete_attempt.id,
            started_at=incomplete_attempt.started_at,
            time_limit_minutes=quiz.time_limit_minutes,
            questions=questions_response
        )
    
    # Create new attempt
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=student.id,
        started_at=datetime.utcnow()
    )
    
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    
    # Return questions (without correct answers)
    questions_response = []
    for q in quiz.questions:
        questions_response.append(QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            marks=q.marks,
            order_index=q.order_index
        ))
    
    return AttemptStartResponse(
        attempt_id=attempt.id,
        started_at=attempt.started_at,
        time_limit_minutes=quiz.time_limit_minutes,
        questions=questions_response
    )


@router.put("/attempts/{attempt_id}", response_model=AttemptResult)
async def submit_quiz_attempt(
    attempt_id: int,
    answer_data: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["student"])),
):
    """
    Submit quiz attempt answers.
    - Student only (owner of the attempt)
    - Auto-grades multiple choice and true/false questions
    - Short answer requires manual grading
    - Enforces time limit
    """
    result = await db.execute(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.quiz).selectinload(Quiz.questions),
            selectinload(QuizAttempt.responses)
        )
        .where(QuizAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Verify ownership
    student = await get_student_from_user(db, current_user)
    if attempt.student_id != student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not your attempt"
        )
    
    # Check if already submitted
    if attempt.submitted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attempt has already been submitted"
        )
    
    quiz = attempt.quiz
    
    # Check time limit
    is_time_up = False
    if quiz.time_limit_minutes:
        deadline = attempt.started_at + timedelta(minutes=quiz.time_limit_minutes)
        if datetime.utcnow() > deadline:
            is_time_up = True
    
    # Grade each answer
    total_score = 0.0
    total_marks = sum(q.marks for q in quiz.questions)
    requires_manual_grading = False
    
    answers_response = []
    
    for answer_dict in answer_data.answers:
        question_id = answer_dict.get("question_id")
        answer = answer_dict.get("answer")
        
        # Find the question
        question = next((q for q in quiz.questions if q.id == question_id), None)
        if not question:
            continue
        
        # Check if response already exists
        existing_response = next(
            (r for r in attempt.responses if r.quiz_question_id == question_id),
            None
        )
        
        # Auto-grade
        is_correct, marks_obtained = auto_grade_question(question, answer)
        
        if is_correct is None and marks_obtained is None:
            # Short answer - requires manual grading
            requires_manual_grading = True
            marks_obtained = 0
        
        if is_correct:
            total_score += marks_obtained
        
        answer_entry = {
            "question_id": question_id,
            "answer": answer,
            "is_correct": is_correct,
            "marks_obtained": marks_obtained
        }
        answers_response.append(answer_entry)
        
        # Save response
        if existing_response:
            existing_response.answer = answer
            existing_response.is_correct = is_correct
            existing_response.marks_obtained = marks_obtained
        else:
            response = QuizResponseModel(
                quiz_attempt_id=attempt_id,
                quiz_question_id=question_id,
                answer=answer,
                is_correct=is_correct,
                marks_obtained=marks_obtained
            )
            db.add(response)
    
    # Calculate percentage
    percentage = None
    passed = None
    
    if not requires_manual_grading:
        percentage = round((total_score / total_marks * 100), 2) if total_marks > 0 else 0
        passed = percentage >= quiz.passing_percentage
        attempt.score = total_score
        attempt.passed = passed
    
    attempt.submitted_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(attempt)
    
    return AttemptResult(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        student_id=student.id,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        total_marks=total_marks,
        percentage=percentage,
        passed=passed,
        is_time_up=is_time_up,
        answers=answers_response
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptResult)
async def get_attempt_result(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get quiz attempt result.
    - Admin/Teacher: Can view any attempt
    - Student: Can only view their own attempts
    """
    result = await db.execute(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.quiz).selectinload(Quiz.questions),
            selectinload(QuizAttempt.responses)
        )
        .where(QuizAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Check access
    if current_user.role == UserRole.STUDENT:
        student = await get_student_from_user(db, current_user)
        if attempt.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own attempts"
            )
    elif current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        if attempt.quiz.course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view attempts for your own quizzes"
            )
    
    # Build answers response with correct answers for teachers/admins
    quiz = attempt.quiz
    answers_response = []
    
    for response in attempt.responses:
        question = next((q for q in quiz.questions if q.id == response.quiz_question_id), None)
        
        answer_entry = {
            "question_id": response.quiz_question_id,
            "answer": response.answer,
            "is_correct": response.is_correct,
            "marks_obtained": response.marks_obtained,
            "correct_answer": None  # Will be filled for teachers/admins
        }
        
        # Include correct answer for teachers/admins
        if current_user.role in [UserRole.ADMIN, UserRole.TEACHER]:
            if question and question.correct_answer:
                answer_entry["correct_answer"] = question.correct_answer
        
        answers_response.append(answer_entry)
    
    # Calculate total marks
    total_marks = sum(q.marks for q in quiz.questions)
    
    return AttemptResult(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        student_id=attempt.student_id,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        total_marks=total_marks,
        percentage=round((attempt.score / total_marks * 100), 2) if attempt.score is not None and total_marks > 0 else None,
        passed=attempt.passed,
        is_time_up=False,
        answers=answers_response
    )


@router.get("/attempts/student/{student_id}", response_model=List[AttemptResult])
async def get_student_attempts(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    quiz_id: Optional[int] = Query(None, description="Filter by quiz"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get all attempts for a student.
    - Admin: Can view any student's attempts
    - Teacher: Can only view attempts for their own courses
    """
    # Verify student exists
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    query = select(QuizAttempt).options(
        selectinload(QuizAttempt.quiz).selectinload(Quiz.questions),
        selectinload(QuizAttempt.responses)
    ).where(QuizAttempt.student_id == student_id)
    
    # Teachers can only see attempts from their quizzes
    if current_user.role == UserRole.TEACHER:
        teacher = await get_teacher_from_user(db, current_user)
        query = query.join(Quiz).where(Quiz.course.has(teacher_id=teacher.id))
    
    if quiz_id:
        query = query.where(QuizAttempt.quiz_id == quiz_id)
    
    query = query.order_by(QuizAttempt.started_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    attempts = result.scalars().all()
    
    response = []
    for attempt in attempts:
        quiz = attempt.quiz
        total_marks = sum(q.marks for q in quiz.questions)
        
        answers_response = []
        for resp in attempt.responses:
            answers_response.append({
                "question_id": resp.quiz_question_id,
                "answer": resp.answer,
                "is_correct": resp.is_correct,
                "marks_obtained": resp.marks_obtained
            })
        
        response.append(AttemptResult(
            attempt_id=attempt.id,
            quiz_id=quiz.id,
            student_id=student_id,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            score=attempt.score,
            total_marks=total_marks,
            percentage=round((attempt.score / total_marks * 100), 2) if attempt.score is not None and total_marks > 0 else None,
            passed=attempt.passed,
            is_time_up=False,
            answers=answers_response
        ))
    
    return response

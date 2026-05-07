from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class Course(Base, TimestampMixin):
    """Online course linked to a subject."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    enrollment_type = Column(String(20), default="open")  # open, approval, paid

    # Relationships
    school = relationship("School", back_populates="courses")
    subject = relationship("Subject", back_populates="courses")
    teacher = relationship("Teacher", back_populates="taught_courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan", order_by="Chapter.order_index")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name='{self.name}', teacher_id={self.teacher_id})>"


class CourseEnrollment(Base, TimestampMixin):
    """Student enrollment in a course."""
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(Date, nullable=False, default=datetime.utcnow)
    completed_at = Column(Date, nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="enrollments")
    student = relationship("Student", back_populates="course_enrollments")

    def __repr__(self) -> str:
        return f"<CourseEnrollment(id={self.id}, course_id={self.course_id}, student_id={self.student_id})>"


class Chapter(Base, TimestampMixin):
    """Chapter within a course."""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="chapters")
    lessons = relationship("Lesson", back_populates="chapter", cascade="all, delete-orphan", order_by="Lesson.order_index")

    def __repr__(self) -> str:
        return f"<Chapter(id={self.id}, title='{self.title}', order_index={self.order_index})>"


class Lesson(Base, TimestampMixin):
    """Individual lesson within a chapter."""
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content_type = Column(String(50), nullable=False)  # video, pdf, text, embed
    content_url = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, default=0, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    is_preview = Column(Boolean, default=False, nullable=False)

    # Relationships
    chapter = relationship("Chapter", back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, title='{self.title}', content_type='{self.content_type}')>"


class LessonProgress(Base, TimestampMixin):
    """Student progress on a lesson."""
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    completed_at = Column(Date, nullable=True)
    time_spent_seconds = Column(Integer, default=0, nullable=False)

    # Relationships
    lesson = relationship("Lesson", back_populates="progress")
    student = relationship("Student", back_populates="lesson_progress")

    def __repr__(self) -> str:
        return f"<LessonProgress(id={self.id}, lesson_id={self.lesson_id}, student_id={self.student_id})>"


class Assignment(Base, TimestampMixin):
    """Assignment for a course."""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    due_date = Column(Date, nullable=False)
    max_marks = Column(Integer, nullable=False)
    submission_type = Column(String(50), default="file")  # file, text, online
    allowed_extensions = Column(JSONB, nullable=True)  # List of allowed file extensions

    # Relationships
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Assignment(id={self.id}, title='{self.title}', due_date={self.due_date})>"


class AssignmentSubmission(Base, TimestampMixin):
    """Student submission for an assignment."""
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url = Column(String(500), nullable=True)
    submitted_at = Column(Date, nullable=False, default=datetime.utcnow)
    marks_obtained = Column(Integer, nullable=True)
    feedback = Column(String(1000), nullable=True)
    graded_by_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    graded_at = Column(Date, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="assignment_submissions")
    graded_by = relationship("Teacher")

    def __repr__(self) -> str:
        return f"<AssignmentSubmission(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id})>"


class Quiz(Base, TimestampMixin):
    """Quiz for a course."""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    time_limit_minutes = Column(Integer, default=30, nullable=False)
    max_attempts = Column(Integer, default=1, nullable=False)
    passing_percentage = Column(Integer, default=60, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Quiz(id={self.id}, title='{self.title}', passing_percentage={self.passing_percentage})>"


class QuizQuestion(Base, TimestampMixin):
    """Question within a quiz."""
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(String(1000), nullable=False)
    question_type = Column(String(50), nullable=False)  # mcq, true_false, short_answer
    options = Column(JSONB, nullable=True)  # List of options for MCQ
    correct_answer = Column(JSONB, nullable=True)  # Correct answer(s)
    marks = Column(Integer, default=1, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    responses = relationship("QuizResponse", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<QuizQuestion(id={self.id}, question_type='{self.question_type}', marks={self.marks})>"


class QuizAttempt(Base, TimestampMixin):
    """Student attempt at a quiz."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(Date, nullable=False, default=datetime.utcnow)
    submitted_at = Column(Date, nullable=True)
    score = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")
    responses = relationship("QuizResponse", back_populates="quiz_attempt", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<QuizAttempt(id={self.id}, quiz_id={self.quiz_id}, student_id={self.student_id})>"


class QuizResponse(Base, TimestampMixin):
    """Student response to a quiz question."""
    __tablename__ = "quiz_responses"

    id = Column(Integer, primary_key=True, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer = Column(JSONB, nullable=True)  # Student's answer
    is_correct = Column(Boolean, nullable=True)
    marks_obtained = Column(Integer, nullable=True)

    # Relationships
    quiz_attempt = relationship("QuizAttempt", back_populates="responses")
    question = relationship("QuizQuestion", back_populates="responses")

    def __repr__(self) -> str:
        return f"<QuizResponse(id={self.id}, quiz_attempt_id={self.quiz_attempt_id}, is_correct={self.is_correct})>"


class Certificate(Base, TimestampMixin):
    """Course completion certificate."""
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    issued_at = Column(Date, nullable=False, default=datetime.utcnow)
    certificate_url = Column(String(500), nullable=True)
    verify_code = Column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    course = relationship("Course", back_populates="certificates")
    student = relationship("Student", back_populates="certificates")

    def __repr__(self) -> str:
        return f"<Certificate(id={self.id}, course_id={self.course_id}, student_id={self.student_id})>"

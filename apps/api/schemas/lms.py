from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    VIDEO = "VIDEO"
    PDF = "PDF"
    TEXT = "TEXT"
    EMBED = "EMBED"


class CourseBase(BaseModel):
    name: str = Field(max_length=200)
    description: Optional[str] = None
    subject_id: Optional[int] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_published: Optional[bool] = None


class CourseResponse(CourseBase):
    id: int
    school_id: int
    teacher_id: int
    is_published: bool
    enrollment_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    title: str = Field(max_length=200)
    description: Optional[str] = None
    order_index: int = Field(ge=0)


class ChapterResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    order_index: int
    lessons: List["LessonResponse"] = []

    class Config:
        from_attributes = True


class LessonCreate(BaseModel):
    title: str = Field(max_length=200)
    content_type: ContentType
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    duration_mins: Optional[int] = None
    order_index: int = Field(ge=0)
    is_preview: bool = False


class LessonResponse(BaseModel):
    id: int
    chapter_id: int
    title: str
    content_type: ContentType
    content_url: Optional[str] = None
    duration_mins: Optional[int] = None
    order_index: int
    is_preview: bool

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    course_id: int
    title: str = Field(max_length=200)
    description: Optional[str] = None
    due_date: datetime
    max_marks: float = Field(gt=0)
    submission_type: str = "FILE"


class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    due_date: datetime
    max_marks: float
    submission_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuizCreate(BaseModel):
    course_id: int
    title: str = Field(max_length=200)
    time_limit_mins: Optional[int] = 30
    max_attempts: int = Field(default=1, ge=1)
    passing_percentage: float = Field(default=60, ge=0, le=100)
    is_published: bool = False


class QuizQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "MULTIPLE_CHOICE"  # MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER
    options: Optional[dict] = None  # JSON object with options
    correct_answer: Optional[dict] = None  # JSON object with correct answer
    marks: float = Field(gt=0)
    order_index: int = Field(ge=0)


class QuizResponse(BaseModel):
    id: int
    course_id: int
    title: str
    time_limit_mins: int
    max_attempts: int
    passing_percentage: float
    is_published: bool
    question_count: int = 0

    class Config:
        from_attributes = True


# Update forward refs
ChapterResponse.model_rebuild()

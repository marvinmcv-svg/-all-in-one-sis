from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal


class GradeScaleResponse(BaseModel):
    id: int
    letter: str
    min_percentage: float
    max_percentage: float
    grade_point: Optional[float] = None

    class Config:
        from_attributes = True


class ExamCreate(BaseModel):
    academic_term_id: int
    class_section_id: int
    subject_id: int
    exam_type_id: int
    name: str = Field(max_length=200)
    max_marks: float = Field(gt=0)
    exam_date: date
    duration_mins: Optional[int] = 60


class ExamResponse(BaseModel):
    id: int
    academic_term_id: int
    class_section_id: int
    subject_id: int
    exam_type_id: int
    name: str
    max_marks: float
    exam_date: date
    duration_mins: int
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExamResultCreate(BaseModel):
    exam_id: int
    student_id: int
    marks_obtained: float = Field(ge=0)
    remarks: Optional[str] = None


class ExamResultResponse(BaseModel):
    id: int
    exam_id: int
    student_id: int
    marks_obtained: float
    grade_id: Optional[int] = None
    remarks: Optional[str] = None
    graded_by_teacher_id: Optional[int] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

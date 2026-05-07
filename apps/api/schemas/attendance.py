from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class AttendanceMark(BaseModel):
    student_id: int
    status: AttendanceStatus
    excuse_id: Optional[int] = None
    remarks: Optional[str] = None


class BulkAttendanceMark(BaseModel):
    class_section_id: int
    date: date
    attendance: List[AttendanceMark]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    class_section_id: int
    academic_term_id: int
    date: date
    status: AttendanceStatus
    excuse_id: Optional[int] = None
    marked_by_teacher_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceExcuseCreate(BaseModel):
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
    status: str
    approved_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

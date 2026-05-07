from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class TeacherBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    gender: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None


class TeacherCreate(TeacherBase):
    password: str = Field(min_length=8)


class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None


class TeacherResponse(TeacherBase):
    id: int
    user_id: int
    employee_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

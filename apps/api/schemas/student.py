from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class StudentBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class StudentCreate(StudentBase):
    password: str = Field(min_length=8)


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    user_id: int
    student_id: str  # Admission number
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

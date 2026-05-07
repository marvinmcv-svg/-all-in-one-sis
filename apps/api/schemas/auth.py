from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "student"  # admin, teacher, student, parent
    first_name: str
    last_name: str
    school_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    person: Optional["PersonResponse"]
    
    class Config:
        from_attributes = True

class PersonResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    gender: Optional[str]
    phone: Optional[str]
    
    class Config:
        from_attributes = True

# Update forward references
UserResponse.model_rebuild()

from datetime import datetime, date
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class BaseSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class DateRangeFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

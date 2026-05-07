"""API routers package."""
from .auth import router as auth
from .students import router as students
from .teachers import router as teachers
from .attendance import router as attendance
from .grades import router as grades
from .courses import router as courses
from .assignments import router as assignments
from .quizzes import router as quizzes
from .fees import router as fees
from .schedules import router as schedules
from .academic import router as academic
from .announcements import router as announcements

__all__ = [
    "auth",
    "students",
    "teachers",
    "attendance",
    "grades",
    "courses",
    "assignments",
    "quizzes",
    "fees",
    "schedules",
    "academic",
    "announcements",
]
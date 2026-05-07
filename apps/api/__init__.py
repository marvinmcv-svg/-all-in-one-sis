"""All-in-One SIS API package."""
from .routers import (
    auth,
    students,
    teachers,
    attendance,
    grades,
    courses,
    assignments,
    quizzes,
    fees,
    schedules,
    academic,
    announcements,
)

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

"""
All-in-One SIS (Student Information System) - FastAPI Backend

This is the main application entry point that configures:
- Database connection (PostgreSQL via asyncpg)
- All API routers for the SIS modules
- CORS middleware
- Exception handlers
- Health check endpoint
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import Base, init_db, close_db
from . import (
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

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.

    On startup:
    - Initialize database tables

    On shutdown:
    - Dispose database engine
    """
    # Startup
    logger.info("Starting up All-in-One SIS API...")
    await init_db()
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="All-in-One SIS API",
    description="Student Information System with LMS, Attendance, Gradebook, and more",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Web and mobile
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent JSON response format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with a generic error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for container orchestration and load balancers.

    Returns:
        dict with status field indicating service health.
    """
    return {"status": "healthy", "service": "all-in-one-sis"}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint returning API information.

    Returns:
        dict with welcome message and documentation link.
    """
    return {
        "name": "All-in-One SIS API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Include all API routers with /api/v1 prefix
app.include_router(auth, prefix="/api/v1")
app.include_router(students, prefix="/api/v1")
app.include_router(teachers, prefix="/api/v1")
app.include_router(attendance, prefix="/api/v1")
app.include_router(grades, prefix="/api/v1")
app.include_router(courses, prefix="/api/v1")
app.include_router(assignments, prefix="/api/v1")
app.include_router(quizzes, prefix="/api/v1")
app.include_router(fees, prefix="/api/v1")
app.include_router(schedules, prefix="/api/v1")
app.include_router(academic, prefix="/api/v1")
app.include_router(announcements, prefix="/api/v1")

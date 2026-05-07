import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime

from models.user import User
from models.person import Person, UserRole
from models.student import Student, StudentStatus, Enrollment
from models.teacher import Teacher
from models.attendance import AttendanceRecord, AttendanceStatus
from models.academic import AcademicTerm, GradeLevel, ClassSection
from core.security import get_password_hash


@pytest.fixture
async def teacher_user(test_db: AsyncSession):
    """Create a test teacher user."""
    user = User(
        email="teacher@test.com",
        password_hash=get_password_hash("teacherpass123"),
        role=UserRole.TEACHER,
        is_active=True,
        tenant_id=1
    )
    test_db.add(user)
    await test_db.flush()
    
    person = Person(
        user_id=user.id,
        first_name="Test",
        last_name="Teacher"
    )
    test_db.add(person)
    await test_db.flush()
    
    teacher = Teacher(
        person_id=person.id,
        employee_id="EMP-001",
        is_active=True
    )
    test_db.add(teacher)
    await test_db.commit()
    await test_db.refresh(teacher)
    return teacher


@pytest.fixture
async def student_with_enrollment(test_db: AsyncSession, teacher_user: Teacher):
    """Create a test student with enrollment."""
    # Create academic term
    academic_term = AcademicTerm(
        name="2026 Spring",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
        is_active=True
    )
    test_db.add(academic_term)
    await test_db.flush()
    
    # Create grade level
    grade_level = GradeLevel(
        name="Grade 1",
        level=1
    )
    test_db.add(grade_level)
    await test_db.flush()
    
    # Create class section
    class_section = ClassSection(
        name="Section A",
        grade_level_id=grade_level.id,
        academic_term_id=academic_term.id
    )
    test_db.add(class_section)
    await test_db.flush()
    
    # Create student user
    user = User(
        email="student@test.com",
        password_hash=get_password_hash("studentpass123"),
        role=UserRole.STUDENT,
        is_active=True,
        tenant_id=1
    )
    test_db.add(user)
    await test_db.flush()
    
    person = Person(
        user_id=user.id,
        first_name="Test",
        last_name="Student"
    )
    test_db.add(person)
    await test_db.flush()
    
    student = Student(
        person_id=person.id,
        student_id="STU-2026-00001",
        admission_date=date(2026, 1, 1),
        status=StudentStatus.ACTIVE
    )
    test_db.add(student)
    await test_db.flush()
    
    # Create enrollment
    enrollment = Enrollment(
        student_id=student.id,
        academic_term_id=academic_term.id,
        grade_level_id=grade_level.id,
        section_id=class_section.id,
        status="active"
    )
    test_db.add(enrollment)
    await test_db.commit()
    await test_db.refresh(student)
    
    return {
        "student": student,
        "academic_term": academic_term,
        "grade_level": grade_level,
        "class_section": class_section
    }


@pytest.fixture
async def teacher_token(client: AsyncClient, teacher_user: Teacher):
    """Get teacher login token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@test.com", "password": "teacherpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
async def admin_token(client: AsyncClient, test_db: AsyncSession):
    """Create and login admin user."""
    user = User(
        email="admin@test.com",
        password_hash=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
        is_active=True,
        tenant_id=1
    )
    test_db.add(user)
    await test_db.flush()
    
    person = Person(
        user_id=user.id,
        first_name="Admin",
        last_name="User"
    )
    test_db.add(person)
    await test_db.commit()
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass123"}
    )
    return response.json()["access_token"]


async def test_mark_attendance_requires_auth(client: AsyncClient):
    """Test that marking attendance requires authentication."""
    response = await client.post(
        "/api/v1/attendance/",
        json={
            "student_id": 1,
            "status": "present"
        }
    )
    assert response.status_code == 401


async def test_mark_attendance_as_teacher(
    client: AsyncClient,
    teacher_token: str,
    student_with_enrollment: dict,
    test_db: AsyncSession
):
    """Test teacher can mark attendance for their assigned students."""
    student_id = student_with_enrollment["student"].id
    class_section_id = student_with_enrollment["class_section"].id
    academic_term_id = student_with_enrollment["academic_term"].id
    
    response = await client.post(
        f"/api/v1/attendance/?class_section_id={class_section_id}&academic_term_id={academic_term_id}&date=2026-03-15",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "student_id": student_id,
            "status": "present"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student_id
    assert data["status"] == "present"


async def test_mark_attendance_student_not_enrolled(
    client: AsyncClient,
    teacher_token: str,
    student_with_enrollment: dict
):
    """Test marking attendance for student not in class fails."""
    class_section_id = student_with_enrollment["class_section"].id
    academic_term_id = student_with_enrollment["academic_term"].id
    
    response = await client.post(
        f"/api/v1/attendance/?class_section_id={class_section_id}&academic_term_id={academic_term_id}&date=2026-03-15",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "student_id": 99999,  # Non-existent student
            "status": "present"
        }
    )
    assert response.status_code == 404


async def test_get_student_attendance_as_admin(
    client: AsyncClient,
    admin_token: str,
    student_with_enrollment: dict,
    test_db: AsyncSession
):
    """Test admin can view any student's attendance."""
    student_id = student_with_enrollment["student"].id
    class_section_id = student_with_enrollment["class_section"].id
    academic_term_id = student_with_enrollment["academic_term"].id
    
    # Create an attendance record first
    attendance = AttendanceRecord(
        student_id=student_id,
        class_section_id=class_section_id,
        academic_term_id=academic_term_id,
        date=date(2026, 3, 15),
        status=AttendanceStatus.PRESENT
    )
    test_db.add(attendance)
    await test_db.commit()
    
    response = await client.get(
        f"/api/v1/attendance/student/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_get_student_attendance_filter_by_date(
    client: AsyncClient,
    admin_token: str,
    student_with_enrollment: dict,
    test_db: AsyncSession
):
    """Test filtering student attendance by date range."""
    student_id = student_with_enrollment["student"].id
    class_section_id = student_with_enrollment["class_section"].id
    academic_term_id = student_with_enrollment["academic_term"].id
    
    # Create attendance records
    for i, day in enumerate([10, 11, 12, 15, 16]):
        attendance = AttendanceRecord(
            student_id=student_id,
            class_section_id=class_section_id,
            academic_term_id=academic_term_id,
            date=date(2026, 3, day),
            status=AttendanceStatus.PRESENT
        )
        test_db.add(attendance)
    await test_db.commit()
    
    response = await client.get(
        f"/api/v1/attendance/student/{student_id}?start_date=2026-03-12&end_date=2026-03-16",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should only get records from 2026-03-12 to 2026-03-16
    for record in data:
        record_date = datetime.strptime(record["date"], "%Y-%m-%d").date()
        assert date(2026, 3, 12) <= record_date <= date(2026, 3, 16)


async def test_get_student_attendance_requires_auth(client: AsyncClient):
    """Test that getting attendance requires authentication."""
    response = await client.get("/api/v1/attendance/student/1")
    assert response.status_code == 401

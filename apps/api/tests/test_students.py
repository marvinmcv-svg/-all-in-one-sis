import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.person import Person, UserRole
from models.student import Student, StudentStatus
from core.security import get_password_hash


@pytest.fixture
async def admin_token(client: AsyncClient, test_db: AsyncSession):
    """Create admin user and return login token."""
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


@pytest.fixture
async def student_user(test_db: AsyncSession):
    """Create a test student with user account."""
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
        admission_date=datetime.now().date(),
        status=StudentStatus.ACTIVE
    )
    test_db.add(student)
    await test_db.commit()
    await test_db.refresh(student)
    return student


@pytest.fixture
async def student_token(client: AsyncClient, test_db: AsyncSession, student_user: Student):
    """Create student user and return login token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@test.com", "password": "studentpass123"}
    )
    return response.json()["access_token"]


from datetime import datetime


async def test_list_students_requires_auth(client: AsyncClient):
    """Test that listing students requires authentication."""
    response = await client.get("/api/v1/students/")
    assert response.status_code == 401


async def test_list_students_as_admin(client: AsyncClient, admin_token: str):
    """Test that admin can list students."""
    response = await client.get(
        "/api/v1/students/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "data" in data
    assert isinstance(data["data"], list)


async def test_list_students_as_student(client: AsyncClient, student_token: str):
    """Test that students cannot list all students (forbidden)."""
    response = await client.get(
        "/api/v1/students/",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403


async def test_create_student_requires_admin(client: AsyncClient, student_token: str):
    """Test that creating student requires admin role."""
    response = await client.post(
        "/api/v1/students/",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "first_name": "New",
            "last_name": "Student",
            "gender": "male",
            "dob": "2010-01-15",
            "email": "newstudent@test.com",
            "password": "password123",
            "grade_level_id": 1,
            "section_id": 1,
            "academic_term_id": 1
        }
    )
    assert response.status_code == 403


async def test_create_student_missing_fields(client: AsyncClient, admin_token: str):
    """Test creating student with missing required fields."""
    response = await client.post(
        "/api/v1/students/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "New",
            "last_name": "Student"
            # Missing required fields: gender, dob, email, password, grade_level_id, section_id, academic_term_id
        }
    )
    assert response.status_code == 422  # Validation error


async def test_get_student_as_admin(client: AsyncClient, admin_token: str, student_user: Student):
    """Test admin can get any student."""
    response = await client.get(
        f"/api/v1/students/{student_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_user.id
    assert data["student_id"] == "STU-2026-00001"


async def test_get_student_as_self(client: AsyncClient, student_token: str, student_user: Student):
    """Test student can get their own record."""
    response = await client.get(
        f"/api/v1/students/{student_user.id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_user.id


async def test_get_nonexistent_student(client: AsyncClient, admin_token: str):
    """Test getting a student that doesn't exist."""
    response = await client.get(
        "/api/v1/students/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


async def test_get_student_forbidden_for_other_student(client: AsyncClient, test_db: AsyncSession, student_token: str):
    """Test that a student cannot view another student's record."""
    # Create another student
    user2 = User(
        email="other@test.com",
        password_hash=get_password_hash("pass123"),
        role=UserRole.STUDENT,
        is_active=True,
        tenant_id=1
    )
    test_db.add(user2)
    await test_db.flush()
    
    person2 = Person(
        user_id=user2.id,
        first_name="Other",
        last_name="Student"
    )
    test_db.add(person2)
    await test_db.flush()
    
    other_student = Student(
        person_id=person2.id,
        student_id="STU-2026-00002",
        admission_date=datetime.now().date(),
        status=StudentStatus.ACTIVE
    )
    test_db.add(other_student)
    await test_db.commit()
    await test_db.refresh(other_student)
    
    response = await client.get(
        f"/api/v1/students/{other_student.id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403

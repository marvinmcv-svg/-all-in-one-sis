import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.person import Person, UserRole
from core.security import get_password_hash


@pytest.fixture
async def test_admin(test_db: AsyncSession):
    """Create a test admin user."""
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
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_student_user(test_db: AsyncSession):
    """Create a test student user."""
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
    await test_db.commit()
    await test_db.refresh(user)
    return user


async def test_login_success(client: AsyncClient, test_admin: User):
    """Test successful login with valid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@test.com"
    assert data["user"]["role"] == "admin"


async def test_login_invalid_credentials(client: AsyncClient, test_admin: User):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect email or password"


async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "anypassword"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect email or password"


async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "newuserpass123",
            "role": "student",
            "first_name": "New",
            "last_name": "User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "student"
    assert data["is_active"] is True
    assert data["person"]["first_name"] == "New"
    assert data["person"]["last_name"] == "User"


async def test_register_duplicate_email(client: AsyncClient, test_admin: User):
    """Test registration with already registered email."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "somepass123",
            "role": "student",
            "first_name": "Another",
            "last_name": "User"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"


async def test_register_as_teacher(client: AsyncClient):
    """Test registration with teacher role."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@test.com",
            "password": "teacherpass123",
            "role": "teacher",
            "first_name": "Test",
            "last_name": "Teacher"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "teacher"


async def test_get_current_user(client: AsyncClient, test_admin: User):
    """Test getting current user info with valid token."""
    # First login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass123"}
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


async def test_get_current_user_without_token(client: AsyncClient):
    """Test getting current user without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"}
    )
    assert response.status_code == 401

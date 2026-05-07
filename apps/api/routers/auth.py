from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from ..database import get_db
from ..models.user import User
from ..models.person import Person
from ..schemas.auth import (
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    RegisterRequest, UserResponse
)
from ..core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token
)
from ..core.deps import get_current_user
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # Find user
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Get person info
    person = None
    if user.person:
        person = {
            "id": user.person.id,
            "first_name": user.person.first_name,
            "last_name": user.person.last_name,
            "gender": user.person.gender,
            "phone": user.person.phone
        }
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            last_login=user.last_login,
            person=person
        )
    )

@router.post("/register", response_model=UserResponse)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # Check if email exists
    result = await db.execute(
        select(User).where(User.email == register_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=register_data.email,
        password_hash=get_password_hash(register_data.password),
        role=register_data.role,
        is_active=True
    )
    db.add(user)
    await db.flush()
    
    # Create person
    person = Person(
        user_id=user.id,
        first_name=register_data.first_name,
        last_name=register_data.last_name
    )
    db.add(person)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        person={
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "gender": person.gender,
            "phone": person.phone
        }
    )

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(refresh_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return RefreshResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    person = None
    if current_user.person:
        person = {
            "id": current_user.person.id,
            "first_name": current_user.person.first_name,
            "last_name": current_user.person.last_name,
            "gender": current_user.person.gender,
            "phone": current_user.person.phone
        }
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        person=person
    )
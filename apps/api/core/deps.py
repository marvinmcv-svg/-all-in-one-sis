from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from jose import JWTError, jwt
from sqlalchemy import select

from .security import decode_token, verify_password, get_password_hash
from ..database import get_db
from ..models.user import User
from ..models.person import Person
from ..config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

async def get_current_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not a teacher")
    return current_user

async def get_current_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Not a student")
    return current_user

async def get_current_parent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Not a parent")
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not an admin")
    return current_user

def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

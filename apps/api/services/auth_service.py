from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.user import User
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from ...schemas.auth import TokenResponse

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    async def create_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(data={"sub": str(user.id), "type": "access"})
        refresh_token = create_refresh_token(data={"sub": str(user.id), "type": "refresh"})
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30,
        )

    async def register_user(self, email: str, password: str, role: str) -> User:
        from ...models.person import Person
        password_hash = get_password_hash(password)
        user = User(email=email, password_hash=password_hash, role=role)
        self.db.add(user)
        await self.db.flush()
        person = Person(user_id=user.id)
        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(user)
        return user

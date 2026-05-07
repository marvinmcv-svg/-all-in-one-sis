from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...models.student import Student
from ...models.person import Person
from ...models.user import User

class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student(self, student_id: int) -> Optional[Student]:
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_students(self, skip: int = 0, limit: int = 100) -> List[Student]:
        result = await self.db.execute(
            select(Student).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def search_students(self, query: str) -> List[Student]:
        result = await self.db.execute(
            select(Student)
            .join(Person)
            .where(
                Person.first_name.ilike(f"%{query}%") |
                Person.last_name.ilike(f"%{query}%") |
                Student.student_id.ilike(f"%{query}%")
            )
        )
        return list(result.scalars().all())

    async def count_students(self) -> int:
        result = await self.db.execute(select(func.count(Student.id)))
        return result.scalar() or 0

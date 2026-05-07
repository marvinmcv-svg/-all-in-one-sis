from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.lms import Course, CourseEnrollment, Chapter, Lesson

class LMSService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_course(self, course_data: dict) -> Course:
        course = Course(**course_data)
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def enroll_student(self, course_id: int, student_id: int) -> CourseEnrollment:
        enrollment = CourseEnrollment(course_id=course_id, student_id=student_id)
        self.db.add(enrollment)
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment

    async def get_course_content(self, course_id: int) -> Optional[Course]:
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()
        if course:
            chapters_result = await self.db.execute(
                select(Chapter)
                .where(Chapter.course_id == course_id)
                .order_by(Chapter.order_index)
            )
            course.chapters = list(chapters_result.scalars().all())
        return course

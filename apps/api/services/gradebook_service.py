from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.gradebook import Exam, ExamResult, GradingSystem

class GradebookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_exam(self, exam_data: dict) -> Exam:
        exam = Exam(**exam_data)
        self.db.add(exam)
        await self.db.commit()
        await self.db.refresh(exam)
        return exam

    async def submit_grade(
        self,
        exam_id: int,
        student_id: int,
        marks_obtained: float,
        teacher_id: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> ExamResult:
        result = ExamResult(
            exam_id=exam_id,
            student_id=student_id,
            marks_obtained=marks_obtained,
            graded_by_teacher_id=teacher_id,
            remarks=remarks
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def get_student_grades(self, student_id: int) -> List[ExamResult]:
        result = await self.db.execute(
            select(ExamResult)
            .where(ExamResult.student_id == student_id)
            .order_by(ExamResult.graded_at.desc())
        )
        return list(result.scalars().all())

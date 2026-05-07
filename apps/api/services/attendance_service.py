from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ...models.attendance import AttendanceRecord, AttendanceExcuse

class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_attendance(
        self,
        student_id: int,
        class_section_id: int,
        academic_term_id: int,
        attendance_date: date,
        status: str,
        teacher_id: Optional[int] = None
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            student_id=student_id,
            class_section_id=class_section_id,
            academic_term_id=academic_term_id,
            date=attendance_date,
            status=status,
            marked_by_teacher_id=teacher_id
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_student_attendance(
        self,
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AttendanceRecord]:
        query = select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
        if start_date:
            query = query.where(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.where(AttendanceRecord.date <= end_date)
        result = await self.db.execute(query.order_by(AttendanceRecord.date.desc()))
        return list(result.scalars().all())

    async def create_excuse(
        self,
        student_id: int,
        start_date: date,
        end_date: date,
        reason: str
    ) -> AttendanceExcuse:
        excuse = AttendanceExcuse(
            student_id=student_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="PENDING"
        )
        self.db.add(excuse)
        await self.db.commit()
        await self.db.refresh(excuse)
        return excuse

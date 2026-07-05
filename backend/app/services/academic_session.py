import io
import csv
from typing import Tuple
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.academic_session import AcademicSessionCreate, AcademicSessionUpdate
from app.repositories.academic_session import academic_session_repo
from app.models.student import StudentAdmission

class AcademicSessionService:
    async def _validate_constraints(
        self, db: AsyncSession, payload: AcademicSessionCreate | AcademicSessionUpdate, current_id: int = None
    ) -> None:
        if payload.start_date >= payload.end_date:
            raise HTTPException(status_code=400, detail="Start Date must be before End Date.")
            
        # Duplicate name
        existing_name = await academic_session_repo.get_by_name(db, payload.session_name)
        if existing_name and (current_id is None or existing_name.id != current_id):
            raise HTTPException(status_code=400, detail="An Academic Session with this name already exists.")
            
        # Overlap
        overlaps = await academic_session_repo.get_overlapping_sessions(db, payload.start_date, payload.end_date, current_id)
        if overlaps:
            raise HTTPException(status_code=400, detail="Dates overlap with another existing Academic Session.")

    async def create_academic_session(self, db: AsyncSession, payload: AcademicSessionCreate):
        await self._validate_constraints(db, payload)
        if payload.is_active:
            await academic_session_repo.unset_active_sessions(db)
        return await academic_session_repo.create(db, payload)

    async def update_academic_session(self, db: AsyncSession, id: int, payload: AcademicSessionUpdate):
        db_obj = await academic_session_repo.get(db, id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Academic Session not found.")
            
        await self._validate_constraints(db, payload, id)
        if payload.is_active and not db_obj.is_active:
            await academic_session_repo.unset_active_sessions(db)
            
        return await academic_session_repo.update(db, db_obj, payload)

    async def delete_academic_session(self, db: AsyncSession, id: int) -> None:
        db_obj = await academic_session_repo.get(db, id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Academic Session not found.")
            
        # Safe Delete Check
        stmt = select(StudentAdmission).where(StudentAdmission.academic_session_id == id).limit(1)
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="Academic Session is currently in use (Student Admissions exist) and cannot be deleted."
            )
            
        await academic_session_repo.delete(db, id)

    async def export_academic_sessions(self, db: AsyncSession) -> Tuple[bytes, str, str]:
        sessions, _ = await academic_session_repo.get_multi(db, limit=10000)
        
        data = []
        for s in sessions:
            data.append({
                "ID": s.id,
                "Session Name": s.session_name,
                "Start Date": s.start_date.isoformat(),
                "End Date": s.end_date.isoformat(),
                "Current Session": "Yes" if s.is_active else "No"
            })
            
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["ID", "Session Name", "Start Date", "End Date", "Current Session"])
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue().encode('utf-8'), "academic_sessions.csv", "text/csv"

academic_session_service = AcademicSessionService()

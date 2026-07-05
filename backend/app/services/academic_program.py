import io
import csv
from typing import Tuple, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.academic_program import (
    AcademicProgramCreate, 
    AcademicProgramUpdate, 
    AcademicProgramListResponse
)
from app.repositories.academic_program import academic_program_repo
from app.models.student import StudentAdmission
from app.models.academic import Department, Program, Specialization

class AcademicProgramService:
    async def _validate_constraints(
        self, db: AsyncSession, payload: AcademicProgramCreate | AcademicProgramUpdate, current_id: int = None
    ) -> None:
        if payload.duration_years <= 0:
            raise HTTPException(status_code=400, detail="Duration must be greater than 0.")
        if payload.total_semesters <= 0:
            raise HTTPException(status_code=400, detail="Semesters must be greater than 0.")
        if payload.entry_semester <= 0 or payload.entry_semester > payload.total_semesters:
            raise HTTPException(status_code=400, detail="Entry semester must be valid and less than or equal to total semesters.")

        # Check Department
        dept = await db.get(Department, payload.department_id)
        if not dept or not dept.active:
            raise HTTPException(status_code=400, detail="Invalid or inactive department selected.")
            
        # Check Program
        prog = await db.get(Program, payload.program_id)
        if not prog or not prog.active:
            raise HTTPException(status_code=400, detail="Invalid or inactive program selected.")
            
        # Check Specialization
        if payload.specialization_id:
            spec = await db.get(Specialization, payload.specialization_id)
            if not spec or not spec.active:
                raise HTTPException(status_code=400, detail="Invalid or inactive specialization selected.")
            if spec.program_id != payload.program_id:
                raise HTTPException(status_code=400, detail="Specialization does not belong to the selected Program.")

        # Check duplicate
        existing = await academic_program_repo.get_by_unique_constraint(
            db, payload.department_id, payload.program_id, payload.specialization_id
        )
        if existing and (current_id is None or existing.id != current_id):
            raise HTTPException(
                status_code=400, 
                detail="An Academic Program with this Department, Program, and Specialization already exists."
            )

    async def create_academic_program(self, db: AsyncSession, payload: AcademicProgramCreate):
        await self._validate_constraints(db, payload)
        return await academic_program_repo.create(db, payload)

    async def update_academic_program(self, db: AsyncSession, prog_id: int, payload: AcademicProgramUpdate):
        db_obj = await academic_program_repo.get(db, prog_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Academic Program not found.")
            
        await self._validate_constraints(db, payload, current_id=prog_id)
        return await academic_program_repo.update(db, db_obj, payload)

    async def delete_academic_program(self, db: AsyncSession, prog_id: int) -> None:
        db_obj = await academic_program_repo.get(db, prog_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Academic Program not found.")
            
        # Safe Delete Check
        # 1. Check Student Admissions
        stmt = select(StudentAdmission).where(StudentAdmission.academic_program_id == prog_id).limit(1)
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail="Academic Program is currently in use (Student Admissions exist). Deletion is not allowed."
            )
            
        # Placeholder for Subjects, Timetable, Results, Attendance when they are added to DB
        
        await academic_program_repo.delete(db, prog_id)

    async def export_academic_programs(self, db: AsyncSession, format: str = "csv") -> Tuple[bytes, str, str]:
        programs, _ = await academic_program_repo.get_multi(db, limit=10000)
        
        data = []
        for p in programs:
            data.append({
                "ID": p.id,
                "Department": p.department.name if p.department else "",
                "Program": p.program.name if p.program else "",
                "Specialization": p.specialization.name if p.specialization else "",
                "Duration (Years)": p.duration_years,
                "Total Semesters": p.total_semesters,
                "Entry Semester": p.entry_semester
            })
            
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["ID", "Department", "Program", "Specialization", "Duration (Years)", "Total Semesters", "Entry Semester"])
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue().encode('utf-8'), "academic_programs.csv", "text/csv"

academic_program_service = AcademicProgramService()

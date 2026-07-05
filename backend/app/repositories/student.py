from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.student import (
    Student,
    StudentAddress,
    StudentAdmission,
    DocumentType,
    StudentDocument,
    StudentEntranceExam,
    StudentGuardian,
    StudentQualification,
)

class StudentRepository(BaseRepository[Student]):
    def __init__(self):
        super().__init__(Student)

    async def get_by_computer_code(self, db: AsyncSession, computer_code: int) -> Optional[Student]:
        return await self.get_by_attribute(db, "computer_code", computer_code)

    async def get_by_enrollment_no(self, db: AsyncSession, enrollment_no: str) -> Optional[Student]:
        return await self.get_by_attribute(db, "enrollment_no", enrollment_no)

class StudentAddressRepository(BaseRepository[StudentAddress]):
    def __init__(self):
        super().__init__(StudentAddress)

    async def get_by_student(self, db: AsyncSession, student_id: int) -> List[StudentAddress]:
        query = select(StudentAddress).where(StudentAddress.student_id == student_id)
        result = await db.execute(query)
        return list(result.scalars().all())

class StudentAdmissionRepository(BaseRepository[StudentAdmission]):
    def __init__(self):
        super().__init__(StudentAdmission)

    async def get_by_student(self, db: AsyncSession, student_id: int) -> Optional[StudentAdmission]:
        return await self.get_by_attribute(db, "student_id", student_id)

class DocumentTypeRepository(BaseRepository[DocumentType]):
    def __init__(self):
        super().__init__(DocumentType)

class StudentDocumentRepository(BaseRepository[StudentDocument]):
    def __init__(self):
        super().__init__(StudentDocument)

    async def get_by_student_and_type(self, db: AsyncSession, student_id: int, doc_type_id: int) -> Optional[StudentDocument]:
        query = select(StudentDocument).where(
            StudentDocument.student_id == student_id,
            StudentDocument.document_type_id == doc_type_id
        )
        result = await db.execute(query)
        return result.scalars().first()

class StudentEntranceExamRepository(BaseRepository[StudentEntranceExam]):
    def __init__(self):
        super().__init__(StudentEntranceExam)

class StudentGuardianRepository(BaseRepository[StudentGuardian]):
    def __init__(self):
        super().__init__(StudentGuardian)

class StudentQualificationRepository(BaseRepository[StudentQualification]):
    def __init__(self):
        super().__init__(StudentQualification)

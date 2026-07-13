# Node.js Comparison:
# In Node.js (without repository pattern), database operations are often called directly in the controller or service:
# e.g., const student = await Student.findOne({ where: { enrollment_no } }); (Sequelize)
# e.g., const student = await Student.findOne({ enrollment_no }); (Mongoose)
#
# With Repository Pattern:
# We isolate all database queries inside "Repository" classes. This makes the database layer swappable and easier to test.
#
# FastAPI/SQLAlchemy Flow:
# Router ➔ Service ➔ Repository (runs SQL/ORM query) ➔ Database

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

# StudentRepository handles DB calls for the 'Student' table.
# It inherits generic CRUD methods (get, get_multi, create, update, remove) from BaseRepository.
#
# Express/Sequelize Equivalent:
# class StudentRepository {
#   async get(id) { return await Student.findByPk(id); }
#   async create(data) { return await Student.create(data); }
# }
class StudentRepository(BaseRepository[Student]):
    def __init__(self):
        # Calls the parent constructor BaseRepository(Student) to bind the database model
        super().__init__(Student)

    # Custom database query
    # Express Equivalent (Sequelize):
    # async getByComputerCode(computerCode) { return await Student.findOne({ where: { computer_code: computerCode } }); }
    # Express Equivalent (Mongoose):
    # async getByComputerCode(computerCode) { return await Student.findOne({ computer_code: computerCode }); }
    async def get_by_computer_code(self, db: AsyncSession, computer_code: int) -> Optional[Student]:
        return await self.get_by_attribute(db, "computer_code", computer_code)

    # Express Equivalent (Sequelize):
    # async getByEnrollmentNo(enrollmentNo) { return await Student.findOne({ where: { enrollment_no: enrollmentNo } }); }
    async def get_by_enrollment_no(self, db: AsyncSession, enrollment_no: str) -> Optional[Student]:
        return await self.get_by_attribute(db, "enrollment_no", enrollment_no)


# StudentAddressRepository handles DB calls for 'student_address' table.
class StudentAddressRepository(BaseRepository[StudentAddress]):
    def __init__(self):
        super().__init__(StudentAddress)

    # Express Equivalent (Sequelize):
    # async getByStudent(studentId) { return await StudentAddress.findAll({ where: { student_id: studentId } }); }
    #
    # FastAPI/SQLAlchemy query breakdown:
    # 1. select(StudentAddress): Generates 'SELECT * FROM student_address'
    # 2. .where(...): Adds 'WHERE student_id = :student_id'
    # 3. await db.execute(query): Runs the query asynchronously
    # 4. result.scalars().all(): Converts result rows into a list of StudentAddress objects
    async def get_by_student(self, db: AsyncSession, student_id: int) -> List[StudentAddress]:
        query = select(StudentAddress).where(StudentAddress.student_id == student_id)
        result = await db.execute(query)
        return list(result.scalars().all())


# StudentAdmissionRepository handles DB calls for 'student_admission' table.
class StudentAdmissionRepository(BaseRepository[StudentAdmission]):
    def __init__(self):
        super().__init__(StudentAdmission)

    # Express Equivalent (Sequelize):
    # async getByStudent(studentId) { return await StudentAdmission.findOne({ where: { student_id: studentId } }); }
    async def get_by_student(self, db: AsyncSession, student_id: int) -> Optional[StudentAdmission]:
        return await self.get_by_attribute(db, "student_id", student_id)


# DocumentTypeRepository handles DB calls for 'document_type' table.
class DocumentTypeRepository(BaseRepository[DocumentType]):
    def __init__(self):
        super().__init__(DocumentType)


# StudentDocumentRepository handles DB calls for 'student_document' table.
class StudentDocumentRepository(BaseRepository[StudentDocument]):
    def __init__(self):
        super().__init__(StudentDocument)

    # Express Equivalent (Sequelize):
    # async getByStudentAndType(studentId, docTypeId) {
    #   return await StudentDocument.findOne({ where: { student_id: studentId, document_type_id: docTypeId } });
    # }
    async def get_by_student_and_type(self, db: AsyncSession, student_id: int, doc_type_id: int) -> Optional[StudentDocument]:
        query = select(StudentDocument).where(
            StudentDocument.student_id == student_id,
            StudentDocument.document_type_id == doc_type_id
        )
        result = await db.execute(query)
        return result.scalars().first()


# StudentEntranceExamRepository handles DB calls for 'student_entrance_exam' table.
class StudentEntranceExamRepository(BaseRepository[StudentEntranceExam]):
    def __init__(self):
        super().__init__(StudentEntranceExam)


# StudentGuardianRepository handles DB calls for 'student_guardian' table.
class StudentGuardianRepository(BaseRepository[StudentGuardian]):
    def __init__(self):
        super().__init__(StudentGuardian)


# StudentQualificationRepository handles DB calls for 'student_qualification' table.
class StudentQualificationRepository(BaseRepository[StudentQualification]):
    def __init__(self):
        super().__init__(StudentQualification)

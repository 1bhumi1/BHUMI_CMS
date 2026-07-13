# Node.js Comparison:
# In Node.js/Express architecture, the Service layer handles business logic:
# e.g., validation checks, password hashing, and orchestrating multiple model/repository operations.
# Example:
# class StudentService {
#   async createStudent(studentData) {
#     const existing = await StudentRepository.findOne({ aadhar_no });
#     if (existing) throw new Error('Aadhar exists');
#     return await StudentRepository.create(studentData);
#   }
# }
#
# FastAPI/SQLAlchemy Flow:
# Router ➔ Service Layer (handles business logic/orchestration) ➔ Repositories ➔ Database

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.student import (
    Student,
    StudentAddress,
    StudentAdmission,
    StudentDocument,
    StudentEntranceExam,
    StudentGuardian,
    StudentQualification,
)
from app.models.auth import Login
from app.repositories import (
    student_repo,
    student_address_repo,
    student_admission_repo,
    student_guardian_repo,
    student_qualification_repo,
    student_entrance_exam_repo,
    student_document_repo,
    login_repo,
    refresh_token_repo,
)
from app.schemas.student import (
    CompositeStudentAdmissionCreate,
    CompositeStudentUpdate,
    StudentUpdate,
    StudentProfileResponse,
    StudentResponse,
    StudentAddressResponse,
    StudentAdmissionResponse,
    StudentGuardianResponse,
    StudentQualificationResponse,
    StudentEntranceExamResponse,
    StudentDocumentResponse,
)
from app.security.password import hash_password

class StudentService:
    # Fetch nested student profile containing addresses, admission, guardians, qualifications, entrance exams, and documents.
    async def get_student_profile(self, db: AsyncSession, student_id: int) -> StudentProfileResponse:
        """
        Fetch the complete nested profile of a student.
        """
        # Node.js Equivalent:
        # const student = await StudentRepository.findById(studentId);
        # if (!student) throw new NotFoundError('Student not found');
        student = await student_repo.get(db, student_id)
        if not student:
            # Express: Instead of res.status(404).json(...), we raise HTTPException which is caught by global exception handlers.
            raise HTTPException(status_code=404, detail="Student not found")

        # Fetch associated records (equivalent to Sequelize findAll with where: { student_id })
        addresses = await student_address_repo.get_multi(db, filters={"student_id": student_id})
        admission = await student_admission_repo.get_by_student(db, student_id)
        guardians = await student_guardian_repo.get_multi(db, filters={"student_id": student_id})
        qualifications = await student_qualification_repo.get_multi(db, filters={"student_id": student_id})
        exams = await student_entrance_exam_repo.get_multi(db, filters={"student_id": student_id})
        documents = await student_document_repo.get_multi(db, filters={"student_id": student_id})

        # Pydantic Serialization:
        # model_validate() converts SQLAlchemy model instances to validated Pydantic response objects (DTOs).
        # Node.js Equivalent:
        # return { student: student.toJSON(), addresses: addresses.map(a => a.toJSON()), ... }
        return StudentProfileResponse(
            student=StudentResponse.model_validate(student),
            addresses=[StudentAddressResponse.model_validate(a) for a in addresses],
            admission=StudentAdmissionResponse.model_validate(admission) if admission else None,
            guardians=[StudentGuardianResponse.model_validate(g) for g in guardians],
            qualifications=[StudentQualificationResponse.model_validate(q) for q in qualifications],
            entrance_exams=[StudentEntranceExamResponse.model_validate(e) for e in exams],
            documents=[StudentDocumentResponse.model_validate(d) for d in documents],
        )

    # Generate the next sequential computer code for students.
    # Express Equivalent (Sequelize):
    # const maxCode = await Student.max('computer_code');
    async def generate_next_computer_code(self, db: AsyncSession) -> int:
        """
        Generate the next sequential computer code for students.
        """
        query = select(func.max(Student.computer_code))
        result = await db.execute(query)
        max_code = result.scalar()
        if max_code is None:
            return 260001  # Start code for academic year 2026
        return max_code + 1

    # Orchestrate student admission record and related details creation.
    async def create_student_admission(
        self, db: AsyncSession, payload: CompositeStudentAdmissionCreate
    ) -> StudentProfileResponse:
        """
        Create a new student admission record along with addresses, guardians, qualifications, 
        and automatic creation of Login credentials.
        """
        # Aadhar existence check
        # Express Equivalent:
        # if (payload.student.aadhar_no) {
        #   const existing = await StudentRepository.findOne({ aadhar_no: payload.student.aadhar_no });
        #   if (existing) throw new BadRequestError("Student with this Aadhar already exists");
        # }
        if payload.student.aadhar_no:
            existing = await student_repo.get_by_attribute(db, "aadhar_no", payload.student.aadhar_no)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student with this Aadhar number already exists"
                )

        # Computer code existence check
        comp_code = payload.student.computer_code
        existing_code = await student_repo.get_by_attribute(db, "computer_code", comp_code)
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student with this computer code already exists"
            )
        
        # 1. Create Student
        # model_dump() is equivalent to converting request body helper object to a raw JS object.
        # Express: const studentData = req.body.student;
        student_data = payload.student.model_dump()
        student = await student_repo.create(db, obj_in=student_data)
        
        # SQLAlchemy Flush (db.flush() vs db.commit()):
        # db.flush() sends SQL write statements to MySQL within the current transaction context.
        # This prompts MySQL to allocate auto-increment IDs (student.id is populated),
        # but does NOT complete/commit the transaction yet.
        # Node.js Equivalent: In Sequelize/Mongoose, creating a model instance updates the instance object in-memory immediately.
        # In SQLAlchemy, we must run await db.flush() to populate autogenerated columns (id, timestamps) before referencing them.
        await db.flush()  # Populates student.id

        # 2. Create Login Credentials
        # Password hashing matches standard Node.js libraries like bcrypt.hash()
        default_pwd = "password"
        if payload.student.date_of_birth:
            default_pwd = payload.student.date_of_birth.strftime("%d%m%Y")
            
        password_hash = hash_password(default_pwd)
        await login_repo.create(db, obj_in={
            "computer_code": str(comp_code),
            "password_hash": password_hash,
            "student_id": student.id,
            "active": True
        })

        # 3. Create Addresses
        # Express Equivalent:
        # const createdAddresses = await Promise.all(payload.addresses.map(addr => StudentAddress.create({ ...addr, student_id: student.id })));
        created_addresses = []
        for addr_in in payload.addresses:
            addr_data = addr_in.model_dump()
            addr_data["student_id"] = student.id
            addr = await student_address_repo.create(db, obj_in=addr_data)
            created_addresses.append(addr)

        # 4. Create Admission Details
        admission_data = payload.admission.model_dump()
        admission_data["student_id"] = student.id
        admission = await student_admission_repo.create(db, obj_in=admission_data)

        # 5. Create Guardians
        created_guardians = []
        for guardian_in in payload.guardians:
            guard_data = guardian_in.model_dump()
            guard_data["student_id"] = student.id
            guard = await student_guardian_repo.create(db, obj_in=guard_data)
            created_guardians.append(guard)

        # 6. Create Qualifications
        created_qualifications = []
        for qual_in in payload.qualifications:
            qual_data = qual_in.model_dump()
            qual_data["student_id"] = student.id
            qual = await student_qualification_repo.create(db, obj_in=qual_data)
            created_qualifications.append(qual)

        # 7. Create Entrance Exams
        created_exams = []
        for exam_in in payload.entrance_exams:
            exam_data = exam_in.model_dump()
            exam_data["student_id"] = student.id
            exam = await student_entrance_exam_repo.create(db, obj_in=exam_data)
            created_exams.append(exam)

        await db.flush()

        return StudentProfileResponse(
            student=StudentResponse.model_validate(student),
            addresses=[StudentAddressResponse.model_validate(a) for a in created_addresses],
            admission=StudentAdmissionResponse.model_validate(admission),
            guardians=[StudentGuardianResponse.model_validate(g) for g in created_guardians],
            qualifications=[StudentQualificationResponse.model_validate(q) for q in created_qualifications],
            entrance_exams=[StudentEntranceExamResponse.model_validate(e) for e in created_exams],
            documents=[]
        )

    # Update basic student details and nested relational collections.
    async def update_student(self, db: AsyncSession, student_id: int, payload: CompositeStudentUpdate) -> StudentResponse:
        """
        Update basic student details and nested relations (addresses, guardians, qualifications, etc.).
        """
        # Node.js Equivalent:
        # const student = await StudentRepository.findById(studentId);
        # if (!student) throw new NotFoundError('Student not found');
        student = await student_repo.get(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        # exclude_unset=True matches Sequelize updating only specified properties (PATCH behavior)
        # Express: const updateData = _.omitBy(req.body.student, _.isUndefined);
        update_data = payload.student.model_dump(exclude_unset=True)
        updated_student = await student_repo.update(db, db_obj=student, obj_in=update_data)
        
        # Sync attributes with Login table (active status or computer code changed)
        if "active" in update_data or "computer_code" in update_data:
            login = await login_repo.get_by_student_id(db, student_id)
            if login:
                if "active" in update_data:
                    login.active = update_data["active"]
                if "computer_code" in update_data and update_data["computer_code"] is not None:
                    login.computer_code = str(update_data["computer_code"])
                db.add(login) # Express: Mark login record as modified/dirty so it gets updated
        
        # Update Addresses: Delete existing and replace with new addresses
        # Express Equivalent:
        # if (payload.addresses) {
        #   await StudentAddress.destroy({ where: { student_id } });
        #   await Promise.all(payload.addresses.map(a => StudentAddress.create({ ...a, student_id })));
        # }
        if payload.addresses is not None:
            existing_addrs = await student_address_repo.get_by_student(db, student_id)
            for addr in existing_addrs:
                # db.delete(obj) instructs the session to remove the record.
                # Express Equivalent (Sequelize): await addr.destroy();
                await db.delete(addr)
            
            for addr_in in payload.addresses:
                addr_data = addr_in.model_dump()
                addr_data["student_id"] = student_id
                await student_address_repo.create(db, obj_in=addr_data)
                
        # Update Admission
        if payload.admission is not None:
            existing_adm = await student_admission_repo.get_by_student(db, student_id)
            if existing_adm:
                adm_data = payload.admission.model_dump(exclude_unset=True)
                await student_admission_repo.update(db, db_obj=existing_adm, obj_in=adm_data)
                
        # Update Guardians: Delete existing and replace
        if payload.guardians is not None:
            existing_guards = await student_guardian_repo.get_multi(db, filters={"student_id": student_id})
            for guard in existing_guards:
                await db.delete(guard)
            for guard_in in payload.guardians:
                guard_data = guard_in.model_dump()
                guard_data["student_id"] = student_id
                await student_guardian_repo.create(db, obj_in=guard_data)
                
        # Update Qualifications: Delete existing and replace
        if payload.qualifications is not None:
            existing_quals = await student_qualification_repo.get_multi(db, filters={"student_id": student_id})
            for qual in existing_quals:
                await db.delete(qual)
            for qual_in in payload.qualifications:
                qual_data = qual_in.model_dump()
                qual_data["student_id"] = student_id
                await student_qualification_repo.create(db, obj_in=qual_data)
                
        # Update Entrance Exams: Delete existing and replace
        if payload.entrance_exams is not None:
            existing_exams = await student_entrance_exam_repo.get_multi(db, filters={"student_id": student_id})
            for exam in existing_exams:
                await db.delete(exam)
            for exam_in in payload.entrance_exams:
                exam_data = exam_in.model_dump()
                exam_data["student_id"] = student_id
                await student_entrance_exam_repo.create(db, obj_in=exam_data)
                
        await db.flush()
        return StudentResponse.model_validate(updated_student)
        
    # Reset password back to Date of Birth
    async def reset_student_password(self, db: AsyncSession, student_id: int) -> None:
        """
        Reset a student's password back to their DOB.
        Admin action only.
        """
        student = await student_repo.get(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        login = await login_repo.get_by_student_id(db, student_id)
        if not login:
            raise HTTPException(status_code=404, detail="Login record not found for student")
            
        default_pwd = "password"
        if student.date_of_birth:
            default_pwd = student.date_of_birth.strftime("%d%m%Y")
            
        login.password_hash = hash_password(default_pwd)
        login.is_first_login = True
        
        # db.add(login) saves changes to session.
        # Express Equivalent: await login.save();
        db.add(login)
        
        # Delete active tokens so they are logged out
        await refresh_token_repo.delete_by_user_id(db, login.id)
        await db.flush()

    # Soft delete student and login record.
    # Soft delete sets active = False.
    # Express Equivalent:
    # await Student.update({ active: false }, { where: { id: studentId } });
    async def delete_student(self, db: AsyncSession, student_id: int) -> None:
        """
        Soft delete student and login record.
        """
        student = await student_repo.get(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        student.active = False
        db.add(student)
        
        login = await login_repo.get_by_student_id(db, student_id)
        if login:
            login.active = False
            db.add(login)
            # Remove active refresh tokens too
            await refresh_token_repo.delete_by_user_id(db, login.id)

# Export instantiated singleton class service
# Express: module.exports = new StudentService();
student_service = StudentService()

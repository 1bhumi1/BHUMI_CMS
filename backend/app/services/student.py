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
    async def get_student_profile(self, db: AsyncSession, student_id: int) -> StudentProfileResponse:
        """
        Fetch the complete nested profile of a student.
        """
        student = await student_repo.get(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Fetch all associated data
        addresses = await student_address_repo.get_multi(db, filters={"student_id": student_id})
        admission = await student_admission_repo.get_by_student(db, student_id)
        guardians = await student_guardian_repo.get_multi(db, filters={"student_id": student_id})
        qualifications = await student_qualification_repo.get_multi(db, filters={"student_id": student_id})
        exams = await student_entrance_exam_repo.get_multi(db, filters={"student_id": student_id})
        documents = await student_document_repo.get_multi(db, filters={"student_id": student_id})

        return StudentProfileResponse(
            student=StudentResponse.model_validate(student),
            addresses=[StudentAddressResponse.model_validate(a) for a in addresses],
            admission=StudentAdmissionResponse.model_validate(admission) if admission else None,
            guardians=[StudentGuardianResponse.model_validate(g) for g in guardians],
            qualifications=[StudentQualificationResponse.model_validate(q) for q in qualifications],
            entrance_exams=[StudentEntranceExamResponse.model_validate(e) for e in exams],
            documents=[StudentDocumentResponse.model_validate(d) for d in documents],
        )

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

    async def create_student_admission(
        self, db: AsyncSession, payload: CompositeStudentAdmissionCreate
    ) -> StudentProfileResponse:
        """
        Create a new student admission record along with addresses, guardians, qualifications, 
        and automatic creation of Login credentials.
        """
        # Check if student with same Aadhar exists
        if payload.student.aadhar_no:
            existing = await student_repo.get_by_attribute(db, "aadhar_no", payload.student.aadhar_no)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student with this Aadhar number already exists"
                )

        # Check if student with same computer code exists
        comp_code = payload.student.computer_code
        existing_code = await student_repo.get_by_attribute(db, "computer_code", comp_code)
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student with this computer code already exists"
            )
        
        # 1. Create Student
        student_data = payload.student.model_dump()
        student = await student_repo.create(db, obj_in=student_data)
        await db.flush()  # Populates student.id

        # 2. Create Login Credentials
        # Default password is their date of birth in DDMMYYYY format
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

    async def update_student(self, db: AsyncSession, student_id: int, payload: CompositeStudentUpdate) -> StudentResponse:
        """
        Update basic student details and nested relations (addresses, guardians, qualifications, etc.).
        """
        student = await student_repo.get(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        update_data = payload.student.model_dump(exclude_unset=True)
        updated_student = await student_repo.update(db, db_obj=student, obj_in=update_data)
        
        # If user deactivated student or changed computer_code, update login credentials too
        if "active" in update_data or "computer_code" in update_data:
            login = await login_repo.get_by_student_id(db, student_id)
            if login:
                if "active" in update_data:
                    login.active = update_data["active"]
                if "computer_code" in update_data and update_data["computer_code"] is not None:
                    login.computer_code = str(update_data["computer_code"])
                db.add(login)
        
        # Update Addresses
        if payload.addresses is not None:
            # Delete existing
            existing_addrs = await student_address_repo.get_by_student(db, student_id)
            for addr in existing_addrs:
                await db.delete(addr)
            # Recreate
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
                
        # Update Guardians
        if payload.guardians is not None:
            existing_guards = await student_guardian_repo.get_multi(db, filters={"student_id": student_id})
            for guard in existing_guards:
                await db.delete(guard)
            for guard_in in payload.guardians:
                guard_data = guard_in.model_dump()
                guard_data["student_id"] = student_id
                await student_guardian_repo.create(db, obj_in=guard_data)
                
        # Update Qualifications
        if payload.qualifications is not None:
            existing_quals = await student_qualification_repo.get_multi(db, filters={"student_id": student_id})
            for qual in existing_quals:
                await db.delete(qual)
            for qual_in in payload.qualifications:
                qual_data = qual_in.model_dump()
                qual_data["student_id"] = student_id
                await student_qualification_repo.create(db, obj_in=qual_data)
                
        # Update Entrance Exams
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
        db.add(login)
        await refresh_token_repo.delete_by_user_id(db, login.id)
        await db.flush()

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

student_service = StudentService()

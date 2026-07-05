import asyncio
import os
import sys
from datetime import date

# Ensure stdout can handle utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import AsyncSessionLocal
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from app.models.academic import Institute, Department, Program, Specialization, AcademicSession, AcademicTerm, AcademicProgram
from app.models.staff import Designation, Staff, StaffDetails, StaffRole
from app.models.student import Student, StudentAddress, StudentAdmission, DocumentType, StudentDocument, StudentEntranceExam, StudentGuardian, StudentQualification
from app.models.system import Role, Permission, role_permissions
from app.models.auth import Login
from app.security.password import hash_password

async def get_or_create(session, model, defaults=None, **kwargs):
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalars().first()
    if instance:
        return instance, False
    
    params = dict((k, v) for k, v in kwargs.items())
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    await session.flush()
    return instance, True

async def seed_data():
    async with AsyncSessionLocal() as session:
        try:
            print("Starting database seeding...")
            
            # 1. Institute
            institute, _ = await get_or_create(session, Institute, name="IPS Academy")
            print("✓ Institute inserted")

            # 2. Departments
            dept_names = ["Computer Science", "Information Technology", "Mechanical", "Civil", "Electronics", "Management"]
            depts = {}
            for i, d in enumerate(dept_names):
                dept, _ = await get_or_create(
                    session, Department, 
                    defaults={"institue_id": institute.id, "dept_code": d[:3].upper(), "have_student": 1, "have_staff": 1, "active": 1}, 
                    name=d
                )
                depts[d] = dept
            print("✓ Departments inserted")

            # 3. Designations
            desig_names = ["Student", "Faculty", "HOD", "Principal", "Admin", "Accountant", "Librarian"]
            designations = {}
            for i, d in enumerate(desig_names):
                desig, _ = await get_or_create(session, Designation, defaults={"d_order": i+1, "active": 1}, designation=d)
                designations[d] = desig

            # 3.1 Legacy Designation Cleanup
            super_admin_desig = (await session.execute(select(Designation).filter_by(designation="Super Admin"))).scalars().first()
            if super_admin_desig:
                admin_desig = designations.get("Admin")
                if admin_desig:
                    await session.execute(
                        update(StaffDetails)
                        .where(StaffDetails.designation_id == super_admin_desig.id)
                        .values(designation_id=admin_desig.id)
                    )
                await session.execute(delete(Designation).where(Designation.id == super_admin_desig.id))
                await session.flush()
                print("✓ Legacy 'Super Admin' designation migrated and removed")

            # 4. Academic Session
            session_rec, _ = await get_or_create(session, AcademicSession, defaults={"start_date": date(2025, 7, 1), "end_date": date(2026, 6, 30), "is_active": True}, session_name="2025-26")

            # 5. Academic Terms
            term1, _ = await get_or_create(session, AcademicTerm, defaults={"start_date": date(2025, 7, 1), "end_date": date(2025, 12, 31)}, term_name="Semester 1", academic_session_id=session_rec.id)
            term2, _ = await get_or_create(session, AcademicTerm, defaults={"start_date": date(2026, 1, 1), "end_date": date(2026, 6, 30)}, term_name="Semester 2", academic_session_id=session_rec.id)

            # 6. Programs
            prog_names = ["B.Tech", "MBA", "MCA", "BCA"]
            programs = {}
            for p in prog_names:
                prog, _ = await get_or_create(session, Program, defaults={"program_code": p.upper().replace(".", ""), "active": 1}, name=p)
                programs[p] = prog
            print("✓ Programs inserted")

            # 7. Specializations
            spec_names = ["Computer Science", "AI & ML", "Data Science", "Cyber Security"]
            for s in spec_names:
                await get_or_create(session, Specialization, defaults={"program_id": programs["B.Tech"].id, "department_id": depts["Computer Science"].id, "specialization_code": "".join([word[0] for word in s.split()]), "active": 1}, name=s)
                
            # 8. Permissions
            crud_entities = [
                "student", "staff", "department", "role", "course",
                "institute", "program", "specialization", "academic_program",
                "academic_session", "academic_term", "designation", "staff_details",
                "staff_role", "student_address", "student_admission", "document_type",
                "student_document", "student_entrance_exam", "student_guardian",
                "student_qualification", "permission", "impersonation_log", "role_permission"
            ]
            
            crud_perms = []
            for entity in crud_entities:
                crud_perms.extend([f"{entity}.create", f"{entity}.read", f"{entity}.update", f"{entity}.delete"])
                
            custom_perms = [
                "attendance.manage", "fees.manage", "library.manage", "exam.manage", 
                "dashboard.read", "user.impersonate", "search.execute"
            ]
            
            all_perms = crud_perms + custom_perms
            
            db_perms = {}
            for p in all_perms:
                perm, _ = await get_or_create(session, Permission, defaults={"description": f"Permission for {p}", "active": True}, permission_name=p)
                db_perms[p] = perm
            print(f"✓ {len(all_perms)} Permissions inserted")

            # 9. Roles
            # Remove legacy "Super Admin" role and "999001" user if they exist
            await session.execute(delete(Login).where(Login.computer_code == 999001))
            await session.execute(delete(Staff).where(Staff.computer_code == 999001))
            await session.execute(delete(Role).where(Role.role_type == "Super Admin"))
            await session.flush()

            roles_data = {
                "Admin": all_perms,
                "Principal": ["student.read", "staff.read", "dashboard.read"],
                "HOD": ["student.read", "staff.read", "attendance.manage", "exam.manage", "dashboard.read"],
                "Faculty": ["student.read", "attendance.manage", "exam.manage", "dashboard.read"],
                "Accountant": ["fees.manage", "dashboard.read"],
                "Librarian": ["library.manage", "dashboard.read"],
                "Student": ["dashboard.read"],
                "Parent": ["dashboard.read"]
            }
            db_roles = {}
            for r_name, r_perms in roles_data.items():
                result = await session.execute(select(Role).filter_by(role_type=r_name))
                role = result.scalars().first()
                if not role:
                    role = Role(role_type=r_name, active=True)
                    session.add(role)
                    await session.flush()
                
                # Fetch existing permissions to avoid deletion and preserve manual grants
                existing_rp = await session.execute(
                    select(role_permissions.c.permission_id).where(role_permissions.c.role_id == role.id)
                )
                existing_perm_ids = {row[0] for row in existing_rp.fetchall()}
                
                # Only insert missing mappings
                for p in r_perms:
                    perm_id = db_perms[p].id
                    if perm_id not in existing_perm_ids:
                        await session.execute(role_permissions.insert().values(role_id=role.id, permission_id=perm_id))
                db_roles[r_name] = role
            await session.flush()
            print("✓ Roles inserted")

            # 10. Staff
            staff_data = [
                {"code": 10001, "fname": "Admin", "lname": "User", "role": "Admin", "dept": "Management", "dob": date(1985, 4, 20)},
                {"code": 11001, "fname": "Principal", "lname": "User", "role": "Principal", "dept": "Management", "dob": date(1975, 8, 10)},
                {"code": 11002, "fname": "HOD", "lname": "CSE", "role": "HOD", "dept": "Computer Science", "dob": date(1982, 11, 5)},
                {"code": 11003, "fname": "Faculty", "lname": "CSE", "role": "Faculty", "dept": "Computer Science", "dob": date(1990, 2, 28)},
                {"code": 12001, "fname": "Account", "lname": "User", "role": "Accountant", "dept": "Management", "dob": date(1988, 7, 22)},
                {"code": 13001, "fname": "Library", "lname": "User", "role": "Librarian", "dept": "Management", "dob": date(1992, 12, 12)},
            ]
            
            for i, s in enumerate(staff_data):
                staff, created = await get_or_create(session, Staff, defaults={
                    "title": "Mr.", "first_name": s["fname"], "last_name": s["lname"],
                    "date_of_birth": s["dob"],
                    "mobile1": f"900000000{i}", "abc_id": f"ABC{i}", "aadhar_number": 1000000000 + i,
                    "permanent_address": "Campus", "city": 1, "date_join": date(2025, 1, 1), "active": True
                }, computer_code=s["code"])
                
                # Update DOB if already existed (for consistency)
                if not created and not staff.date_of_birth:
                    staff.date_of_birth = s["dob"]
                    session.add(staff)
                
                if created:
                    staff_role = StaffRole(staff_id=staff.id, role_id=db_roles[s["role"]].id, department_id=depts[s["dept"]].id)
                    session.add(staff_role)
                    
                    dob_pass = s["dob"].strftime("%d%m%Y")
                    login = Login(computer_code=s["code"], password_hash=hash_password(dob_pass), staff_id=staff.id, active=True, is_first_login=True)
                    session.add(login)
                else:
                    # update login if already exists
                    res_login = await session.execute(select(Login).filter_by(computer_code=s["code"]))
                    login_rec = res_login.scalars().first()
                    dob_pass = s["dob"].strftime("%d%m%Y")
                    if not login_rec:
                        login = Login(computer_code=s["code"], password_hash=hash_password(dob_pass), staff_id=staff.id, active=True, is_first_login=True)
                        session.add(login)
                    else:
                        login_rec.password_hash = hash_password(dob_pass)
                        login_rec.is_first_login = True
                        session.add(login_rec)
            await session.flush()
            print("✓ Staff inserted")
            
            # Clean up old generic employee codes and orphaned logins
            old_codes = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 2025002]
            await session.execute(delete(Login).where(Login.computer_code.in_(old_codes)))
            await session.execute(delete(Login).where((Login.student_id == None) & (Login.staff_id == None)))
            await session.flush()

            # 12. Student
            student_dob = date(2005, 8, 15)
            student, created = await get_or_create(session, Student, defaults={
                "first_name": "Student", "last_name": "One",
                "gender": "M", "date_of_birth": student_dob, "mobile": "9876543210",
                "email": "student001@college.edu", "aadhar_no": "123456789012", "active": True
            }, computer_code=2025001, enrollment_no="2025CS001")
            
            if not created and not student.date_of_birth:
                student.date_of_birth = student_dob
                session.add(student)
            
            if created:
                session.add(StudentAddress(student_id=student.id, address_type="permanent", address_line="123 Student St", district="Indore", state="MP", pincode="452001"))
                session.add(StudentGuardian(student_id=student.id, relation="father", name="Parent One", mobile="9876543211"))
                session.add(StudentQualification(student_id=student.id, qualification_type="12th", board_university="CBSE", passing_year=2024, percentage=85.0))
                
                ap, _ = await get_or_create(session, AcademicProgram, defaults={"specialization_id": None, "duration_years": 4, "total_semesters": 8, "entry_semester": 1}, department_id=depts["Computer Science"].id, program_id=programs["B.Tech"].id)
                
                session.add(StudentAdmission(student_id=student.id, academic_program_id=ap.id, academic_session_id=session_rec.id, admission_date=date(2025, 7, 10), admission_type="regular"))
                session.add(StudentEntranceExam(student_id=student.id, exam_name="JEE Main", roll_no="JM2025001", score=120, percentile=90.5))
                
                doc_type, _ = await get_or_create(session, DocumentType, defaults={"required": True, "active": True}, name="12th Marksheet")
                session.add(StudentDocument(student_id=student.id, document_type_id=doc_type.id, submitted=True, verified=True))
                
                dob_pass = student_dob.strftime("%d%m%Y")
                session.add(Login(computer_code=2025001, password_hash=hash_password(dob_pass), student_id=student.id, active=True, is_first_login=True))
            else:
                res_login = await session.execute(select(Login).filter_by(computer_code=2025001))
                login_rec = res_login.scalars().first()
                dob_pass = student_dob.strftime("%d%m%Y")
                if not login_rec:
                    session.add(Login(computer_code=2025001, password_hash=hash_password(dob_pass), student_id=student.id, active=True, is_first_login=True))
                else:
                    login_rec.password_hash = hash_password(dob_pass)
                    login_rec.is_first_login = True
                    session.add(login_rec)
            
            await session.flush()
            print("✓ Student inserted")
            print("✓ Login accounts inserted")

            await session.commit()
            print("✓ Seed completed successfully\n")
            
            # --- VERIFICATION ---
            print("=== VERIFICATION TABLE ===")
            print(f"{'Login ID':<10} | {'Username':<15} | {'Role':<15} | {'User ID':<10} | {'DOB':<12} | {'First Login'}")
            print("-" * 80)
            
            logins = (await session.execute(select(Login))).scalars().all()
            for l in logins:
                role = "Unknown"
                uid = "N/A"
                dob_str = "NULL"
                
                if l.student_id:
                    uid = f"STU-{l.student_id}"
                    role = "Student"
                    stu = (await session.execute(select(Student).filter_by(id=l.student_id))).scalars().first()
                    if stu and stu.date_of_birth:
                        dob_str = stu.date_of_birth.strftime("%Y-%m-%d")
                elif l.staff_id:
                    uid = f"STF-{l.staff_id}"
                    stf = (await session.execute(select(Staff).filter_by(id=l.staff_id))).scalars().first()
                    if stf and stf.date_of_birth:
                        dob_str = stf.date_of_birth.strftime("%Y-%m-%d")
                    # get role
                    sr = (await session.execute(select(StaffRole).options(selectinload(StaffRole.role)).filter_by(staff_id=l.staff_id))).scalars().first()
                    if sr and sr.role:
                        role = sr.role.role_type
                
                print(f"{l.id:<10} | {l.computer_code:<15} | {role:<15} | {uid:<10} | {dob_str:<12} | {l.is_first_login}")
                
                # Assertions
                assert dob_str != "NULL", f"User {l.computer_code} has NULL date_of_birth"
                assert l.is_first_login is True, f"User {l.computer_code} is_first_login is not True"
                assert (l.student_id is not None) or (l.staff_id is not None), f"Orphaned login found: {l.computer_code}"
            
            print("===========================")
            
            # --- STAFF DETAILS MIGRATION ---
            print("Running StaffDetails idempotent migration...")
            
            # Fetch designations to create a map
            res_desig = await session.execute(select(Designation))
            designations_list = res_desig.scalars().all()
            desig_map = {d.designation.lower(): d.id for d in designations_list}

            # Fetch roles to create a map
            res_roles = await session.execute(select(Role))
            roles_list = res_roles.scalars().all()
            role_map = {r.id: r.role_type.lower() for r in roles_list}

            all_staff = (await session.execute(select(Staff))).scalars().all()
            for staff_member in all_staff:
                # Query staff_details
                res_details = await session.execute(select(StaffDetails).where(StaffDetails.staff_id == staff_member.id))
                details = res_details.scalar()
                
                # Fetch primary role
                res_role = await session.execute(select(StaffRole).where(StaffRole.staff_id == staff_member.id).limit(1))
                staff_role = res_role.scalar()

                if not details:
                    details = StaffDetails(staff_id=staff_member.id)
                    session.add(details)
                    await session.flush()
                
                if staff_role:
                    if staff_role.department_id and not details.dept_id:
                        details.dept_id = staff_role.department_id
                    if not details.designation_id:
                        role_type = role_map.get(staff_role.role_id)
                        if role_type:
                            desig_id = desig_map.get(role_type)
                            if desig_id:
                                details.designation_id = desig_id
                session.add(details)
            await session.flush()
            print("✓ StaffDetails migrated and updated successfully.")
            
            # --- FINAL VERIFICATION ---
            super_admin_count = (await session.execute(select(Role).filter_by(role_type="Super Admin"))).scalars().all()
            assert len(super_admin_count) == 0, "Super Admin role should not exist"
            
            super_admin_desig_count = (await session.execute(select(Designation).filter_by(designation="Super Admin"))).scalars().all()
            assert len(super_admin_desig_count) == 0, "Super Admin designation should not exist"
            
            super001_staff_count = (await session.execute(select(Staff).filter_by(computer_code=999001))).scalars().all()
            assert len(super001_staff_count) == 0, "SUPER001 staff should not exist"
            
            super001_login_count = (await session.execute(select(Login).filter_by(computer_code=999001))).scalars().all()
            assert len(super001_login_count) == 0, "SUPER001 login should not exist"
            
            print("Legacy cleanup verification passed.")
            
            # Output the required SQL query results
            from sqlalchemy import text
            print("\n--- REQUIRED SQL VERIFICATION OUTPUT ---")
            
            res1 = await session.execute(text("SELECT * FROM roles WHERE role_type='Super Admin'"))
            print("SELECT * FROM roles WHERE role_type='Super Admin'; ->", res1.fetchall())

            res1_d = await session.execute(text("SELECT * FROM designation WHERE designation='Super Admin'"))
            print("SELECT * FROM designation WHERE designation='Super Admin'; ->", res1_d.fetchall())
            
            res2 = await session.execute(text("SELECT * FROM staff WHERE computer_code=999001"))
            print("SELECT * FROM staff WHERE computer_code=999001; ->", res2.fetchall())
            
            res3 = await session.execute(text("SELECT * FROM login WHERE computer_code=999001"))
            print("SELECT * FROM login WHERE computer_code=999001; ->", res3.fetchall())
            
            res4 = await session.execute(text('''
                SELECT staff.computer_code, roles.role_type
                FROM staff
                JOIN staff_role ON staff.id = staff_role.staff_id
                JOIN roles ON roles.id = staff_role.role_id
                WHERE roles.role_type = 'Admin';
            '''))
            print("Admin Role Mappings:")
            for row in res4.fetchall():
                print(f" - {row[0]}: {row[1]}")
                
            res5 = await session.execute(text("SELECT COUNT(*) FROM staff"))
            res6 = await session.execute(text("SELECT COUNT(*) FROM staff_details"))
            staff_count = res5.scalar()
            details_count = res6.scalar()
            print(f"Total Staff records: {staff_count}, Total StaffDetails records: {details_count}")
            assert staff_count == details_count, f"Mismatch: {staff_count} staff vs {details_count} staff_details"
            
            print("All verification checks passed.")

            await session.commit()
            print("✓ Seed completed successfully")

        except Exception as e:
            await session.rollback()
            print(f"Seeding failed, transaction rolled back. Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_data())

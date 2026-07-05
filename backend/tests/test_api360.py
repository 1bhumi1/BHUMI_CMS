import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.academic import AcademicSession
from app.models.staff import Staff
from app.models.auth import Login
from app.security.password import hash_password

@pytest.mark.asyncio
async def test_api360_crud(client: AsyncClient, db_session: AsyncSession):
    # 1. Seed AcademicSession, Staff, and Login in test DB
    session_obj = AcademicSession(
        id=9,
        session_name="2026-27",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 7, 1),
        is_active=True
    )
    staff_obj = Staff(
        id=2,
        computer_code=11003,
        title="Dr.",
        first_name="Test",
        last_name="Faculty",
        mobile1="9999999999",
        abc_id="ABC999",
        aadhar_number=999999999999,
        permanent_address="Test Address",
        city=1,
        date_join=date(2025, 1, 1),
        active=True
    )
    staff_login = Login(
        computer_code=11003,
        password_hash=hash_password("adminpass"),
        staff_id=2,
        active=True,
        is_first_login=False
    )
    db_session.add(session_obj)
    db_session.add(staff_obj)
    db_session.add(staff_login)
    await db_session.commit()

    # 2. Login as Admin
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    assert login_resp.status_code == 200
    admin_token = login_resp.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Login as Staff
    staff_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 11003, "password": "adminpass"}
    )
    assert staff_login_resp.status_code == 200
    staff_token = staff_login_resp.json()["data"]["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 4. Create record as Staff (even if they specify 10001, backend forces 11003)
    payload = {
        "faculty_computer_code": 10001,  # Try to manipulate
        "academic_session": 9,
        "submited": False,
        "hod_approval": True,            # Try to manipulate HOD approval
        "cr": {
            "cr1": 8, "cr2": 9, "cr3": 10, "cr4": 9, "cr5": 8,
            "cr6": 9, "cr7": 10, "cr8": 9, "cr9": 8, "cr10": 9
        },
        "cat1i": [
            {
                "sno": 1,
                "sas": "July-Dec 2026",
                "ccnc": "CS-101",
                "nsc": 40,
                "nahcof": 38,
                "nahcon": 2
            }
        ],
        "cat1ii": [],
        "cat1iii": [],
        "cat1iv": [],
        "cat1v": [],
        "cat2": [],
        "cat3": []
    }

    create_resp = await client.post(
        "/api/v1/api360/",
        json=payload,
        headers=staff_headers
    )
    assert create_resp.status_code == 201
    record_id = create_resp.json()["data"]["api_id"]
    
    # Verify backend enforced staff code and HOD approval was reset to False
    assert create_resp.json()["data"]["faculty_computer_code"] == 11003
    assert create_resp.json()["data"]["hod_approval"] is False

    # 5. Duplicate Check Prevention: Create again for same staff + session
    dup_payload = {
        "faculty_computer_code": 11003,
        "academic_session": 9,
        "submited": False,
        "hod_approval": False,
        "cr": {"cr1": 10, "cr2": 10, "cr3": 10, "cr4": 10, "cr5": 10, "cr6": 10, "cr7": 10, "cr8": 10, "cr9": 10, "cr10": 10},
        "cat1i": [], "cat1ii": [], "cat1iii": [], "cat1iv": [], "cat1v": [], "cat2": [], "cat3": []
    }
    dup_resp = await client.post(
        "/api/v1/api360/",
        json=dup_payload,
        headers=staff_headers
    )
    assert dup_resp.status_code == 201 or dup_resp.status_code == 200
    assert "already exists" in dup_resp.json()["message"]
    assert dup_resp.json()["data"]["api_id"] == record_id

    # 6. Create record for Admin as Admin
    admin_payload = {
        "faculty_computer_code": 10001,
        "academic_session": 9,
        "submited": False,
        "hod_approval": True,
        "cr": {"cr1": 10, "cr2": 10, "cr3": 10, "cr4": 10, "cr5": 10, "cr6": 10, "cr7": 10, "cr8": 10, "cr9": 10, "cr10": 10},
        "cat1i": [], "cat1ii": [], "cat1iii": [], "cat1iv": [], "cat1v": [], "cat2": [], "cat3": []
    }
    admin_create_resp = await client.post(
        "/api/v1/api360/",
        json=admin_payload,
        headers=admin_headers
    )
    assert admin_create_resp.status_code == 201
    admin_record_id = admin_create_resp.json()["data"]["api_id"]

    # 7. Staff tries to retrieve Admin's record (should fail)
    get_fail = await client.get(f"/api/v1/api360/{admin_record_id}", headers=staff_headers)
    assert get_fail.status_code == 403

    # 8. Staff tries to update Admin's record (should fail)
    put_fail = await client.put(
        f"/api/v1/api360/{admin_record_id}",
        json={"faculty_computer_code": 10001, "academic_session": 9},
        headers=staff_headers
    )
    assert put_fail.status_code == 403

    # 9. Staff tries to delete Admin's record (should fail)
    delete_fail = await client.delete(f"/api/v1/api360/{admin_record_id}", headers=staff_headers)
    assert delete_fail.status_code == 403

    # 9.5. Staff updates their own record (should pass)
    update_payload = {
        "faculty_computer_code": 11003,
        "academic_session": 9,
        "submited": False,
        "hod_approval": False,
        "cr": {
            "cr1": 7, "cr2": 7, "cr3": 7, "cr4": 7, "cr5": 7,
            "cr6": 7, "cr7": 7, "cr8": 7, "cr9": 7, "cr10": 7
        },
        "cat1i": [
            {
                "sno": 1,
                "sas": "July-Dec 2026",
                "ccnc": "CS-101 (Updated)",
                "nsc": 45,
                "nahcof": 40,
                "nahcon": 5
            }
        ],
        "cat1ii": [],
        "cat1iii": [],
        "cat1iv": [],
        "cat1v": [],
        "cat2": [],
        "cat3": []
    }
    update_resp = await client.put(
        f"/api/v1/api360/{record_id}",
        json=update_payload,
        headers=staff_headers
    )
    assert update_resp.status_code == 200, f"Update failed: {update_resp.json()}"
    assert update_resp.json()["data"]["cr"]["cr1"] == 7
    assert update_resp.json()["data"]["cat1i"][0]["ccnc"] == "CS-101 (Updated)"

    # 10. Delete owned record as Staff (should pass)
    delete_success = await client.delete(f"/api/v1/api360/{record_id}", headers=staff_headers)
    assert delete_success.status_code == 200


@pytest.mark.asyncio
async def test_hod_confidential_report_workflow(client: AsyncClient, db_session: AsyncSession):
    import json
    from app.models.academic import Department
    from app.models.staff import StaffRole, StaffDetails
    from app.models.system import Role
    from app.models.api360 import API360Info, API360Cat1i, API360Confidential

    # Seed HOD role and Faculty role (admin role is role id 2, student is 1, so HOD role id 3, Faculty role id 4)
    hod_role = Role(id=3, role_type="HOD", active=True)
    faculty_role = Role(id=4, role_type="Faculty", active=True)
    db_session.add_all([hod_role, faculty_role])
    await db_session.flush()

    # HOD staff
    hod_staff = Staff(
        id=3,
        computer_code="12001",
        title="Dr.",
        first_name="HOD",
        last_name="User",
        mobile1="9876543211",
        abc_id="ABCHOD",
        aadhar_number=123456789013,
        permanent_address="HOD street",
        city=1,
        date_join=date(2020, 1, 1),
        active=True
    )
    # Faculty staff
    fac_staff = Staff(
        id=4,
        computer_code="12002",
        title="Mr.",
        first_name="Faculty",
        last_name="User",
        mobile1="9876543212",
        abc_id="ABCFAC",
        aadhar_number=123456789014,
        permanent_address="Faculty street",
        city=1,
        date_join=date(2021, 1, 1),
        active=True
    )
    db_session.add_all([hod_staff, fac_staff])
    await db_session.flush()

    # StaffRoles
    hod_staff_role = StaffRole(id=2, staff_id=3, role_id=3, department_id=1) # role_id=3 is HOD role
    fac_staff_role = StaffRole(id=3, staff_id=4, role_id=4, department_id=1) # role_id=4 is Faculty role
    db_session.add_all([hod_staff_role, fac_staff_role])

    # StaffDetails
    hod_details = StaffDetails(id=1, staff_id=3, dept_id=1)
    fac_details = StaffDetails(id=2, staff_id=4, dept_id=1)
    db_session.add_all([hod_details, fac_details])

    # Logins
    hod_login = Login(
        id=3,
        computer_code=12001,
        password_hash=hash_password("hodpass"),
        staff_id=3,
        active=True
    )
    fac_login = Login(
        id=4,
        computer_code=12002,
        password_hash=hash_password("facpass"),
        staff_id=4,
        active=True
    )
    db_session.add_all([hod_login, fac_login])
    await db_session.flush()

    # 360 Feedback Master Record for Faculty
    appraisal = API360Info(
        api_id=20,
        faculty_computer_code=12002,
        academic_session=9,
        submited=True,
        hod_approval=False
    )
    db_session.add(appraisal)
    await db_session.flush()

    meta_val = {
        "status": "Under HOD Review",
        "hod_remarks": "",
        "submitted_at": "",
        "last_modified": ""
    }
    meta_row = API360Cat1i(
        api_id=20,
        sno=-999,
        sas='METADATA',
        ccnc=json.dumps(meta_val),
        nsc=0, nahcof=0, nahcon=0
    )
    db_session.add(meta_row)
    await db_session.commit()

    # Login as HOD
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 12001, "password": "hodpass"}
    )
    assert login_resp.status_code == 200
    hod_token = login_resp.json()["data"]["access_token"]
    hod_headers = {"Authorization": f"Bearer {hod_token}"}

    # HOD fills and submits Confidential Report
    payload = {
        "faculty_feedback_id": 20,
        "parameter_1": 8,
        "parameter_2": 9,
        "parameter_3": 7,
        "parameter_4": 10,
        "parameter_5": 8,
        "parameter_6": 9,
        "parameter_7": 9,
        "remarks": "Excellent faculty performance",
        "status": "Submitted"
    }

    cr_resp = await client.post(
        "/api/v1/api360/confidential",
        json=payload,
        headers=hod_headers
    )
    assert cr_resp.status_code == 201
    
    # Verify response
    resp_data = cr_resp.json()["data"]
    assert resp_data["status"] == "Submitted"
    assert resp_data["total_marks"] == 60 # 8+9+7+10+8+9+9 = 60
    assert resp_data["remarks"] == "Excellent faculty performance"

    # Verify that the appraisal's metadata status is now "Confidential Report Submitted"
    from sqlalchemy import select
    appr_stmt = select(API360Cat1i).where(API360Cat1i.api_id == 20, API360Cat1i.sno == -999)
    res = await db_session.execute(appr_stmt)
    updated_meta = res.scalar_one()
    meta_dict = json.loads(updated_meta.ccnc)
    assert meta_dict["status"] == "Confidential Report Submitted"

    # Simulate HOD editing the Confidential Report after submission
    edit_payload = {
        "faculty_feedback_id": 20,
        "parameter_1": 10,  # Changed from 8 to 10
        "parameter_2": 9,
        "parameter_3": 7,
        "parameter_4": 10,
        "parameter_5": 8,
        "parameter_6": 9,
        "parameter_7": 9,
        "remarks": "Superb faculty performance",
        "status": "Submitted"
    }

    edit_resp = await client.post(
        "/api/v1/api360/confidential",
        json=edit_payload,
        headers=hod_headers
    )
    assert edit_resp.status_code == 201
    edit_data = edit_resp.json()["data"]
    assert edit_data["status"] == "Submitted"
    assert edit_data["total_marks"] == 62 # 10+9+7+10+8+9+9 = 62
    assert edit_data["remarks"] == "Superb faculty performance"


@pytest.mark.asyncio
async def test_hod_cannot_access_faculty_drafts(client: AsyncClient, db_session: AsyncSession):
    import json
    from app.models.academic import Department
    from app.models.staff import StaffRole, StaffDetails
    from app.models.system import Role
    from app.models.api360 import API360Info, API360Cat1i, API360Confidential

    # Seed HOD role and Faculty role (admin role is role id 2, student is 1, so HOD role id 3, Faculty role id 4)
    hod_role = Role(id=3, role_type="HOD", active=True)
    faculty_role = Role(id=4, role_type="Faculty", active=True)
    db_session.add_all([hod_role, faculty_role])
    await db_session.flush()

    # HOD staff
    hod_staff = Staff(
        id=3,
        computer_code="12001",
        title="Dr.",
        first_name="HOD",
        last_name="User",
        mobile1="9876543211",
        abc_id="ABCHOD",
        aadhar_number=123456789013,
        permanent_address="HOD street",
        city=1,
        date_join=date(2020, 1, 1),
        active=True
    )
    # Faculty staff
    fac_staff = Staff(
        id=4,
        computer_code="12002",
        title="Mr.",
        first_name="Faculty",
        last_name="User",
        mobile1="9876543212",
        abc_id="ABCFAC",
        aadhar_number=123456789014,
        permanent_address="Faculty street",
        city=1,
        date_join=date(2021, 1, 1),
        active=True
    )
    db_session.add_all([hod_staff, fac_staff])
    await db_session.flush()

    # StaffRoles
    hod_staff_role = StaffRole(id=2, staff_id=3, role_id=3, department_id=1) # role_id=3 is HOD role
    fac_staff_role = StaffRole(id=3, staff_id=4, role_id=4, department_id=1) # role_id=4 is Faculty role
    db_session.add_all([hod_staff_role, fac_staff_role])

    # StaffDetails
    hod_details = StaffDetails(id=1, staff_id=3, dept_id=1)
    fac_details = StaffDetails(id=2, staff_id=4, dept_id=1)
    db_session.add_all([hod_details, fac_details])

    # Logins
    hod_login = Login(
        id=3,
        computer_code=12001,
        password_hash=hash_password("hodpass"),
        staff_id=3,
        active=True
    )
    fac_login = Login(
        id=4,
        computer_code=12002,
        password_hash=hash_password("facpass"),
        staff_id=4,
        active=True
    )
    db_session.add_all([hod_login, fac_login])
    await db_session.flush()

    # 360 Feedback Master Record for Faculty - submited = False (Draft)
    appraisal = API360Info(
        api_id=20,
        faculty_computer_code=12002,
        academic_session=9,
        submited=False, # DRAFT
        hod_approval=False
    )
    db_session.add(appraisal)
    await db_session.commit()

    # Login as HOD
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 12001, "password": "hodpass"}
    )
    assert login_resp.status_code == 200
    hod_token = login_resp.json()["data"]["access_token"]
    hod_headers = {"Authorization": f"Bearer {hod_token}"}

    # 1. HOD list endpoint should not return this record
    list_resp = await client.get("/api/v1/api360/", headers=hod_headers)
    assert list_resp.status_code == 200
    records = list_resp.json()["data"]["items"]
    # Verify our draft record ID 20 is not in the list
    assert not any(r["api_id"] == 20 for r in records)

    # 2. HOD get single record endpoint should return 403 Forbidden for draft
    get_resp = await client.get("/api/v1/api360/20", headers=hod_headers)
    assert get_resp.status_code == 403

    # 3. HOD update endpoint should return 403 Forbidden for draft
    update_resp = await client.put(
        "/api/v1/api360/20",
        json={"academic_session": 9},
        headers=hod_headers
    )
    assert update_resp.status_code == 403

    # 4. HOD delete endpoint should return 403 Forbidden for draft
    delete_resp = await client.delete("/api/v1/api360/20", headers=hod_headers)
    assert delete_resp.status_code == 403

    # 5. HOD confidential get/save endpoints should return 403 Forbidden for draft
    conf_get_resp = await client.get("/api/v1/api360/confidential/20", headers=hod_headers)
    assert conf_get_resp.status_code == 403

    conf_save_resp = await client.post(
        "/api/v1/api360/confidential",
        json={
            "faculty_feedback_id": 20,
            "parameter_1": 8, "parameter_2": 8, "parameter_3": 8,
            "parameter_4": 8, "parameter_5": 8, "parameter_6": 8, "parameter_7": 8,
            "remarks": "should fail", "status": "Submitted"
        },
        headers=hod_headers
    )
    assert conf_save_resp.status_code == 403




import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_access_granted_with_permission(client: AsyncClient):
    """
    Admin user has 'student.read' and 'search.execute' permissions, and should be granted access.
    """
    # 1. Login as Admin
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Access restricted search endpoint
    search_resp = await client.get("/api/v1/search/global?q=Student", headers=headers)
    assert search_resp.status_code == 200
    assert search_resp.json()["success"] is True

@pytest.mark.asyncio
async def test_access_denied_without_permission(client: AsyncClient):
    """
    Student user has 'student.read' but NOT 'student.create' permission,
    and should be blocked from student admission.
    """
    # 1. Login as Student
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 20001, "password": "studentpass"}
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Try to hit student admission creation endpoint (requires student.create)
    payload = {
        "student": {
            "first_name": "New",
            "last_name": "Student",
            "gender": "M",
            "date_of_birth": "2005-01-01",
            "aadhar_no": "999999999999",
            "mobile": "9999999999",
            "email": "newstudent@college.edu"
        },
        "addresses": [],
        "admission": {
            "academic_program_id": 1,
            "academic_session_id": 1,
            "admission_date": "2026-06-01",
            "admission_type": "regular",
            "entry_semester": 1,
            "status": "active"
        },
        "guardians": [],
        "qualifications": [],
        "entrance_exams": []
    }

    create_resp = await client.post("/api/v1/students/", json=payload, headers=headers)
    assert create_resp.status_code == 403
    assert create_resp.json()["success"] is False
    assert "Permission denied" in create_resp.json()["message"]

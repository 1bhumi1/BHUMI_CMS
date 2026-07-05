import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_student_lifecycle(client: AsyncClient):
    """
    Test student registration, read, update, and deactivation lifecycle.
    """
    # 1. Login as Admin
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Admission (Create Student)
    admission_payload = {
        "student": {
            "computer_code": 20002,
            "first_name": "Alice",
            "last_name": "Smith",
            "gender": "F",
            "date_of_birth": "2006-05-15",
            "aadhar_no": "987654321098",
            "mobile": "9876543210",
            "email": "alice@college.edu",
            "blood_group": "O+",
            "category": "General",
            "religion": "Christianity"
        },
        "addresses": [
            {
                "address_type": "permanent",
                "address_line": "123 Cherry Street",
                "district": "Indore",
                "state": "MP",
                "pincode": "452001"
            }
        ],
        "admission": {
            "academic_program_id": 1,
            "academic_session_id": 1,
            "admission_date": "2026-06-01",
            "admission_type": "regular",
            "entry_semester": 1,
            "status": "active"
        },
        "guardians": [
            {
                "relation": "father",
                "name": "John Smith",
                "mobile": "9876543211",
                "occupation": "Engineer"
            }
        ],
        "qualifications": [
            {
                "qualification_type": "10th",
                "board_university": "CBSE",
                "passing_year": 2022,
                "percentage": 92.5
            }
        ],
        "entrance_exams": []
    }

    create_resp = await client.post("/api/v1/students/", json=admission_payload, headers=headers)
    assert create_resp.status_code == 201
    res_data = create_resp.json()
    assert res_data["success"] is True
    student_id = res_data["data"]["student"]["id"]
    computer_code = res_data["data"]["student"]["computer_code"]

    # 3. Read profile
    read_resp = await client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert read_resp.status_code == 200
    profile = read_resp.json()["data"]
    assert profile["student"]["first_name"] == "Alice"
    assert len(profile["addresses"]) == 1
    assert profile["admission"]["admission_type"] == "regular"
    assert len(profile["guardians"]) == 1
    assert len(profile["qualifications"]) == 1

    # 4. Update student
    update_resp = await client.put(
        f"/api/v1/students/{student_id}",
        json={"student": {"first_name": "Alicia", "blood_group": "A-"}},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["first_name"] == "Alicia"
    assert update_resp.json()["data"]["blood_group"] == "A-"

    # 5. Soft Delete
    delete_resp = await client.delete(f"/api/v1/students/{student_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # Check updated status (should be active = False)
    check_resp = await client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert check_resp.status_code == 200
    assert check_resp.json()["data"]["student"]["active"] is False

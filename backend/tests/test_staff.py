import pytest
from httpx import AsyncClient


async def admin_login(client: AsyncClient) -> dict:
    """Helper to login as admin and return auth headers."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "10001", "password": "adminpass"}
    )
    token = login_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def student_login(client: AsyncClient) -> dict:
    """Helper to login as student and return auth headers."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "20001", "password": "studentpass"}
    )
    token = login_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_staff_crud_lifecycle(client: AsyncClient):
    """
    Test staff registration, read (single + list), update, and soft-delete lifecycle.
    """
    headers = await admin_login(client)

    # 1. Create Staff
    create_payload = {
        "staff": {
            "computer_code": "50001",
            "title": "Dr.",
            "first_name": "Jane",
            "middle_name": "M",
            "last_name": "Doe",
            "date_of_birth": "1985-03-15",
            "gender": "F",
            "mobile1": "9876500001",
            "email": "jane.doe@college.edu",
            "abc_id": "ABC50001",
            "aadhar_number": 111122223333,
            "permanent_address": "456 Faculty Lane",
            "city": 1,
            "date_join": "2024-01-15",
            "role_id": 2,
            "department_id": 1
        },
        "details": {
            "dept_id": 1,
            "designation_id": 1,
            "qualification": "Ph.D",
            "experience_years": 5.5,
            "bank_name": "SBI",
            "account_number": "12345678901234",
            "ifsc": "SBIN0001234"
        },
        "roles": [
            {
                "staff_id": 0,
                "role_id": 2,
                "department_id": 1
            }
        ]
    }
    create_resp = await client.post("/api/v1/staff/", json=create_payload, headers=headers)
    assert create_resp.status_code == 201, f"Create failed: {create_resp.json()}"
    res_data = create_resp.json()
    assert res_data["success"] is True
    staff_id = res_data["data"]["staff"]["id"]
    assert res_data["data"]["staff"]["computer_code"] == 50001
    assert res_data["data"]["staff"]["first_name"] == "Jane"

    # 2. Read single staff profile
    read_resp = await client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert read_resp.status_code == 200
    profile = read_resp.json()["data"]
    assert profile["staff"]["first_name"] == "Jane"
    assert profile["staff"]["email"] == "jane.doe@college.edu"

    # 3. List staff (paginated)
    list_resp = await client.get("/api/v1/staff/?limit=10", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()["data"]
    assert "items" in list_data
    assert "total" in list_data
    assert list_data["total"] >= 1
    names = [s["first_name"] for s in list_data["items"]]
    assert "Jane" in names

    # 4. Update staff
    update_resp = await client.put(
        f"/api/v1/staff/{staff_id}",
        json={"first_name": "Janet", "title": "Prof."},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["first_name"] == "Janet"
    assert update_resp.json()["data"]["title"] == "Prof."

    # 5. Soft Delete
    delete_resp = await client.delete(f"/api/v1/staff/{staff_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # 6. Verify soft-deleted (active = False)
    check_resp = await client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert check_resp.status_code == 200
    assert check_resp.json()["data"]["staff"]["active"] is False


@pytest.mark.asyncio
async def test_staff_search(client: AsyncClient):
    """
    Test search functionality on the staff list endpoint.
    """
    headers = await admin_login(client)

    # Create a staff member with a distinctive name
    create_payload = {
        "staff": {
            "computer_code": "50010",
            "first_name": "Rajesh",
            "last_name": "Koothrappali",
            "mobile1": "9876500010",
            "email": "rajesh@college.edu",
            "abc_id": "ABC50010",
            "aadhar_number": 222233334444,
            "permanent_address": "789 Search Test Ave",
            "city": 1,
            "date_join": "2024-06-01",
            "role_id": 2,
            "department_id": 1
        },
        "roles": []
    }
    await client.post("/api/v1/staff/", json=create_payload, headers=headers)

    # Search by first name
    search_resp = await client.get("/api/v1/staff/?search=Rajesh", headers=headers)
    assert search_resp.status_code == 200
    items = search_resp.json()["data"]["items"]
    assert any(s["first_name"] == "Rajesh" for s in items)

    # Search by last name
    search_resp2 = await client.get("/api/v1/staff/?search=Koothrappali", headers=headers)
    assert search_resp2.status_code == 200
    assert search_resp2.json()["data"]["total"] >= 1

    # Search with no results
    search_resp3 = await client.get("/api/v1/staff/?search=ZZZNonExistent", headers=headers)
    assert search_resp3.status_code == 200
    assert search_resp3.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_staff_not_found(client: AsyncClient):
    """
    Test 404 for non-existent staff.
    """
    headers = await admin_login(client)
    resp = await client.get("/api/v1/staff/999999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_staff_duplicate_computer_code(client: AsyncClient):
    """
    Test that creating staff with a duplicate computer code returns 400.
    """
    headers = await admin_login(client)

    payload = {
        "staff": {
            "computer_code": "50020",
            "first_name": "Duplicate",
            "last_name": "Test",
            "mobile1": "9876500020",
            "abc_id": "ABC50020",
            "aadhar_number": 333344445555,
            "permanent_address": "Dup Test Lane",
            "city": 1,
            "date_join": "2024-01-01",
            "role_id": 2,
            "department_id": 1
        },
        "roles": []
    }
    # First creation should succeed
    resp1 = await client.post("/api/v1/staff/", json=payload, headers=headers)
    assert resp1.status_code == 201

    # Second creation with same code should fail
    payload["staff"]["aadhar_number"] = 333344445556
    resp2 = await client.post("/api/v1/staff/", json=payload, headers=headers)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_staff_duplicate_aadhar(client: AsyncClient):
    """
    Test that creating staff with a duplicate aadhar returns 409.
    """
    headers = await admin_login(client)

    payload1 = {
        "staff": {
            "computer_code": "50030",
            "first_name": "Aadhar",
            "last_name": "Test1",
            "mobile1": "9876500030",
            "abc_id": "ABC50030",
            "aadhar_number": 444455556666,
            "permanent_address": "Aadhar Test Lane",
            "city": 1,
            "date_join": "2024-01-01",
            "role_id": 2,
            "department_id": 1
        },
        "roles": []
    }
    resp1 = await client.post("/api/v1/staff/", json=payload1, headers=headers)
    assert resp1.status_code == 201

    # Same aadhar, different code
    payload2 = {
        "staff": {
            "computer_code": "50031",
            "first_name": "Aadhar",
            "last_name": "Test2",
            "mobile1": "9876500031",
            "abc_id": "ABC50031",
            "aadhar_number": 444455556666,
            "permanent_address": "Aadhar Test Lane 2",
            "city": 1,
            "date_join": "2024-01-01",
            "role_id": 2,
            "department_id": 1
        },
        "roles": []
    }
    resp2 = await client.post("/api/v1/staff/", json=payload2, headers=headers)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_staff_validation_failure(client: AsyncClient):
    """
    Test that invalid aadhar (not 12 digits) returns 422.
    """
    headers = await admin_login(client)

    payload = {
        "staff": {
            "computer_code": "50040",
            "first_name": "Invalid",
            "last_name": "Aadhar",
            "mobile1": "9876500040",
            "abc_id": "ABC50040",
            "aadhar_number": 12345,
            "permanent_address": "Invalid Test Lane",
            "city": 1,
            "date_join": "2024-01-01",
            "role_id": 2,
            "department_id": 1
        },
        "roles": []
    }
    resp = await client.post("/api/v1/staff/", json=payload, headers=headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_staff_permission_denied(client: AsyncClient):
    """
    Test that student user cannot access staff CRUD endpoints.
    """
    headers = await student_login(client)

    # Student should not have staff.read permission
    resp = await client.get("/api/v1/staff/", headers=headers)
    assert resp.status_code == 403

    # Student should not have staff.create permission
    resp2 = await client.post("/api/v1/staff/", json={"staff": {}, "roles": []}, headers=headers)
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_staff_pagination(client: AsyncClient):
    """
    Test pagination parameters on staff list.
    """
    headers = await admin_login(client)

    # Create 3 additional staff members
    for i in range(3):
        payload = {
            "staff": {
                "computer_code": f"6000{i}",
                "first_name": f"Page{i}",
                "last_name": "Test",
                "mobile1": f"987650100{i}",
                "abc_id": f"ABCP{i}",
                "aadhar_number": int(f"55556666777{i}"),
                "permanent_address": f"Page Test Lane {i}",
                "city": 1,
                "date_join": "2024-01-01",
                "role_id": 2,
                "department_id": 1
            },
            "roles": []
        }
        await client.post("/api/v1/staff/", json=payload, headers=headers)

    # Fetch page 1 with limit 2
    page1 = await client.get("/api/v1/staff/?skip=0&limit=2", headers=headers)
    assert page1.status_code == 200
    data1 = page1.json()["data"]
    assert len(data1["items"]) <= 2
    assert data1["total"] >= 3
    assert data1["skip"] == 0
    assert data1["limit"] == 2

    # Fetch page 2
    page2 = await client.get("/api/v1/staff/?skip=2&limit=2", headers=headers)
    assert page2.status_code == 200
    data2 = page2.json()["data"]
    assert len(data2["items"]) <= 2

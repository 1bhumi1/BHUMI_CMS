import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.auth import Login, RefreshToken

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """
    Test login with valid computer code and password.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "access_token" in res_data["data"]
    assert "refresh_token" in res_data["data"]

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """
    Test login with correct user but incorrect password.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["success"] is False

@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient, db_session: AsyncSession):
    """
    Test token refresh rotation.
    """
    # 1. Login to get refresh token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # 2. Call refresh endpoint
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    res_data = refresh_resp.json()
    assert res_data["success"] is True
    assert "access_token" in res_data["data"]
    assert "refresh_token" in res_data["data"]
    assert res_data["data"]["refresh_token"] != refresh_token  # Enforce rotation!

@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    """
    Test password change with authentication.
    """
    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    change_resp = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "adminpass", "new_password": "Newadminpass1!", "confirm_password": "Newadminpass1!"},
        headers=headers
    )
    assert change_resp.status_code == 200
    assert change_resp.json()["success"] is True

    # Re-login with old password (should fail)
    fail_login = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "adminpass"}
    )
    assert fail_login.status_code == 401

    # Re-login with new password (should succeed)
    success_login = await client.post(
        "/api/v1/auth/login",
        json={"username": 10001, "password": "Newadminpass1!"}
    )
    assert success_login.status_code == 200

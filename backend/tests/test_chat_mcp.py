import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.models.academic import AcademicSession
from app.models.staff import Staff
from app.models.auth import Login
from datetime import date
from app.security.password import hash_password

@pytest.mark.asyncio
async def test_chatbot_endpoints_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Seed test database with session, staff and credentials
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

    # 2. Login as Staff
    staff_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": 11003, "password": "adminpass"}
    )
    assert staff_login_resp.status_code == 200
    staff_token = staff_login_resp.json()["data"]["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 3. Test chat endpoint with mocked LangGraph agent
    mock_final_state = {
        "final_response": "Here is your final score of 85.5.",
        "intent": "conversational",
        "selected_tool": None,
        "tool_parameters": None,
        "sql_query": "SELECT ...",
        "rows_returned": 1,
        "execution_time_ms": 12.3,
        "error": None
    }
    
    with patch("app.mcp.agent.run_agent", return_value=mock_final_state) as mock_run_agent:
        chat_resp = await client.post(
            "/api/v1/chat",
            json={"message": "Show my final score", "academic_session": 9},
            headers=staff_headers
        )
        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert "response" in data
        assert data["response"] == "Here is your final score of 85.5."
        assert len(data["history"]) == 2

        # 4. Test chat history retrieval
        hist_resp = await client.post(
            "/api/v1/chat/history",
            headers=staff_headers
        )
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert len(hist_data["history"]) == 2

        # 5. Test chat history reset
        reset_resp = await client.post(
            "/api/v1/chat/reset",
            headers=staff_headers
        )
        assert reset_resp.status_code == 200
        
        # Verify history is now empty
        hist_resp = await client.post(
            "/api/v1/chat/history",
            headers=staff_headers
        )
        assert hist_resp.status_code == 200
        assert len(hist_resp.json()["history"]) == 0

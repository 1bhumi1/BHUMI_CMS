import asyncio
import os
import sys

from app.database.session import AsyncSessionLocal
from sqlalchemy import text
from app.security.password import verify_password, hash_password

async def investigate():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, computer_code, password_hash, staff_id FROM login ORDER BY id DESC LIMIT 5"))
        logins = result.fetchall()
        for login in logins:
            print(f"Login ID: {login.id}, Computer Code: {login.computer_code}")
            print(f"Hash: {login.password_hash[:15]}...{login.password_hash[-15:]}")
            
            # Fetch staff DOB
            if login.staff_id:
                s_res = await session.execute(text("SELECT date_of_birth FROM staff WHERE id = :id"), {"id": login.staff_id})
                staff_row = s_res.fetchone()
                if staff_row and staff_row[0]:
                    dob = staff_row[0]
                    expected_pwd = f"Staff@{dob.strftime('%d%m%Y')}"
                    
                    # Verify
                    is_valid = verify_password(expected_pwd, login.password_hash)
                    print(f"DOB: {dob}, Expected Pwd: {expected_pwd}")
                    print(f"verify_password({expected_pwd}): {is_valid}")
            print("-" * 20)
            
            
if __name__ == "__main__":
    asyncio.run(investigate())

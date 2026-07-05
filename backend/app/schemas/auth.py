from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class LoginRequest(BaseModel):
    username: int = Field(..., description="Unique computer code or employee code of student/staff")
    password: str = Field(..., description="Plaintext password")

class UserInfo(BaseModel):
    id: int
    name: str
    computer_code: int
    role: str
    department: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds
    user: UserInfo
    permissions: list[str]
    dashboard: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

import re
from pydantic import BaseModel, Field, EmailStr, field_validator

def validate_password_complexity(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
        raise ValueError("Password must contain at least one special character")
    return v

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    def validate_new_password(cls, v):
        return validate_password_complexity(v)

    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v

class ForgotPasswordRequest(BaseModel):
    username: int
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    computer_code: int
    student_id: Optional[int] = None
    staff_id: Optional[int] = None
    active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

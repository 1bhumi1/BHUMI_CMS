from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

# Helper validators
def validate_mobile_field(v: str) -> str:
    if not re.match(r"^\+?[0-9]{10,15}$", v):
        raise ValueError("Invalid phone number format. Must be 10-15 digits.")
    return v

# Designation Schemas
class DesignationCreate(BaseModel):
    d_order: int
    designation: str = Field(..., max_length=100)
    active: int = Field(1)

class DesignationResponse(BaseModel):
    id: int
    d_order: int
    designation: str
    active: int

    class Config:
        from_attributes = True

# StaffRole Schemas
class StaffRoleCreate(BaseModel):
    staff_id: int
    role_id: int
    department_id: int
    academic_session_id: Optional[int] = None
    academic_term_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class StaffRoleResponse(BaseModel):
    id: int
    staff_id: int
    role_id: int
    department_id: int
    academic_session_id: Optional[int] = None
    academic_term_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True

# StaffDetails Schemas
class StaffDetailsCreate(BaseModel):
    designation_id: Optional[int] = None
    dept_id: Optional[int] = None
    qualification: Optional[str] = Field(None, max_length=100)
    experience_years: Optional[float] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=30)
    ifsc: Optional[str] = Field(None, max_length=20)

class StaffDetailsResponse(BaseModel):
    id: int
    staff_id: Optional[int] = None
    designation_id: Optional[int] = None
    dept_id: Optional[int] = None
    qualification: Optional[str] = None
    experience_years: Optional[float] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None

    class Config:
        from_attributes = True

# Staff Schemas
class StaffCreate(BaseModel):
    computer_code: int = Field(..., description="Manually entered computer code")
    title: Optional[str] = Field(None, max_length=10)
    first_name: str = Field(..., max_length=64)
    middle_name: Optional[str] = Field(None, max_length=64)
    last_name: str = Field(..., max_length=64)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, description="M, F, or O")
    mobile1: str
    mobile2: Optional[str] = None
    email: Optional[EmailStr] = None
    abc_id: str = Field(..., max_length=50)
    aadhar_number: int = Field(..., description="12-digit numeric value")
    permanent_address: str = Field(..., max_length=100)
    city: int
    date_join: date
    date_leave: Optional[date] = None
    role_id: int
    department_id: int
    academic_session_id: Optional[int] = None
    academic_term_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str] = None) -> Optional[str]:
        if v is not None and v not in ["M", "F", "O"]:
            raise ValueError("gender must be 'M', 'F', or 'O'")
        return v

    @field_validator("mobile1", "mobile2")
    @classmethod
    def validate_mobiles(cls, v: Optional[str] = None) -> Optional[str]:
        if v is not None:
            return validate_mobile_field(v)
        return v

    @field_validator("aadhar_number")
    @classmethod
    def validate_aadhar(cls, v: int) -> int:
        if len(str(v)) != 12:
            raise ValueError("Aadhar number must be exactly 12 digits.")
        return v

class StaffUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=10)
    first_name: Optional[str] = Field(None, max_length=64)
    middle_name: Optional[str] = Field(None, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    mobile1: Optional[str] = None
    mobile2: Optional[str] = None
    email: Optional[EmailStr] = None
    abc_id: Optional[str] = Field(None, max_length=50)
    aadhar_number: Optional[int] = None
    permanent_address: Optional[str] = Field(None, max_length=100)
    city: Optional[int] = None
    photo: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None
    date_join: Optional[date] = None
    date_leave: Optional[date] = None
    role_id: Optional[int] = None
    department_id: Optional[int] = None
    academic_session_id: Optional[int] = None
    academic_term_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    details: Optional['StaffDetailsCreate'] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str] = None) -> Optional[str]:
        if v is not None and v not in ["M", "F", "O"]:
            raise ValueError("gender must be 'M', 'F', or 'O'")
        return v

    @field_validator("mobile1", "mobile2")
    @classmethod
    def validate_mobiles(cls, v: Optional[str] = None) -> Optional[str]:
        if v is not None:
            return validate_mobile_field(v)
        return v

    @field_validator("aadhar_number")
    @classmethod
    def validate_aadhar(cls, v: Optional[int] = None) -> Optional[int]:
        if v is not None:
            if len(str(v)) != 12:
                raise ValueError("Aadhar number must be exactly 12 digits.")
        return v

class StaffResponse(BaseModel):
    id: int
    computer_code: int
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    mobile1: str
    mobile2: Optional[str] = None
    email: Optional[str] = None
    abc_id: str
    aadhar_number: int
    permanent_address: str
    city: int
    active: bool
    date_join: date
    date_leave: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Paginated Staff list response
class StaffListResponse(BaseModel):
    items: List[StaffResponse]
    total: int
    skip: int
    limit: int

# Composite Staff creation schema
class CompositeStaffCreate(BaseModel):
    staff: StaffCreate
    details: Optional[StaffDetailsCreate] = None
    roles: List[StaffRoleCreate] = []

# Detailed Staff profile response
class StaffProfileResponse(BaseModel):
    staff: StaffResponse
    details: Optional[StaffDetailsResponse] = None
    roles: List[StaffRoleResponse] = []

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class AcademicSessionBase(BaseModel):
    session_name: str = Field(..., max_length=20, description="Session name (e.g. 2026-2027)")
    start_date: date = Field(..., description="Start date of the academic session")
    end_date: date = Field(..., description="End date of the academic session")
    is_active: bool = Field(False, description="Is this the current session")

class AcademicSessionCreate(AcademicSessionBase):
    pass

class AcademicSessionUpdate(AcademicSessionBase):
    pass

class AcademicSessionResponse(AcademicSessionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class AcademicSessionListResponse(BaseModel):
    items: List[AcademicSessionResponse]
    total: int
    page: int
    size: int

class DropdownOption(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
class AcademicSessionDropdownResponse(BaseModel):
    sessions: List[DropdownOption]

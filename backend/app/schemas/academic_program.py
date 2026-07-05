from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class DepartmentBase(BaseModel):
    id: int
    name: str
    dept_code: str
    active: int
    model_config = ConfigDict(from_attributes=True)

class ProgramBase(BaseModel):
    id: int
    name: str
    program_code: str
    active: int
    model_config = ConfigDict(from_attributes=True)

class SpecializationBase(BaseModel):
    id: int
    name: str
    specialization_code: str
    active: int
    model_config = ConfigDict(from_attributes=True)

class AcademicProgramBase(BaseModel):
    department_id: int = Field(..., description="ID of the associated department")
    program_id: int = Field(..., description="ID of the associated program")
    specialization_id: Optional[int] = Field(None, description="ID of the associated specialization")
    duration_years: int = Field(..., gt=0, description="Duration in years")
    total_semesters: int = Field(..., gt=0, description="Total number of semesters")
    entry_semester: int = Field(..., gt=0, description="Entry semester number")

class AcademicProgramCreate(AcademicProgramBase):
    pass

class AcademicProgramUpdate(AcademicProgramBase):
    pass

class AcademicProgramResponse(AcademicProgramBase):
    id: int
    
    # Nested fields for frontend rendering
    department: Optional[DepartmentBase] = None
    program: Optional[ProgramBase] = None
    specialization: Optional[SpecializationBase] = None

    model_config = ConfigDict(from_attributes=True)

class AcademicProgramListResponse(BaseModel):
    items: List[AcademicProgramResponse]
    total: int
    page: int
    size: int

class DropdownOption(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DepartmentDropdownResponse(BaseModel):
    departments: List[DropdownOption]

class ProgramDropdownResponse(BaseModel):
    programs: List[DropdownOption]

class SpecializationDropdownResponse(BaseModel):
    specializations: List[DropdownOption]

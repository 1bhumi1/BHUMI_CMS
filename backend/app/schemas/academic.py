from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field

# Institute Schemas
class InstituteCreate(BaseModel):
    name: str = Field(..., max_length=150)

class InstituteResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class InstituteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)

# Department Schemas
class DepartmentCreate(BaseModel):
    institue_id: int = Field(..., description="Typo-aligned institute reference id")
    name: str = Field(..., max_length=100)
    dept_code: str = Field(..., max_length=50)
    have_student: int = Field(default=1)
    have_staff: int = Field(default=1)
    active: int = Field(default=1)

class DepartmentResponse(BaseModel):
    id: int
    institue_id: int
    name: str
    dept_code: str
    have_student: int
    have_staff: int
    active: int

    class Config:
        from_attributes = True

class DepartmentUpdate(BaseModel):
    institue_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=100)
    dept_code: Optional[str] = Field(None, max_length=50)
    have_student: Optional[int] = None
    have_staff: Optional[int] = None
    active: Optional[int] = None

# Program Schemas
class ProgramCreate(BaseModel):
    name: str = Field(..., max_length=100)
    program_code: str = Field(..., max_length=50)
    active: int = Field(default=1)

class ProgramResponse(BaseModel):
    id: int
    name: str
    program_code: str
    active: int

    class Config:
        from_attributes = True

class ProgramUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    program_code: Optional[str] = Field(None, max_length=50)
    active: Optional[int] = None

# Specialization Schemas
class SpecializationCreate(BaseModel):
    program_id: int
    department_id: int
    name: str = Field(..., max_length=150)
    specialization_code: str = Field(..., max_length=50)
    active: int = Field(default=1)

class SpecializationResponse(BaseModel):
    id: int
    program_id: int
    department_id: int
    name: str
    specialization_code: str
    active: int

    class Config:
        from_attributes = True

class SpecializationUpdate(BaseModel):
    program_id: Optional[int] = None
    department_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=150)
    specialization_code: Optional[str] = Field(None, max_length=50)
    active: Optional[int] = None

# AcademicProgram Schemas
class AcademicProgramCreate(BaseModel):
    department_id: int
    program_id: int
    specialization_id: Optional[int] = None
    duration_years: int
    total_semesters: int
    entry_semester: int

class AcademicProgramResponse(BaseModel):
    id: int
    department_id: int
    program_id: int
    specialization_id: Optional[int]
    duration_years: int
    total_semesters: int
    entry_semester: int

    class Config:
        from_attributes = True

# AcademicSession Schemas
class AcademicSessionCreate(BaseModel):
    session_name: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    is_active: bool = False

class AcademicSessionResponse(BaseModel):
    id: int
    session_name: str
    start_date: date
    end_date: date
    is_active: bool

    class Config:
        from_attributes = True

# AcademicTerm Schemas
class AcademicTermCreate(BaseModel):
    academic_session_id: int
    term_name: str = Field(..., max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class AcademicTermResponse(BaseModel):
    id: int
    academic_session_id: int
    term_name: str
    start_date: Optional[date]
    end_date: Optional[date]

    class Config:
        from_attributes = True
class AcademicTermDetailResponse(AcademicTermResponse):
    academic_session: Optional[AcademicSessionResponse] = None

class AcademicTermUpdate(BaseModel):
    academic_session_id: Optional[int] = None
    term_name: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# Subject Schemas
class SubjectCreate(BaseModel):
    subject_code: str = Field(..., max_length=50)
    subject_name: str = Field(..., max_length=150)
    department_id: Optional[int] = None
    active: int = Field(default=1)

class SubjectResponse(BaseModel):
    id: int
    subject_code: str
    subject_name: str
    department_id: Optional[int]
    active: int

    class Config:
        from_attributes = True

class SubjectDetailResponse(SubjectResponse):
    department: Optional[DepartmentResponse] = None

class SubjectUpdate(BaseModel):
    subject_code: Optional[str] = Field(None, max_length=50)
    subject_name: Optional[str] = Field(None, max_length=150)
    department_id: Optional[int] = None
    active: Optional[int] = None


# SubjectCredit Schemas
class SubjectCreditCreate(BaseModel):
    subject_id: int
    scheme_name: str = Field(..., max_length=100)
    lecture_credits: int = Field(default=0)
    tutorial_credits: int = Field(default=0)
    practical_credits: int = Field(default=0)
    total_credits: int = Field(default=0)

class SubjectCreditResponse(BaseModel):
    id: int
    subject_id: int
    scheme_name: str
    lecture_credits: int
    tutorial_credits: int
    practical_credits: int
    total_credits: int

    class Config:
        from_attributes = True

class SubjectCreditDetailResponse(SubjectCreditResponse):
    subject: Optional[SubjectResponse] = None

class SubjectCreditUpdate(BaseModel):
    subject_id: Optional[int] = None
    scheme_name: Optional[str] = Field(None, max_length=100)
    lecture_credits: Optional[int] = None
    tutorial_credits: Optional[int] = None
    practical_credits: Optional[int] = None
    total_credits: Optional[int] = None






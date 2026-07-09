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


# SubjectNewCredit Schemas
class SubjectNewCreditCreate(BaseModel):
    college_sub_code: str = Field(..., max_length=32)
    type: str = Field(..., max_length=50)
    credit: int = Field(default=0)
    end_sem: int = Field(default=0)
    mst: int = Field(default=0)
    assignment: int = Field(default=0)
    labwork_sessional: int = Field(default=0)
    academic_session: int
    semester: int
    course: Optional[str] = "B.Tech."
    remark: Optional[str] = ""

class SubjectNewCreditResponse(BaseModel):
    id: int
    college_sub_code: str
    type: str
    credit: int
    end_sem: int
    mst: int
    assignment: int
    labwork_sessional: int
    academic_session: int
    semester: int
    course: str
    remark: str

    class Config:
        from_attributes = True

class SubjectNewCreditDetailResponse(SubjectNewCreditResponse):
    pass

class SubjectNewCreditUpdate(BaseModel):
    college_sub_code: Optional[str] = None
    type: Optional[str] = None
    credit: Optional[int] = None
    end_sem: Optional[int] = None
    mst: Optional[int] = None
    assignment: Optional[int] = None
    labwork_sessional: Optional[int] = None
    academic_session: Optional[int] = None
    semester: Optional[int] = None
    course: Optional[str] = None
    remark: Optional[str] = None


class SubjectCategoryResponse(BaseModel):
    id: int
    category: str
    category_code: str
    active: int

    class Config:
        from_attributes = True


class SubjectCodeResponse(BaseModel):
    id: int
    sub_code: str
    hod_computer_code: Optional[int] = None
    department: Optional[int] = None

    class Config:
        from_attributes = True


class SubjectNewCreate(BaseModel):
    semester: int
    academic_session: int
    clg_sub_code: str
    university_sub_code: str
    subject_name: str
    type: str
    priority: Optional[str] = None
    scheme_id: Optional[int] = None
    department: Optional[int] = None
    specialization: Optional[int] = None
    course: Optional[str] = None
    active: int = 1
    elective: int = 0
    remark: Optional[str] = None


class SubjectNewResponse(BaseModel):
    id: int
    semester: int
    academic_session: int
    clg_sub_code: str
    university_sub_code: str
    subject_name: str
    type: str
    priority: Optional[str] = None
    scheme_id: Optional[int] = None
    department: Optional[int] = None
    specialization: Optional[int] = None
    course: Optional[str] = None
    active: int
    elective: int
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class SubjectNewListResponse(BaseModel):
    items: List[SubjectNewResponse]
    total: int
    page: int
    size: int


class SubjectNewCreditConfigSave(BaseModel):
    college_sub_code: str
    totalCredit: int
    endSem: int
    mst: Optional[int] = 0
    assignment: Optional[int] = 0
    labwork_sessional: Optional[int] = 0
    type: Optional[str] = None


class SubjectNewCreditBulkSave(BaseModel):
    semester: int
    academic_session: int
    configs: List[SubjectNewCreditConfigSave]






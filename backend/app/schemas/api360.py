from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- CR Scores ---
class API360CRBase(BaseModel):
    cr1: int = Field(0, ge=0)
    cr2: int = Field(0, ge=0)
    cr3: int = Field(0, ge=0)
    cr4: int = Field(0, ge=0)
    cr5: int = Field(0, ge=0)
    cr6: int = Field(0, ge=0)
    cr7: int = Field(0, ge=0)
    cr8: int = Field(0, ge=0)
    cr9: int = Field(0, ge=0)
    cr10: int = Field(0, ge=0)

class API360CRCreate(API360CRBase):
    pass

class API360CRResponse(API360CRBase):
    api_id: int
    class Config:
        from_attributes = True

# --- Category 1i ---
class API360Cat1iBase(BaseModel):
    sno: int
    sas: str = Field(..., max_length=30)
    ccnc: str
    nsc: int = Field(0, ge=0)
    nahcof: int = Field(0, ge=0)
    nahcon: int = Field(0, ge=0)

class API360Cat1iCreate(API360Cat1iBase):
    pass

class API360Cat1iResponse(API360Cat1iBase):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True

# --- Category 1ii ---
class API360Cat1iiBase(BaseModel):
    sno: int
    sas: str = Field(..., max_length=30)
    cnctp: str
    asf: int = Field(0, ge=0)

class API360Cat1iiCreate(API360Cat1iiBase):
    pass

class API360Cat1iiResponse(API360Cat1iiBase):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True

# --- Category 1iii ---
class API360Cat1iiiBase(BaseModel):
    sno: int
    sas: str = Field(..., max_length=30)
    activity: str = Field(..., max_length=500)
    pe: str = Field(..., max_length=500)

class API360Cat1iiiCreate(API360Cat1iiiBase):
    pass

class API360Cat1iiiResponse(API360Cat1iiiBase):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True

# --- Category 1iv ---
class API360Cat1ivBase(BaseModel):
    sno: int
    sas: str = Field(..., max_length=30)
    activity: str = Field(..., max_length=500)
    pe: int = Field(0, ge=0)

class API360Cat1ivCreate(API360Cat1ivBase):
    pass

class API360Cat1ivResponse(API360Cat1ivBase):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True

# --- Category 1v ---
class API360Cat1vBase(BaseModel):
    sno: int
    sas: str = Field(..., max_length=30)
    activity: str = Field(..., max_length=500)
    pe: int = Field(0, ge=0)

class API360Cat1vCreate(API360Cat1vBase):
    pass

class API360Cat1vResponse(API360Cat1vBase):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True

# --- Category 2 ---
class API360Cat2Base(BaseModel):
    sno: str = Field(..., max_length=10)
    score: str = Field(..., max_length=5)

class API360Cat2Create(API360Cat2Base):
    pass

class API360Cat2Response(API360Cat2Base):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True

# --- Category 3 ---
class API360Cat3Base(BaseModel):
    sno: str = Field(..., max_length=10)
    score: str = Field(..., max_length=5)

class API360Cat3Create(API360Cat3Base):
    pass

class API360Cat3Response(API360Cat3Base):
    api_data_id: int
    api_id: int
    class Config:
        from_attributes = True


# --- Master Info ---
class API360InfoBase(BaseModel):
    faculty_computer_code: int
    academic_session: int = Field(9)
    submited: bool = Field(False)
    hod_approval: bool = Field(False)

class API360InfoCreate(API360InfoBase):
    cr: Optional[API360CRCreate] = None
    cat1i: List[API360Cat1iCreate] = []
    cat1ii: List[API360Cat1iiCreate] = []
    cat1iii: List[API360Cat1iiiCreate] = []
    cat1iv: List[API360Cat1ivCreate] = []
    cat1v: List[API360Cat1vCreate] = []
    cat2: List[API360Cat2Create] = []
    cat3: List[API360Cat3Create] = []

class API360InfoUpdate(BaseModel):
    faculty_computer_code: Optional[int] = None
    academic_session: Optional[int] = None
    submited: Optional[bool] = None
    hod_approval: Optional[bool] = None
    cr: Optional[API360CRCreate] = None
    cat1i: Optional[List[API360Cat1iCreate]] = None
    cat1ii: Optional[List[API360Cat1iiCreate]] = None
    cat1iii: Optional[List[API360Cat1iiiCreate]] = None
    cat1iv: Optional[List[API360Cat1ivCreate]] = None
    cat1v: Optional[List[API360Cat1vCreate]] = None
    cat2: Optional[List[API360Cat2Create]] = None
    cat3: Optional[List[API360Cat3Create]] = None

class API360InfoResponse(API360InfoBase):
    api_id: int

    class Config:
        from_attributes = True

class API360ConfidentialBase(BaseModel):
    faculty_feedback_id: int
    faculty_code: int
    hod_code: int
    department_id: int
    academic_session: int
    parameter_1: Optional[int] = Field(None, ge=1, le=10)
    parameter_2: Optional[int] = Field(None, ge=1, le=10)
    parameter_3: Optional[int] = Field(None, ge=1, le=10)
    parameter_4: Optional[int] = Field(None, ge=1, le=10)
    parameter_5: Optional[int] = Field(None, ge=1, le=10)
    parameter_6: Optional[int] = Field(None, ge=1, le=10)
    parameter_7: Optional[int] = Field(None, ge=1, le=10)
    total_marks: int = 0
    remarks: Optional[str] = None
    status: str = Field("Draft", max_length=20)

class API360ConfidentialCreate(BaseModel):
    faculty_feedback_id: int
    parameter_1: Optional[int] = Field(None, ge=1, le=10)
    parameter_2: Optional[int] = Field(None, ge=1, le=10)
    parameter_3: Optional[int] = Field(None, ge=1, le=10)
    parameter_4: Optional[int] = Field(None, ge=1, le=10)
    parameter_5: Optional[int] = Field(None, ge=1, le=10)
    parameter_6: Optional[int] = Field(None, ge=1, le=10)
    parameter_7: Optional[int] = Field(None, ge=1, le=10)
    remarks: Optional[str] = None
    status: str = Field("Draft", max_length=20)

class API360ConfidentialResponse(API360ConfidentialBase):
    confidential_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class API360InfoDetailedResponse(API360InfoResponse):
    cr: Optional[API360CRResponse] = None
    confidential: Optional[API360ConfidentialResponse] = None
    cat1i: List[API360Cat1iResponse] = []
    cat1ii: List[API360Cat1iiResponse] = []
    cat1iii: List[API360Cat1iiiResponse] = []
    cat1iv: List[API360Cat1ivResponse] = []
    cat1v: List[API360Cat1vResponse] = []
    cat2: List[API360Cat2Response] = []
    cat3: List[API360Cat3Response] = []
    faculty_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None

    class Config:
        from_attributes = True

class API360InfoListResponse(BaseModel):
    items: List[API360InfoDetailedResponse]
    total: int
    skip: int
    limit: int

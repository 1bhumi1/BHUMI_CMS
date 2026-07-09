from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from app.schemas.academic import AcademicSessionResponse, DepartmentResponse, ProgramResponse

class EventBase(BaseModel):
    academic_session_id: int
    department_id: Optional[int] = None
    program_id: Optional[int] = None
    semester: Optional[int] = None
    title: str = Field(..., max_length=255)
    event_type: str = Field(..., max_length=50) # Workshop, Seminar, etc.
    description: str
    start_date: datetime
    end_date: datetime
    venue: str = Field(..., max_length=255)
    max_seats: int
    registration_deadline: datetime
    poster_url: Optional[str] = Field(None, max_length=500)
    audience: str = Field(..., max_length=50) # Students, Faculty, Both
    registration_required: int = Field(default=1) # 1=Yes, 0=No
    fee_required: int = Field(default=0) # 1=Yes, 0=No
    fee_amount: Decimal = Field(default=Decimal("0.00"))
    status: str = Field(default="Draft", max_length=50) # Draft, Published, Closed

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    academic_session_id: Optional[int] = None
    department_id: Optional[int] = None
    program_id: Optional[int] = None
    semester: Optional[int] = None
    title: Optional[str] = Field(None, max_length=255)
    event_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    venue: Optional[str] = Field(None, max_length=255)
    max_seats: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    poster_url: Optional[str] = Field(None, max_length=500)
    audience: Optional[str] = Field(None, max_length=50)
    registration_required: Optional[int] = None
    fee_required: Optional[int] = None
    fee_amount: Optional[Decimal] = None
    status: Optional[str] = Field(None, max_length=50)

class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class EventDetailResponse(EventResponse):
    academic_session: Optional[AcademicSessionResponse] = None
    department: Optional[DepartmentResponse] = None
    program: Optional[ProgramResponse] = None
    registered_count: int = 0
    is_registered: bool = False
    registration_status: Optional[str] = None

class EventRegistrationBase(BaseModel):
    event_id: int

class EventRegistrationCreate(EventRegistrationBase):
    pass

class EventRegistrationResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    registered_at: datetime
    status: str

    class Config:
        from_attributes = True

class EventRegistrationDetailResponse(EventRegistrationResponse):
    event_title: str
    event_type: str
    user_name: str
    user_computer_code: int
    user_role: str
    payment_status: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    attended: int = 0
    has_certificate: bool = False
    certificate_code: Optional[str] = None

class EventPaymentResponse(BaseModel):
    id: int
    registration_id: int
    transaction_id: str
    payment_gateway_ref: Optional[str] = None
    amount: Decimal
    status: str
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PayUCallbackPayload(BaseModel):
    transaction_id: str
    status: str # Success, Failed
    payment_gateway_ref: Optional[str] = None

class EventAttendanceMark(BaseModel):
    registration_id: int
    attended: int # 1=Yes, 0=No

class EventCertificateResponse(BaseModel):
    id: int
    event_id: int
    registration_id: int
    certificate_code: str
    issued_at: datetime
    file_url: Optional[str] = None

    class Config:
        from_attributes = True

class EventReportSummary(BaseModel):
    total_registrations: int
    paid_registrations: int
    pending_registrations: int
    cancelled_registrations: int
    attendance_count: int
    total_revenue: Decimal

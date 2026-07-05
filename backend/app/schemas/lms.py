from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional, List

class LeaveBase(BaseModel):
    session: Optional[str] = None
    start_date: date
    end_date: date
    days: float
    leave_type: str
    reason: str

class FacultyAssignmentRequest(BaseModel):
    faculty_date: date
    faculty_computer_code: int
    assigned_class_dept: str
    assigned_section: str
    lecture_type: str
    start_time: str
    end_time: str
    other_responsibility: str

class LeaveCreate(LeaveBase):
    assignments: Optional[List[FacultyAssignmentRequest]] = []

class LeaveUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: Optional[float] = None
    leave_type: Optional[str] = None
    reason: Optional[str] = None

class LeaveResponse(LeaveBase):
    model_config = ConfigDict(from_attributes=True)

    apply_id: str
    apply_date: date
    faculty_computer_code: int
    pre_balance: float
    hod_approval: int
    principal_approval: int
    ot_hours: Optional[float] = None
    required_action: Optional[str] = None
    faculty_name: Optional[str] = None
    assignments: Optional[List['FacultyAssignmentResponse']] = []

class LeaveApproval(BaseModel):
    status: int = Field(..., description="0 for pending, 1 for approved, 2 for rejected")

class LeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty_computer_code: int
    academic_session: int
    cl: float
    dl: float
    el: float
    ol: float
    lwp: float
    sl: float
    ab: float
    ml: float
    sdl: float
    vl: float
    od: float
    ot: int

class LeaveLimitBase(BaseModel):
    leave_type: str
    days: int
    active: int

class LeaveLimitCreate(LeaveLimitBase):
    pass

class LeaveLimitUpdate(BaseModel):
    days: Optional[int] = None
    active: Optional[int] = None

class LeaveLimitResponse(LeaveLimitBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class FacultyAssignmentBase(BaseModel):
    apply_id: str
    faculty_date: date
    faculty_computer_code: int
    assigned_class_dept: str
    assigned_section: str
    lecture_type: str
    start_time: str
    end_time: str
    other_responsibility: str

class FacultyAssignmentCreate(FacultyAssignmentBase):
    pass

class FacultyAssignmentResponse(FacultyAssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    assign_faculty_id: int
    status: int

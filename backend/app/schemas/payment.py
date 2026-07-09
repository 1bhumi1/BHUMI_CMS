from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List, Dict, Any

class FeeStructureResponse(BaseModel):
    id: int
    title: str
    description: str
    amount: float
    academic_session_id: int
    due_date: date
    
    model_config = ConfigDict(from_attributes=True)

class StudentFeeResponse(BaseModel):
    id: int
    computer_code: int
    fee_structure_id: int
    status: str
    txn_details_id: Optional[int] = None
    fee_structure: FeeStructureResponse
    
    model_config = ConfigDict(from_attributes=True)

class PaymentInitiateResponse(BaseModel):
    key: str
    txnid: str
    amount: float
    productinfo: str
    firstname: str
    email: str
    phone: str
    surl: str
    furl: str
    hash: str
    action_url: str # PayU post URL (sandbox/live)
    udf1: str
    udf2: str
    
    model_config = ConfigDict(from_attributes=True)

class TransactionResponse(BaseModel):
    id: int
    computer_code: int
    enrollment: str
    firstname: str
    email: str
    phone: int
    student_section_id: int
    study_department_id: int
    semester: int
    academic_session: int
    amount: float
    extra_charge: float
    productinfo: str
    txnid: str
    txn_date: date
    status: str
    status_to_show: str
    msg: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaymentStatsResponse(BaseModel):
    total_revenue: float
    pending_count: int
    success_count: int
    failed_count: int
    refunded_count: int
    
    model_config = ConfigDict(from_attributes=True)

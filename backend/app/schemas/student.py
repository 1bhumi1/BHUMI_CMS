# Node.js Comparison:
# In Node.js/Express, we validate request bodies using libraries like Joi, Zod, or express-validator.
# Example using Zod:
# const StudentCreateSchema = z.object({
#   computer_code: z.number(),
#   first_name: z.string().max(100),
#   email: z.string().email().optional()
# });
#
# In FastAPI, we use Pydantic schemas (inheriting from BaseModel).
# Pydantic schemas handle:
# 1. Validation (req.body parsing & error raising)
# 2. Serialization (converting DB models to JSON responses)

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
import re

# Helper validators (Equivalent to custom validator functions in Joi/Zod)
def validate_mobile_field(v: Optional[str]) -> Optional[str]:
    if v is not None:
        if not re.match(r"^\+?[0-9]{10,15}$", v):
            raise ValueError("Invalid phone number format. Must be 10-15 digits.")
    return v

def validate_aadhar_field(v: Optional[str]) -> Optional[str]:
    if v is not None:
        if not re.match(r"^[0-9]{12}$", v):
            raise ValueError("Aadhar number must be exactly 12 digits.")
    return v


# Address Schemas
# Express/Joi Equivalent:
# const StudentAddressCreate = Joi.object({
#   address_type: Joi.string().valid('permanent', 'local').required(),
#   address_line: Joi.string().min(5).max(500).required(),
#   district: Joi.string().max(100).optional(),
#   state: Joi.string().max(100).optional(),
#   pincode: Joi.string().max(10).optional()
# });
class StudentAddressCreate(BaseModel):
    address_type: str = Field(..., description="permanent or local")
    address_line: str = Field(..., min_length=5, max_length=500)
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

    # Field validator for enum verification
    # Express Equivalent (Zod):
    # address_type: z.enum(["permanent", "local"])
    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, v: str) -> str:
        if v not in ["permanent", "local"]:
            raise ValueError("address_type must be either 'permanent' or 'local'")
        return v


# Response Schema (Used to format JSON output sent to the client)
# Express Equivalent:
# In Express, we serialize data manually or using templates/DTOs:
# res.json({ id: addr.id, student_id: addr.student_id, ... });
class StudentAddressResponse(BaseModel):
    id: int
    student_id: int
    address_type: str
    address_line: str
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    # Config class allows Pydantic to read SQLAlchemy model object attributes
    # In Node.js, we can do JSON.stringify(dbModel) directly.
    # In FastAPI, setting 'from_attributes = True' tells Pydantic:
    # "Hey, you can read fields using object dot-notation (e.g., student.id) instead of just dict brackets."
    class Config:
        from_attributes = True


# Admission Schemas
class StudentAdmissionCreate(BaseModel):
    academic_program_id: int
    academic_session_id: int
    admission_date: date
    admission_type: str = Field("regular", description="regular, lateral, or transfer")
    quota: Optional[str] = Field(None, max_length=50)
    admission_round: Optional[str] = Field(None, max_length=100)
    entry_semester: int = Field(1)
    status: str = Field("active", description="active, completed, cancelled, or dropout")

    @field_validator("admission_type")
    @classmethod
    def validate_admission_type(cls, v: str) -> str:
        if v not in ["regular", "lateral", "transfer"]:
            raise ValueError("admission_type must be 'regular', 'lateral', or 'transfer'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["active", "completed", "cancelled", "dropout"]:
            raise ValueError("status must be 'active', 'completed', 'cancelled', or 'dropout'")
        return v


class StudentAdmissionResponse(BaseModel):
    id: int
    student_id: int
    academic_program_id: int
    academic_session_id: int
    admission_date: date
    admission_type: str
    quota: Optional[str] = None
    admission_round: Optional[str] = None
    entry_semester: int
    status: Optional[str] = None

    class Config:
        from_attributes = True


# Document Schemas
class StudentDocumentCreate(BaseModel):
    document_type_id: int
    submitted: bool = False
    verified: bool = False
    file_path: Optional[str] = Field(None, max_length=500)
    remarks: Optional[str] = Field(None, max_length=500)


class StudentDocumentResponse(BaseModel):
    id: int
    student_id: int
    document_type_id: int
    submitted: Optional[bool] = None
    verified: Optional[bool] = None
    file_path: Optional[str] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


# Entrance Exam Schemas
class StudentEntranceExamCreate(BaseModel):
    exam_name: str = Field(..., max_length=100)
    roll_no: Optional[str] = Field(None, max_length=50)
    score: Optional[float] = None
    percentile: Optional[float] = None
    exam_rank: Optional[int] = None


class StudentEntranceExamResponse(BaseModel):
    id: int
    student_id: int
    exam_name: str
    roll_no: Optional[str] = None
    score: Optional[float] = None
    percentile: Optional[float] = None
    exam_rank: Optional[int] = None

    class Config:
        from_attributes = True


# Guardian Schemas
class StudentGuardianCreate(BaseModel):
    relation: str = Field(..., description="father, mother, or guardian")
    name: str = Field(..., max_length=200)
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    occupation: Optional[str] = Field(None, max_length=100)
    occupation_description: Optional[str] = Field(None, max_length=255)

    @field_validator("relation")
    @classmethod
    def validate_relation(cls, v: str) -> str:
        if v not in ["father", "mother", "guardian"]:
            raise ValueError("relation must be 'father', 'mother', or 'guardian'")
        return v

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: Optional[str] = None) -> Optional[str]:
        return validate_mobile_field(v)


class StudentGuardianResponse(BaseModel):
    id: int
    student_id: int
    relation: str
    name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    occupation: Optional[str] = None
    occupation_description: Optional[str] = None

    class Config:
        from_attributes = True


# Qualification Schemas
class StudentQualificationCreate(BaseModel):
    qualification_type: str = Field(..., description="10th, 12th, Diploma, UG, PG, or Other")
    board_university: Optional[str] = Field(None, max_length=255)
    passing_year: Optional[int] = Field(None, description="Passing year (YYYY)")
    marks: Optional[float] = None
    max_marks: Optional[float] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None

    @field_validator("qualification_type")
    @classmethod
    def validate_qualification_type(cls, v: str) -> str:
        if v not in ["10th", "12th", "Diploma", "UG", "PG", "Other"]:
            raise ValueError("qualification_type must be '10th', '12th', 'Diploma', 'UG', 'PG', or 'Other'")
        return v

    @field_validator("passing_year")
    @classmethod
    def validate_passing_year(cls, v: Optional[int] = None) -> Optional[int]:
        if v is not None:
            if v < 1900 or v > 2100:
                raise ValueError("passing_year must be between 1900 and 2100")
        return v


class StudentQualificationResponse(BaseModel):
    id: int
    student_id: int
    qualification_type: str
    board_university: Optional[str] = None
    passing_year: Optional[int] = None
    marks: Optional[float] = None
    max_marks: Optional[float] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None

    class Config:
        from_attributes = True


# Master Student Schemas
# StudentCreate maps to POST request bodies (req.body when adding a student).
class StudentCreate(BaseModel):
    computer_code: int = Field(..., description="Manually entered computer code")
    enrollment_no: Optional[str] = Field(None, max_length=50)
    first_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, description="M, F, or O")
    date_of_birth: Optional[date] = None
    aadhar_no: Optional[str] = None
    abc_id: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    blood_group: Optional[str] = Field(None, max_length=5)
    category: Optional[str] = Field(None, max_length=20)
    religion: Optional[str] = Field(None, max_length=50)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str] = None) -> Optional[str]:
        if v is not None and v not in ["M", "F", "O"]:
            raise ValueError("gender must be 'M', 'F', or 'O'")
        return v

    @field_validator("aadhar_no")
    @classmethod
    def validate_aadhar(cls, v: Optional[str] = None) -> Optional[str]:
        return validate_aadhar_field(v)

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: Optional[str] = None) -> Optional[str]:
        return validate_mobile_field(v)


# StudentUpdate maps to PUT request bodies (req.body when updating a student).
# All fields are optional since we might only want to update a subset of fields.
class StudentUpdate(BaseModel):
    computer_code: Optional[int] = None
    enrollment_no: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None)
    date_of_birth: Optional[date] = None
    aadhar_no: Optional[str] = None
    abc_id: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    blood_group: Optional[str] = Field(None, max_length=5)
    category: Optional[str] = Field(None, max_length=20)
    religion: Optional[str] = Field(None, max_length=50)
    active: Optional[bool] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str] = None) -> Optional[str]:
        if v is not None and v not in ["M", "F", "O"]:
            raise ValueError("gender must be 'M', 'F', or 'O'")
        return v

    @field_validator("aadhar_no")
    @classmethod
    def validate_aadhar(cls, v: Optional[str] = None) -> Optional[str]:
        return validate_aadhar_field(v)

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: Optional[str] = None) -> Optional[str]:
        return validate_mobile_field(v)


# StudentResponse maps to the response object structure returned to the client (res.json()).
class StudentResponse(BaseModel):
    id: int
    computer_code: Optional[int] = None
    enrollment_no: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    aadhar_no: Optional[str] = None
    abc_id: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    blood_group: Optional[str] = None
    category: Optional[str] = None
    religion: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Composite creation structure (ideal for complete admission pipelines)
# This represents a nested structure where a single POST request registers the student
# along with addresses, admission records, guardian details, and qualifications.
# Express Equivalent:
# Joi.object({ student: StudentCreate, addresses: Joi.array().items(StudentAddressCreate), ... })
class CompositeStudentAdmissionCreate(BaseModel):
    student: StudentCreate
    addresses: List[StudentAddressCreate] = []
    admission: StudentAdmissionCreate
    guardians: List[StudentGuardianCreate] = []
    qualifications: List[StudentQualificationCreate] = []
    entrance_exams: List[StudentEntranceExamCreate] = []


# Composite update structure
class CompositeStudentUpdate(BaseModel):
    student: StudentUpdate
    addresses: Optional[List[StudentAddressCreate]] = None
    admission: Optional[StudentAdmissionCreate] = None
    guardians: Optional[List[StudentGuardianCreate]] = None
    qualifications: Optional[List[StudentQualificationCreate]] = None
    entrance_exams: Optional[List[StudentEntranceExamCreate]] = None


# Detailed Student profile response
class StudentProfileResponse(BaseModel):
    student: StudentResponse
    addresses: List[StudentAddressResponse] = []
    admission: Optional[StudentAdmissionResponse] = None
    guardians: List[StudentGuardianResponse] = []
    qualifications: List[StudentQualificationResponse] = []
    entrance_exams: List[StudentEntranceExamResponse] = []
    documents: List[StudentDocumentResponse] = []

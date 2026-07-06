from app.repositories.student import (
    StudentRepository,
    StudentAddressRepository,
    StudentAdmissionRepository,
    StudentDocumentRepository,
    StudentEntranceExamRepository,
    StudentGuardianRepository,
    StudentQualificationRepository,
    DocumentTypeRepository,
)
from app.repositories.staff import (
    DesignationRepository,
    StaffRepository,
    StaffDetailsRepository,
    StaffRoleRepository,
)
from app.repositories.rbac import (
    LoginRepository,
    RefreshTokenRepository,
    RoleRepository,
    PermissionRepository,
    ImpersonationLogRepository,
)
from app.repositories.academic import (
    InstituteRepository,
    DepartmentRepository,
    ProgramRepository,
    SpecializationRepository,
    AcademicProgramRepository,
    AcademicSessionRepository,
    AcademicTermRepository,
    SubjectRepository,
    SubjectCreditRepository,
)

# Instantiate repository singletons for injection
student_repo = StudentRepository()
student_address_repo = StudentAddressRepository()
student_admission_repo = StudentAdmissionRepository()
student_document_repo = StudentDocumentRepository()
student_entrance_exam_repo = StudentEntranceExamRepository()
student_guardian_repo = StudentGuardianRepository()
student_qualification_repo = StudentQualificationRepository()
document_type_repo = DocumentTypeRepository()

designation_repo = DesignationRepository()
staff_repo = StaffRepository()
staff_details_repo = StaffDetailsRepository()
staff_role_repo = StaffRoleRepository()

login_repo = LoginRepository()
refresh_token_repo = RefreshTokenRepository()
role_repo = RoleRepository()
permission_repo = PermissionRepository()
impersonation_log_repo = ImpersonationLogRepository()

institute_repo = InstituteRepository()
department_repo = DepartmentRepository()
program_repo = ProgramRepository()
specialization_repo = SpecializationRepository()
academic_program_repo = AcademicProgramRepository()
academic_session_repo = AcademicSessionRepository()
academic_term_repo = AcademicTermRepository()
subject_repo = SubjectRepository()
subject_credit_repo = SubjectCreditRepository()

from app.repositories.feedback import FeedbackRepository
feedback_repo = FeedbackRepository()

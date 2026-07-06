from app.services.auth import auth_service
from app.services.student import student_service
from app.services.staff import staff_service
from app.services.rbac import rbac_service
from app.services.academic import academic_service
from app.services.feedback import FeedbackService
from app.repositories import feedback_repo

feedback_service = FeedbackService(feedback_repo)

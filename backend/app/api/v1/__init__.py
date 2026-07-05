from app.api.v1.auth import router as auth_router
from app.api.v1.rbac import router as rbac_router
from app.api.v1.students import router as student_router
from app.api.v1.staff import router as staff_router
from app.api.v1.academic import router as academic_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.search import router as search_router
from app.api.v1.academic_programs import router as academic_programs_router
from app.api.v1.academic_sessions import router as academic_sessions_router
from app.api.v1.lms import router as lms_router
from app.api.v1.api360 import router as api360_router
from app.api.v1.notifications import router as notifications_router

__all__ = [
    "auth_router",
    "rbac_router",
    "student_router",
    "staff_router",
    "academic_router",
    "academic_programs_router",
    "academic_sessions_router",
    "dashboard_router",
    "search_router",
    "lms_router",
    "api360_router",
    "notifications_router",
]

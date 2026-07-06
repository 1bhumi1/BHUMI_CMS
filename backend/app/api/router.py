from fastapi import APIRouter
from app.api.v1 import (
    auth_router,
    rbac_router,
    student_router,
    staff_router,
    academic_router,
    dashboard_router,
    search_router,
    academic_programs_router,
    academic_sessions_router,
    lms_router,
    api360_router,
    notifications_router,
    chat_router,
    ai_router,
)

api_router = APIRouter()

# Group all version 1 endpoints under /api/v1
api_router.include_router(auth_router)
api_router.include_router(rbac_router)
api_router.include_router(student_router)
api_router.include_router(staff_router)
api_router.include_router(academic_router)
api_router.include_router(dashboard_router)
api_router.include_router(search_router)
api_router.include_router(academic_programs_router)
api_router.include_router(academic_sessions_router)
api_router.include_router(lms_router)
api_router.include_router(api360_router)
api_router.include_router(notifications_router)
api_router.include_router(chat_router)
api_router.include_router(ai_router)

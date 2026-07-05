from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.schemas.response import StandardResponse
from app.services.auth import auth_service
from app.dependencies.auth import get_current_user
from app.models.auth import Login
from app.audit.auditor import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    try:
        token_data = await auth_service.login_user(db, payload.username, payload.password)
        # Fetch user for logging
        user = await auth_service.authenticate_user(db, payload.username, payload.password)
        
        log_audit_event(
            event_type="LOGIN",
            actor_id=user.id,
            actor_code=user.computer_code,
            action="User login successful",
            status="SUCCESS",
            ip_address=ip_addr,
            user_agent=ua
        )
        return StandardResponse(message="Login successful", data=token_data)
        
    except Exception as e:
        log_audit_event(
            event_type="FAILED_LOGIN",
            actor_id=None,
            actor_code=payload.username,
            action=f"Failed login attempt: {str(e)}",
            status="FAILURE",
            ip_address=ip_addr,
            user_agent=ua
        )
        raise e

@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    token_data = await auth_service.refresh_tokens(db, payload.refresh_token)
    return StandardResponse(message="Tokens refreshed successfully", data=token_data)

@router.post("/logout", response_model=StandardResponse)
async def logout(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    # We retrieve user_id from token to log it
    try:
        from jose import jwt
        from app.core.config import settings
        claims = jwt.decode(payload.refresh_token, settings.JWT_REFRESH_SECRET, algorithms=[settings.ALGORITHM])
        user_id = int(claims.get("sub"))
        user = await db.get(Login, user_id)
        actor_code = user.computer_code if user else None
    except Exception:
        user_id = None
        actor_code = None

    await auth_service.logout_user(db, payload.refresh_token)
    
    log_audit_event(
        event_type="LOGOUT",
        actor_id=user_id,
        actor_code=actor_code,
        action="User logout successful",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua
    )
    return StandardResponse(message="Logout successful")

@router.post("/logout-all", response_model=StandardResponse)
async def logout_all(
    request: Request,
    current_user: Login = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    await auth_service.logout_all_devices(db, current_user.id)
    
    log_audit_event(
        event_type="LOGOUT_ALL",
        current_user=current_user,
        action="User logged out from all devices",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua
    )
    return StandardResponse(message="Logged out from all devices successfully")

@router.post("/change-password", response_model=StandardResponse)
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: Login = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    await auth_service.change_password(db, current_user, payload.old_password, payload.new_password)
    
    log_audit_event(
        event_type="PASSWORD_CHANGE",
        current_user=current_user,
        action="Password changed successfully",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua
    )
    return StandardResponse(message="Password changed successfully")

@router.post("/forgot-password", response_model=StandardResponse[str])
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    reset_token = await auth_service.forgot_password_simulate(db, payload.username, payload.email)
    return StandardResponse(
        message="Simulated password reset token generated. In production, this would be sent via email.",
        data=reset_token
    )

@router.post("/reset-password", response_model=StandardResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    await auth_service.reset_password(db, payload.token, payload.new_password)
    return StandardResponse(message="Password reset successfully")

@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_me(
    current_user: Login = Depends(get_current_user)
):
    return StandardResponse(message="Profile retrieved successfully", data=UserResponse.model_validate(current_user))

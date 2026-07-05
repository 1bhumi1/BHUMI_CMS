from typing import List
from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.rbac import (
    RoleCreate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    RolePermissionAssign,
    RoleWithPermissionsResponse,
    ImpersonationStartRequest,
    ImpersonationLogResponse,
)
from app.schemas.auth import TokenResponse
from app.schemas.response import StandardResponse
from app.services.rbac import rbac_service
from app.services.auth import auth_service
from app.permissions.evaluator import has_permission
from app.models.auth import Login
from app.models.system import Role, Permission, ImpersonationLog
from app.repositories import role_repo, permission_repo, impersonation_log_repo, login_repo
from app.audit.auditor import log_audit_event
from app.dependencies.auth import get_current_user, oauth2_scheme
from app.security.tokens import decode_access_token

router = APIRouter(prefix="/rbac", tags=["Role-Based Access Control"])

# Role Endpoints
@router.post("/roles", response_model=StandardResponse[RoleResponse])
async def create_role(
    request: Request,
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("role.create"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    role = await role_repo.create(db, obj_in=payload.model_dump())
    
    log_audit_event(
        event_type="ROLE_CREATE",
        current_user=current_user,
        action=f"Created role '{payload.role_type}'",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua
    )
    return StandardResponse(message="Role created successfully", data=RoleResponse.model_validate(role))

@router.get("/roles", response_model=StandardResponse[List[RoleResponse]])
async def list_roles(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("role.read"))
):
    roles = await role_repo.get_multi(db)
    return StandardResponse(data=[RoleResponse.model_validate(r) for r in roles])

# Permission Endpoints
@router.post("/permissions", response_model=StandardResponse[PermissionResponse])
async def create_permission(
    request: Request,
    payload: PermissionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("permission.create"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    permission = await permission_repo.create(db, obj_in=payload.model_dump())
    
    log_audit_event(
        event_type="PERMISSION_CREATE",
        current_user=current_user,
        action=f"Created permission '{payload.permission_name}'",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua
    )
    return StandardResponse(message="Permission created successfully", data=PermissionResponse.model_validate(permission))

@router.get("/permissions", response_model=StandardResponse[List[PermissionResponse]])
async def list_permissions(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("permission.read"))
):
    permissions = await permission_repo.get_multi(db)
    return StandardResponse(data=[PermissionResponse.model_validate(p) for p in permissions])

# Role Permissions Mapping
@router.post("/role-permissions", response_model=StandardResponse[RoleWithPermissionsResponse])
async def assign_role_permissions(
    request: Request,
    payload: RolePermissionAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("role_permission.update"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    role_with_perms = await rbac_service.assign_permissions_to_role(
        db, payload.role_id, payload.permission_ids
    )
    
    log_audit_event(
        event_type="ROLE_PERMISSION_CHANGE",
        current_user=current_user,
        action=f"Updated permissions for role_id {payload.role_id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua
    )
    return StandardResponse(message="Role permissions updated successfully", data=role_with_perms)

# Impersonation Endpoints
@router.post("/impersonate/start", response_model=StandardResponse[TokenResponse])
async def start_impersonation(
    request: Request,
    payload: ImpersonationStartRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("user.impersonate"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    # Resolve the correct login ID using the provided role and ID
    if payload.target_role == "student":
        target_user = await login_repo.get_by_student_id(db, payload.target_user_id)
    elif payload.target_role == "staff":
        target_user = await login_repo.get_by_staff_id(db, payload.target_user_id)
    else:
        raise HTTPException(status_code=400, detail="target_role must be 'student' or 'staff'")

    if not target_user:
        raise HTTPException(status_code=404, detail=f"Target {payload.target_role} not found")

    log_entry = await rbac_service.start_impersonation(
        db, current_user, target_user.id, payload.reason, ip_addr, ua
    )

    additional_claims = {
        "impersonating": True,
        "impersonation_id": log_entry.id,
        "actor_user_id": current_user.id,
        "actor_role": getattr(current_user, 'role_name', 'admin') # Or fetch properly
    }

    token_data = await auth_service.generate_user_tokens(db, target_user, additional_claims)
    
    log_audit_event(
        event_type="IMPERSONATION_START",
        current_user=current_user,
        action=f"Started impersonating user_id {payload.target_user_id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"target_user_id": payload.target_user_id, "reason": payload.reason}
    )
    return StandardResponse(message="Impersonation started successfully", data=token_data)

@router.post("/impersonate/stop", response_model=StandardResponse[TokenResponse])
async def stop_impersonation(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    # Decode token to get impersonation details
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not payload.get("impersonating"):
        raise HTTPException(status_code=400, detail="Not currently impersonating anyone")

    actor_user_id = payload.get("actor_user_id")
    if not actor_user_id:
        raise HTTPException(status_code=400, detail="Invalid impersonation token: missing actor_user_id")
        
    active = await impersonation_log_repo.get_active_impersonation(db, actor_user_id)
    if not active:
        raise HTTPException(status_code=400, detail="No active impersonation session to stop")

    target_id = active.target_user_id
    await rbac_service.end_impersonation(db, actor_user_id)
    
    # Revert back to actor
    actor_user = await login_repo.get(db, actor_user_id)
    if not actor_user:
        raise HTTPException(status_code=404, detail="Original actor not found")

    token_data = await auth_service.generate_user_tokens(db, actor_user)

    log_audit_event(
        event_type="IMPERSONATION_STOP",
        current_user=actor_user,
        action=f"Stopped impersonating user_id {target_id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"target_user_id": target_id}
    )
    return StandardResponse(message="Impersonation stopped successfully", data=token_data)

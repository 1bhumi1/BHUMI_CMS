from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Permission Schemas
class PermissionCreate(BaseModel):
    permission_name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    active: bool = True

class PermissionResponse(BaseModel):
    id: int
    permission_name: str
    description: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True

# Role Schemas
class RoleCreate(BaseModel):
    role_type: str = Field(..., max_length=64)
    active: bool = True

class RoleResponse(BaseModel):
    id: int
    role_type: str
    active: bool

    class Config:
        from_attributes = True

# Role Permissions Mapping
class RolePermissionAssign(BaseModel):
    role_id: int
    permission_ids: List[int]

class RoleWithPermissionsResponse(RoleResponse):
    permissions: List[PermissionResponse] = []

# Impersonation schemas
class ImpersonationStartRequest(BaseModel):
    target_user_id: int
    target_role: str = Field(..., description="student or staff")
    reason: str = Field(..., max_length=255)

class ImpersonationLogResponse(BaseModel):
    id: int
    actor_user_id: int
    target_user_id: int
    actor_role: Optional[str] = None
    target_role: Optional[str] = None
    reason: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True

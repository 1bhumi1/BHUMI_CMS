from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.auth import Login, RefreshToken
from app.models.system import Role
from app.models.student import Student
from app.models.staff import StaffRole
from app.repositories import login_repo, refresh_token_repo, student_repo, staff_repo, role_repo, department_repo, impersonation_log_repo
from app.security.password import verify_password, hash_password
from app.security.tokens import create_access_token, create_refresh_token, decode_refresh_token, decode_access_token
from app.schemas.auth import TokenResponse, UserInfo
from app.core.config import settings

class AuthService:
    async def authenticate_user(self, db: AsyncSession, username: int, password: str) -> Login:
        """
        Authenticate a user by username (computer_code) and password.
        Handles lockouts and failed attempts.
        """
        query = select(Login).where(Login.computer_code == username)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or inactive account"
            )
            
        # Check lockout
        if user.locked_until and user.locked_until > datetime.now():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is temporarily locked due to too many failed attempts"
            )

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now() + timedelta(minutes=15)
            db.add(user)
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
            
        # Reset attempts on success
        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(user)
        return user

    async def generate_user_tokens(self, db: AsyncSession, user: Login, additional_claims: Optional[dict] = None) -> TokenResponse:
        """
        Generate access & refresh tokens, fetch RBAC and return TokenResponse for a given user.
        """
        # Determine Role, Department, and Permissions
        role_name = "Unknown"
        dept_name = "Unknown"
        name = "Unknown"
        permissions = []
        dashboard = "/dashboard"

        if user.student_id:
            student = await student_repo.get(db, user.student_id)
            if student:
                name = f"{student.first_name} {student.last_name}"
                role_name = "Student"
                dept_name = "Student"
                dashboard = "/dashboard/student"
                # Fetch Student role permissions
                q_role = select(Role).options(selectinload(Role.permissions)).where(Role.role_type == "Student")
                r_res = await db.execute(q_role)
                r_obj = r_res.scalars().first()
                if r_obj:
                    permissions = [p.permission_name for p in r_obj.permissions]

        elif user.staff_id:
            staff = await staff_repo.get(db, user.staff_id)
            if staff:
                name = f"{staff.first_name} {staff.last_name}"
                # Get role from staff_role
                q_srole = select(StaffRole).options(
                    selectinload(StaffRole.role).selectinload(Role.permissions),
                    selectinload(StaffRole.department)
                ).where(StaffRole.staff_id == staff.id).order_by(StaffRole.id.desc())
                srole_res = await db.execute(q_srole)
                staff_role = srole_res.scalars().first()
                if staff_role and staff_role.role:
                    role_name = staff_role.role.role_type
                    permissions = [p.permission_name for p in staff_role.role.permissions]
                    if staff_role.department:
                        dept_name = staff_role.department.name
                        
                    # Map dashboard
                    if role_name == "Admin":
                        dashboard = "/dashboard/admin"
                    else:
                        dashboard = "/dashboard/staff"
        elif user.computer_code.startswith("PAR"):
            name = "Parent"
            role_name = "Parent"
            dashboard = "/dashboard/parent"
            q_role = select(Role).options(selectinload(Role.permissions)).where(Role.role_type == "Parent")
            r_res = await db.execute(q_role)
            r_obj = r_res.scalars().first()
            if r_obj:
                permissions = [p.permission_name for p in r_obj.permissions]
            
        # Update last login time
        user.last_login = datetime.now()
        db.add(user)
        await db.flush()

        # Generate tokens
        access_token = create_access_token(user_id=user.id, computer_code=user.computer_code, additional_claims=additional_claims)
        refresh_token = create_refresh_token(user_id=user.id, additional_claims=additional_claims)
        
        token_hash = hash_password(refresh_token)
        expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        await refresh_token_repo.create(db, obj_in={
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": expires_at
        })
        
        user_info = UserInfo(
            id=user.id,
            name=name,
            computer_code=user.computer_code,
            role=role_name,
            department=dept_name
        )

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user=user_info,
            permissions=permissions,
            dashboard=dashboard
        )

    async def login_user(self, db: AsyncSession, username: int, password: str) -> TokenResponse:
        """
        Authenticate, generate access & refresh tokens, fetch RBAC and return TokenResponse.
        """
        user = await self.authenticate_user(db, username, password)
        return await self.generate_user_tokens(db, user)

    async def refresh_tokens(self, db: AsyncSession, refresh_token_str: str) -> TokenResponse:
        """
        Perform refresh token rotation
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = decode_refresh_token(refresh_token_str)
            user_id_str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
            user_id = int(user_id_str)
            
            is_impersonating = payload.get("impersonating")
            impersonation_id = payload.get("impersonation_id")
            actor_user_id = payload.get("actor_user_id")
            actor_role = payload.get("actor_role")
        except Exception:
            raise credentials_exception

        query = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await db.execute(query)
        db_tokens = result.scalars().all()
        
        matched_token: Optional[RefreshToken] = None
        for db_token in db_tokens:
            if db_token.expires_at > datetime.now():
                if verify_password(refresh_token_str, db_token.token_hash):
                    matched_token = db_token
                    break
                    
        if not matched_token:
            raise credentials_exception

        await db.delete(matched_token)
        await db.flush()

        user = await login_repo.get(db, user_id)
        if not user or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found"
            )

        additional_claims = None
        if is_impersonating and actor_user_id:
            active = await impersonation_log_repo.get_active_impersonation(db, actor_user_id)
            if active and active.id == impersonation_id and active.target_user_id == user_id:
                additional_claims = {
                    "impersonating": True,
                    "impersonation_id": impersonation_id,
                    "actor_user_id": actor_user_id,
                    "actor_role": actor_role
                }

        new_access_token = create_access_token(user_id=user.id, computer_code=user.computer_code, additional_claims=additional_claims)
        new_refresh_token = create_refresh_token(user_id=user.id, additional_claims=additional_claims)
        
        new_token_hash = hash_password(new_refresh_token)
        new_expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        await refresh_token_repo.create(db, obj_in={
            "user_id": user.id,
            "token_hash": new_token_hash,
            "expires_at": new_expires_at
        })
        
        role_name = "Unknown"
        dept_name = "Unknown"
        name = "Unknown"
        permissions = []
        dashboard = "/dashboard"

        if user.student_id:
            student = await student_repo.get(db, user.student_id)
            if student:
                name = f"{student.first_name} {student.last_name}"
                role_name = "Student"
                dept_name = "Student"
                dashboard = "/dashboard/student"
                q_role = select(Role).options(selectinload(Role.permissions)).where(Role.role_type == "Student")
                r_res = await db.execute(q_role)
                r_obj = r_res.scalars().first()
                if r_obj:
                    permissions = [p.permission_name for p in r_obj.permissions]
        elif user.staff_id:
            staff = await staff_repo.get(db, user.staff_id)
            if staff:
                name = f"{staff.first_name} {staff.last_name}"
                q_srole = select(StaffRole).options(
                    selectinload(StaffRole.role).selectinload(Role.permissions),
                    selectinload(StaffRole.department)
                ).where(StaffRole.staff_id == staff.id).order_by(StaffRole.id.desc())
                srole_res = await db.execute(q_srole)
                staff_role = srole_res.scalars().first()
                if staff_role and staff_role.role:
                    role_name = staff_role.role.role_type
                    permissions = [p.permission_name for p in staff_role.role.permissions]
                    if staff_role.department:
                        dept_name = staff_role.department.name
                    if role_name == "Admin":
                        dashboard = "/dashboard/admin"
                    else:
                        dashboard = "/dashboard/staff"
        elif user.computer_code.startswith("PAR"):
            name = "Parent"
            role_name = "Parent"
            dashboard = "/dashboard/parent"
            q_role = select(Role).options(selectinload(Role.permissions)).where(Role.role_type == "Parent")
            r_res = await db.execute(q_role)
            r_obj = r_res.scalars().first()
            if r_obj:
                permissions = [p.permission_name for p in r_obj.permissions]
                    
        user_info = UserInfo(
            id=user.id,
            name=name,
            computer_code=user.computer_code,
            role=role_name,
            department=dept_name
        )
        
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
            user=user_info,
            permissions=permissions,
            dashboard=dashboard
        )

    async def logout_user(self, db: AsyncSession, refresh_token_str: str) -> None:
        try:
            payload = decode_refresh_token(refresh_token_str)
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        query = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await db.execute(query)
        db_tokens = result.scalars().all()
        
        for db_token in db_tokens:
            if verify_password(refresh_token_str, db_token.token_hash):
                await db.delete(db_token)
                break

    async def logout_all_devices(self, db: AsyncSession, user_id: int) -> None:
        await refresh_token_repo.delete_by_user_id(db, user_id)

    async def change_password(self, db: AsyncSession, user: Login, old_password: str, new_password: str) -> None:
        if user.student_id is not None:
            raise HTTPException(status_code=403, detail="Students are not permitted to change their password.")

        if not verify_password(old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect old password")
            
        user.password_hash = hash_password(new_password)
        user.is_first_login = False
        user.password_changed_at = datetime.now()
        db.add(user)
        
        # Invalidate all refresh tokens after password change
        await refresh_token_repo.delete_by_user_id(db, user.id)

    async def forgot_password_simulate(self, db: AsyncSession, username: int, email: str) -> str:
        query = select(Login).where(Login.computer_code == username)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Username not found")
            
        if user.student_id is not None:
            raise HTTPException(status_code=403, detail="Students are not permitted to use the forgot password feature.")

        matched = False
        if user.student_id:
            student = await student_repo.get(db, user.student_id)
            if student and student.email == email:
                matched = True
        elif user.staff_id:
            staff = await staff_repo.get(db, user.staff_id)
            if staff and staff.email == email:
                matched = True
                
        if not matched:
            raise HTTPException(status_code=400, detail="Email does not match our records for this user")
            
        reset_token = create_access_token(user_id=user.id, computer_code=user.computer_code, additional_claims={"type": "reset"})
        return reset_token

    async def reset_password(self, db: AsyncSession, reset_token: str, new_password: str) -> None:
        try:
            payload = decode_access_token(reset_token)
            if payload.get("type") != "reset":
                raise ValueError("Invalid token scope")
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
            
        user = await login_repo.get(db, user_id)
        if not user or not user.active:
            raise HTTPException(status_code=400, detail="User account is inactive or not found")
            
        user.password_hash = hash_password(new_password)
        user.is_first_login = False
        user.password_changed_at = datetime.now()
        db.add(user)
        await refresh_token_repo.delete_by_user_id(db, user.id)

auth_service = AuthService()

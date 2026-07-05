from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.staff import Staff, StaffDetails, StaffRole
from app.models.auth import Login
from app.repositories import staff_repo, staff_details_repo, staff_role_repo, login_repo, refresh_token_repo, role_repo, department_repo
from app.schemas.staff import (
    CompositeStaffCreate,
    StaffUpdate,
    StaffProfileResponse,
    StaffResponse,
    StaffDetailsResponse,
    StaffRoleResponse,
    StaffRoleCreate,
    StaffListResponse,
)
from app.security.password import hash_password

class StaffService:
    async def get_staff_profile(self, db: AsyncSession, staff_id: int) -> StaffProfileResponse:
        """
        Fetch complete staff profile including details and roles.
        """
        staff = await staff_repo.get(db, staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        # Fetch detail and roles
        details = await staff_details_repo.get_by_staff_id(db, staff_id)
        roles = await staff_role_repo.get_multi(db, filters={"staff_id": staff_id})

        return StaffProfileResponse(
            staff=StaffResponse.model_validate(staff),
            details=StaffDetailsResponse.model_validate(details) if details else None,
            roles=[StaffRoleResponse.model_validate(r) for r in roles]
        )

    async def list_staff(
        self,
        db: AsyncSession,
        *,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = "id",
        sort_order: str = "asc",
        filters: Optional[Dict[str, Any]] = None,
    ) -> StaffListResponse:
        """
        List staff with search, filtering, sorting, and pagination.
        Returns items and total count for frontend pagination.
        """
        items = await staff_repo.search_staff(
            db, search=search, skip=skip, limit=limit,
            sort_by=sort_by, sort_order=sort_order, filters=filters
        )
        total = await staff_repo.count_staff(
            db, search=search, filters=filters
        )
        return StaffListResponse(
            items=[StaffResponse.model_validate(s) for s in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def create_staff(self, db: AsyncSession, payload: CompositeStaffCreate) -> StaffProfileResponse:
        """
        Create staff member, nested qualifications/details, assign initial roles, and provision credentials.
        """
        comp_code_int = payload.staff.computer_code

        # Check if staff with code or email exists
        existing_code = await staff_repo.get_by_computer_code(db, payload.staff.computer_code)
        if existing_code:
            raise HTTPException(status_code=400, detail="Staff with this computer code already exists")

        if payload.staff.email:
            existing_email = await staff_repo.get_by_email(db, payload.staff.email)
            if existing_email:
                raise HTTPException(status_code=409, detail="Staff with this email already exists")

        # Check duplicate aadhar
        existing_aadhar = await staff_repo.get_by_aadhar(db, payload.staff.aadhar_number)
        if existing_aadhar:
            raise HTTPException(status_code=409, detail="Staff with this Aadhar number already exists")

        # Validate role and department
        role = await role_repo.get(db, payload.staff.role_id)
        if not role or not role.active:
            raise HTTPException(status_code=400, detail="Invalid or inactive role selected")
            
        dept = await department_repo.get(db, payload.staff.department_id)
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department selected")

        # 1. Create Staff
        staff_data = payload.staff.model_dump(exclude={"role_id", "department_id", "academic_session_id", "academic_term_id", "start_date", "end_date"})
        staff = await staff_repo.create(db, obj_in=staff_data)
        await db.flush()

        # 2. Create Login credentials
        default_pwd = "12345"
        if payload.staff.date_of_birth:
            default_pwd = payload.staff.date_of_birth.strftime("%d%m%Y")

        password_hash = hash_password(default_pwd)
        await login_repo.create(db, obj_in={
            "computer_code": comp_code_int,
            "password_hash": password_hash,
            "staff_id": staff.id,
            "active": True
        })

        # 3. Create Staff Details (Unconditionally)
        details_data = payload.details.model_dump() if payload.details else {}
        details_data["staff_id"] = staff.id
        if not details_data.get("designation_id") and role:
            from app.models.staff import Designation
            from sqlalchemy import func
            res_desig = await db.execute(
                select(Designation).where(func.lower(Designation.designation) == func.lower(role.role_type))
            )
            desig_obj = res_desig.scalar()
            if desig_obj:
                details_data["designation_id"] = desig_obj.id
        created_details = await staff_details_repo.create(db, obj_in=details_data)

        # 4. Assign Initial Role from StaffCreate
        initial_role_data = {
            "staff_id": staff.id,
            "role_id": payload.staff.role_id,
            "department_id": payload.staff.department_id,
            "academic_session_id": payload.staff.academic_session_id,
            "academic_term_id": payload.staff.academic_term_id,
            "start_date": payload.staff.start_date,
            "end_date": payload.staff.end_date,
        }
        role_record = await staff_role_repo.create(db, obj_in=initial_role_data)
        created_roles = [role_record]

        # Handle any additional roles if provided
        for role_in in payload.roles:
            role_data = role_in.model_dump()
            role_data["staff_id"] = staff.id
            if role_data["role_id"] == payload.staff.role_id and role_data["department_id"] == payload.staff.department_id:
                continue # Already assigned
            # Check unique constraint staff_id + role_id + department_id
            existing_role = await staff_role_repo.get_by_staff_and_role(
                db, staff.id, role_data["role_id"], role_data["department_id"]
            )
            if not existing_role:
                add_role_record = await staff_role_repo.create(db, obj_in=role_data)
                created_roles.append(add_role_record)

        await db.flush()

        return StaffProfileResponse(
            staff=StaffResponse.model_validate(staff),
            details=StaffDetailsResponse.model_validate(created_details) if created_details else None,
            roles=[StaffRoleResponse.model_validate(r) for r in created_roles]
        )

    async def update_staff(self, db: AsyncSession, staff_id: int, payload: StaffUpdate) -> StaffResponse:
        """
        Update basic staff details.
        """
        staff = await staff_repo.get(db, staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        update_data = payload.model_dump(exclude_unset=True)
        
        # Extract details data if nested
        details_update_data = update_data.pop("details", None)
        
        # Check aadhar uniqueness if being updated
        if "aadhar_number" in update_data and update_data["aadhar_number"] is not None:
            existing_aadhar = await staff_repo.get_by_aadhar(db, update_data["aadhar_number"])
            if existing_aadhar and existing_aadhar.id != staff_id:
                raise HTTPException(status_code=409, detail="Another staff member already has this Aadhar number")

        # Check email uniqueness if being updated
        if "email" in update_data and update_data["email"] is not None:
            existing_email = await staff_repo.get_by_email(db, update_data["email"])
            if existing_email and existing_email.id != staff_id:
                raise HTTPException(status_code=409, detail="Another staff member already has this email")

        updated_staff = await staff_repo.update(db, db_obj=staff, obj_in=update_data)

        # Handle role update if provided
        role_update_keys = ["role_id", "department_id", "academic_session_id", "academic_term_id", "start_date", "end_date"]
        role_update_provided = {k: update_data.pop(k) for k in role_update_keys if k in update_data}

        if role_update_provided:
            # We assume updating the primary (most recent) role for simplicity
            roles = await staff_role_repo.get_multi(db, filters={"staff_id": staff_id})
            if roles:
                # Update the first/primary role
                primary_role = roles[0]
                role_update = {}
                if "role_id" in role_update_provided:
                    new_role_id = role_update_provided["role_id"]
                    role_obj = await role_repo.get(db, new_role_id)
                    if not role_obj or not role_obj.active:
                        raise HTTPException(status_code=400, detail="Invalid or inactive role selected")
                    role_update["role_id"] = new_role_id
                
                if "department_id" in role_update_provided:
                    new_dept_id = role_update_provided["department_id"]
                    dept_obj = await department_repo.get(db, new_dept_id)
                    if not dept_obj:
                        raise HTTPException(status_code=400, detail="Invalid department selected")
                    role_update["department_id"] = new_dept_id
                
                for k in ["academic_session_id", "academic_term_id", "start_date", "end_date"]:
                    if k in role_update_provided:
                        role_update[k] = role_update_provided[k]

                if role_update:
                    await staff_role_repo.update(db, db_obj=primary_role, obj_in=role_update)
            else:
                # Create a new role mapping if none exists but required fields are provided
                if "role_id" in role_update_provided and "department_id" in role_update_provided:
                    new_role_id = role_update_provided["role_id"]
                    new_dept_id = role_update_provided["department_id"]
                    role_obj = await role_repo.get(db, new_role_id)
                    dept_obj = await department_repo.get(db, new_dept_id)
                    if not role_obj or not role_obj.active or not dept_obj:
                        raise HTTPException(status_code=400, detail="Invalid role or department")
                    
                    create_role_data = {
                        "staff_id": staff_id,
                        "role_id": new_role_id,
                        "department_id": new_dept_id
                    }
                    for k in ["academic_session_id", "academic_term_id", "start_date", "end_date"]:
                        if k in role_update_provided:
                            create_role_data[k] = role_update_provided[k]
                    await staff_role_repo.create(db, obj_in=create_role_data)
                else:
                    raise HTTPException(status_code=400, detail="Both role and department must be provided to create a new mapping")

        # Handle active state change
        if "active" in update_data:
            login = await login_repo.get_by_staff_id(db, staff_id)
            if login:
                login.active = update_data["active"]
                db.add(login)

        # Handle StaffDetails update or create if missing
        if details_update_data:
            existing_details = await staff_details_repo.get_by_staff_id(db, staff_id)
            if existing_details:
                await staff_details_repo.update(db, db_obj=existing_details, obj_in=details_update_data)
            else:
                details_update_data["staff_id"] = staff_id
                await staff_details_repo.create(db, obj_in=details_update_data)

        await db.flush()

        return StaffResponse.model_validate(updated_staff)

    async def delete_staff(self, db: AsyncSession, staff_id: int) -> None:
        """
        Soft delete staff and login.
        """
        staff = await staff_repo.get(db, staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        staff.active = False
        db.add(staff)

        login = await login_repo.get_by_staff_id(db, staff_id)
        if login:
            login.active = False
            db.add(login)
            await refresh_token_repo.delete_by_user_id(db, login.id)

    async def assign_staff_role(self, db: AsyncSession, role_in: StaffRoleCreate) -> StaffRoleResponse:
        """
        Assign an administrative role to a staff member.
        """
        staff = await staff_repo.get(db, role_in.staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        # Check unique constraint staff_id + role_id + department_id
        existing = await staff_role_repo.get_by_staff_and_role(
            db, role_in.staff_id, role_in.role_id, role_in.department_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="This role is already assigned to the staff in this department")

        role_record = await staff_role_repo.create(db, obj_in=role_in.model_dump())
        return StaffRoleResponse.model_validate(role_record)

    async def revoke_staff_role(self, db: AsyncSession, staff_role_id: int) -> None:
        """
        Revoke an administrative role from a staff member.
        """
        await staff_role_repo.remove(db, id=staff_role_id)

from app.schemas.staff import StaffRoleCreate
staff_service = StaffService()

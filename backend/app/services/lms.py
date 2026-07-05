import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

def _extract_faculty_code(computer_code: str) -> int:
    try:
        return int(computer_code)
    except ValueError:
        match = re.search(r'\d+', computer_code)
        if match:
            return int(match.group())
        raise ValueError(f"Cannot extract integer faculty code from {computer_code}")

from app.schemas.lms import (
    LeaveCreate, LeaveUpdate, LeaveApproval,
    LeaveLimitCreate, LeaveLimitUpdate, FacultyAssignmentCreate
)
from app.models.lms import LMSAssignFaculty, LMSApplyDetails
from app.repositories.lms import (
    lms_apply_details_repo, lms_apply_limit_repo,
    lms_assign_faculty_repo, lms_staff_record_repo
)
from app.repositories import staff_repo
from app.audit.auditor import log_audit_event

class LMSService:
    @staticmethod
    async def apply_leave(db: AsyncSession, leave_in: LeaveCreate, current_user: Any, request: Any) -> Any:
        faculty_code = _extract_faculty_code(current_user.computer_code)
        
        from app.models.academic import AcademicSession
        from sqlalchemy import select
        
        query = select(AcademicSession).where(AcademicSession.is_active == True)
        result = await db.execute(query)
        active_session = result.scalars().first()
        
        session_str = active_session.session_name if active_session else (leave_in.session or "2023-24")
        leave_in.session = session_str
        
        # Validate apply limit
        from app.models.lms import LMSApplyLimit
        limit_query = select(LMSApplyLimit).where(LMSApplyLimit.leave_type == leave_in.leave_type, LMSApplyLimit.active == 1)
        limit_result = await db.execute(limit_query)
        apply_limit = limit_result.scalars().first()
        
        if apply_limit:
            today = datetime.now().date()
            if isinstance(leave_in.start_date, str):
                start_date_obj = datetime.strptime(leave_in.start_date, '%Y-%m-%d').date()
            else:
                start_date_obj = leave_in.start_date
                
            delta_days = (start_date_obj - today).days
            
            if delta_days < apply_limit.days:
                if apply_limit.days < 0:
                    raise HTTPException(status_code=400, detail=f"Cannot apply for {leave_in.leave_type}. You can only apply up to {abs(apply_limit.days)} days after taking the leave.")
                else:
                    raise HTTPException(status_code=400, detail=f"Cannot apply for {leave_in.leave_type}. You must apply at least {apply_limit.days} days in advance.")
        
        # Validate balance
        staff_record = await lms_staff_record_repo.get_by_faculty_session(db, faculty_code, int(leave_in.session.split('-')[0]))
        if not staff_record:
            # Auto-create a default record for testing/smooth integration
            staff_record = await lms_staff_record_repo.create(
                db,
                obj_in={
                    "faculty_computer_code": faculty_code,
                    "academic_session": int(leave_in.session.split('-')[0]),
                    "cl": 10.0,
                    "ml": 10.0,
                    "el": 10.0
                }
            )

        balance = getattr(staff_record, leave_in.leave_type.lower(), 0.0)
        if balance < leave_in.days:
            raise HTTPException(status_code=400, detail=f"Insufficient {leave_in.leave_type} balance")
            
        # Deduct balance immediately upon application
        new_balance = max(0, balance - leave_in.days)
        await lms_staff_record_repo.update(db, db_obj=staff_record, obj_in={leave_in.leave_type.lower(): new_balance})

        apply_id = uuid.uuid4().hex

        new_leave = await lms_apply_details_repo.create(
            db,
            obj_in={
                "apply_id": apply_id,
                "apply_date": datetime.now().date(),
                "faculty_computer_code": faculty_code,
                "session": leave_in.session,
                "start_date": leave_in.start_date,
                "end_date": leave_in.end_date,
                "days": leave_in.days,
                "pre_balance": balance,
                "leave_type": leave_in.leave_type,
                "reason": leave_in.reason,
                "hod_approval": 0,
                "principal_approval": 0
            }
        )

        if hasattr(leave_in, 'assignments') and leave_in.assignments:
            for assign in leave_in.assignments:
                await lms_assign_faculty_repo.create(
                    db,
                    obj_in={
                        "apply_id": apply_id,
                        "faculty_date": assign.faculty_date,
                        "faculty_computer_code": assign.faculty_computer_code,
                        "assigned_class_dept": assign.assigned_class_dept,
                        "assigned_section": assign.assigned_section,
                        "lecture_type": assign.lecture_type,
                        "start_time": assign.start_time,
                        "end_time": assign.end_time,
                        "other_responsibility": assign.other_responsibility,
                        "status": 0
                    }
                )

        log_audit_event(
            event_type="LMS",
            action="Leave Applied",
            status="SUCCESS",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            current_user=current_user,
            details={"apply_id": apply_id, "days": leave_in.days, "type": leave_in.leave_type}
        )
        return new_leave

    @staticmethod
    async def get_my_leaves(db: AsyncSession, current_user: Any, skip: int = 0, limit: int = 100) -> List[Any]:
        faculty_code = _extract_faculty_code(current_user.computer_code)
        leaves = await lms_apply_details_repo.get_multi(
            db, skip=skip, limit=limit, filters={"faculty_computer_code": faculty_code}, sort_by="apply_date", sort_order="desc"
        )
        return leaves

    @staticmethod
    async def get_pending_leaves(db: AsyncSession, skip: int = 0, limit: int = 100, is_principal: bool = False, is_hod: bool = False, current_user: Any = None) -> List[Any]:
        leaves_result = []
        faculty_code = _extract_faculty_code(current_user.computer_code) if current_user else None

        # 1. Substitute Approvals (for the current user)
        if faculty_code:
            query = select(LMSAssignFaculty).where(
                LMSAssignFaculty.faculty_computer_code == faculty_code,
                LMSAssignFaculty.status == 0
            )
            sub_result = await db.execute(query)
            sub_assigns = sub_result.scalars().all()
            for sa in sub_assigns:
                leave = await lms_apply_details_repo.get_by_apply_id(db, sa.apply_id)
                if leave:
                    # Don't show leave if it's already rejected or processed completely by someone else
                    setattr(leave, "required_action", "SUBSTITUTE")
                    leaves_result.append(leave)

        # 2. HOD Approvals
        if is_hod:
            hod_leaves = await lms_apply_details_repo.get_multi(
                db, skip=skip, limit=limit, filters={"hod_approval": 0}, sort_by="apply_date", sort_order="desc"
            )
            # Filter out leaves that still have pending substitute approvals
            for hl in hod_leaves:
                q = select(LMSAssignFaculty).where(LMSAssignFaculty.apply_id == hl.apply_id, LMSAssignFaculty.status == 0)
                res = await db.execute(q)
                pending_subs = res.scalars().all()
                if pending_subs:
                    setattr(hl, "required_action", "WAITING_ON_SUBSTITUTE")
                else:
                    setattr(hl, "required_action", "HOD")
                
                if not any(l.apply_id == hl.apply_id for l in leaves_result):
                    leaves_result.append(hl)

        # 3. Principal Approvals
        if is_principal:
            principal_leaves = await lms_apply_details_repo.get_multi(
                db, skip=skip, limit=limit, filters={"hod_approval": 1, "principal_approval": 0}, sort_by="apply_date", sort_order="desc"
            )
            for pl in principal_leaves:
                setattr(pl, "required_action", "PRINCIPAL")
                if not any(l.apply_id == pl.apply_id for l in leaves_result):
                    leaves_result.append(pl)

        # Attach faculty names and assignments
        for leave in leaves_result:
            staff = await staff_repo.get_by_computer_code(db, leave.faculty_computer_code)
            if staff:
                setattr(leave, "faculty_name", f"{staff.first_name} {staff.last_name}")
            else:
                setattr(leave, "faculty_name", "Unknown Faculty")

            # Fetch assignments for this leave
            q = select(LMSAssignFaculty).where(LMSAssignFaculty.apply_id == leave.apply_id)
            res = await db.execute(q)
            assignments = res.scalars().all()
            setattr(leave, "assignments", assignments)

        return leaves_result

    @staticmethod
    async def approve_leave(db: AsyncSession, apply_id: str, approval_in: LeaveApproval, current_user: Any, request: Any, action_type: str = "HOD") -> Any:
        faculty_code = _extract_faculty_code(current_user.computer_code)

        if action_type == "SUBSTITUTE":
            # Update lms_assign_faculty
            q = select(LMSAssignFaculty).where(
                LMSAssignFaculty.apply_id == apply_id,
                LMSAssignFaculty.faculty_computer_code == faculty_code
            )
            res = await db.execute(q)
            assignment = res.scalars().first()
            if not assignment:
                raise HTTPException(status_code=404, detail="Substitute assignment not found")
            
            await lms_assign_faculty_repo.update(db, db_obj=assignment, obj_in={"status": approval_in.status})
            
            leave = await lms_apply_details_repo.get_by_apply_id(db, apply_id)
            if approval_in.status == 2:
                # If substitute rejects, reject the whole leave and restore balance
                await lms_apply_details_repo.update(db, db_obj=leave, obj_in={"hod_approval": 2, "principal_approval": 2})
                session_start = int(leave.session.split('-')[0])
                staff_record = await lms_staff_record_repo.get_by_faculty_session(db, leave.faculty_computer_code, session_start)
                if staff_record:
                    current_bal = getattr(staff_record, leave.leave_type.lower(), 0.0)
                    await lms_staff_record_repo.update(db, db_obj=staff_record, obj_in={leave.leave_type.lower(): current_bal + leave.days})

            setattr(leave, "required_action", "SUBSTITUTE")
            return leave

        leave = await lms_apply_details_repo.get_by_apply_id(db, apply_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave not found")

        update_data = {}
        if action_type == "PRINCIPAL":
            update_data["principal_approval"] = approval_in.status
        elif action_type == "HOD":
            update_data["hod_approval"] = approval_in.status

        updated_leave = await lms_apply_details_repo.update(db, db_obj=leave, obj_in=update_data)

        # Restore balance if rejected by HOD or Principal
        if approval_in.status == 2:
            session_start = int(leave.session.split('-')[0])
            staff_record = await lms_staff_record_repo.get_by_faculty_session(db, leave.faculty_computer_code, session_start)
            if staff_record:
                current_bal = getattr(staff_record, leave.leave_type.lower(), 0.0)
                await lms_staff_record_repo.update(db, db_obj=staff_record, obj_in={leave.leave_type.lower(): current_bal + leave.days})

        action_name = f"Leave {approval_in.status} by {action_type}"
        log_audit_event(
            event_type="LMS",
            action=action_name,
            status="SUCCESS",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            current_user=current_user,
            details={"apply_id": apply_id, "action_type": action_type}
        )
        setattr(updated_leave, "required_action", action_type)
        return updated_leave

    @staticmethod
    async def get_leave_balance(db: AsyncSession, faculty_code: int, session: int) -> Any:
        record = await lms_staff_record_repo.get_by_faculty_session(db, faculty_code, session)
        if not record:
            # Auto-create a default record for testing/smooth integration
            record = await lms_staff_record_repo.create(
                db,
                obj_in={
                    "faculty_computer_code": faculty_code,
                    "academic_session": session,
                    "cl": 10.0,
                    "ml": 10.0,
                    "el": 10.0
                }
            )
        return record

    @staticmethod
    async def assign_faculty(db: AsyncSession, assign_in: FacultyAssignmentCreate, current_user: Any, request: Any) -> Any:
        new_assign = await lms_assign_faculty_repo.create(db, obj_in=assign_in.model_dump())
        log_audit_event(
            event_type="LMS",
            action="Faculty Assigned",
            status="SUCCESS",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            current_user=current_user,
            details={"apply_id": assign_in.apply_id, "substitute_code": assign_in.faculty_computer_code}
        )
        return new_assign

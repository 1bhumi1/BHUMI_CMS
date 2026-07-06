import os
import json
import logging
from typing import Optional
from sqlalchemy import select
from app.mcp.database import get_mcp_db
from app.services.lms import LMSService
from app.models.lms import LMSApplyDetails, LMSApplyLimit, LMSAssignFaculty
from app.repositories import staff_repo

logger = logging.getLogger(__name__)

class MockLMSUser:
    def __init__(self, computer_code: str, staff_id: Optional[int] = None):
        self.computer_code = computer_code
        self.staff_id = staff_id

def get_leave_status_label(hod_val: int, principal_val: int) -> str:
    if principal_val == 1:
        return "Approved"
    elif principal_val == 2:
        return "Rejected by Principal"
    elif hod_val == 1:
        return "Pending Principal Approval"
    elif hod_val == 2:
        return "Rejected by HOD"
    return "Pending HOD Approval"

def register_leave_tools(mcp):
    @mcp.tool()
    async def get_pending_leaves(skip: int = 0, limit: int = 100) -> str:
        """
        Get all pending leave requests. Access restricted by role.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_code = os.environ.get("CALLER_CODE", "-1")
        
        async with get_mcp_db() as db:
            try:
                # Resolve staff_id
                staff = await staff_repo.get_by_computer_code(db, caller_code)
                staff_id = staff.id if staff else None
                user = MockLMSUser(caller_code, staff_id)
                
                is_principal = (caller_role == "Principal")
                is_hod = (caller_role == "HOD")
                
                leaves = await LMSService.get_pending_leaves(
                    db, skip=skip, limit=limit,
                    is_principal=is_principal, is_hod=is_hod,
                    current_user=user
                )
                if not leaves:
                    return "No records found."
                return json.dumps(leaves, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_approved_leaves(skip: int = 0, limit: int = 100) -> str:
        """
        Get approved leave requests for the caller or institution.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_code = os.environ.get("CALLER_CODE", "-1")
        
        async with get_mcp_db() as db:
            try:
                staff = await staff_repo.get_by_computer_code(db, caller_code)
                staff_id = staff.id if staff else None
                user = MockLMSUser(caller_code, staff_id)
                
                if caller_role == "Faculty":
                    # Faculty can only view their own leaves
                    leaves = await LMSService.get_my_leaves(db, user, skip=skip, limit=limit)
                else:
                    # HOD/Principal can list overall approved leaves (where principal_approval == 1)
                    stmt = select(LMSApplyDetails).where(LMSApplyDetails.principal_approval == 1).offset(skip).limit(limit)
                    res = await db.execute(stmt)
                    leaves = res.scalars().all()
                    leaves = [{
                        "apply_id": l.apply_id,
                        "faculty_code": l.faculty_computer_code,
                        "leave_type": l.leave_type,
                        "start_date": l.start_date,
                        "end_date": l.end_date,
                        "status": "Approved"
                    } for l in leaves]
                    
                if not leaves:
                    return "No records found."
                return json.dumps(leaves, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_leave_balance(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get the current leave balance for a faculty member.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_code = int(os.environ.get("CALLER_CODE", "-1"))
        
        if caller_role == "Faculty" and caller_code != faculty_computer_code:
            return "Permission Denied: You cannot view another faculty's leave balance."
            
        async with get_mcp_db() as db:
            try:
                balance = await LMSService.get_leave_balance(db, faculty_computer_code, academic_session)
                if not balance:
                    return "No records found."
                return json.dumps(balance, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_leave_details(apply_id: str) -> str:
        """
        Fetch details of a specific leave request using apply_id.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(LMSApplyDetails).where(LMSApplyDetails.apply_id == apply_id)
                res = await db.execute(stmt)
                leave = res.scalars().first()
                if not leave:
                    return "No records found."
                return json.dumps({
                    "apply_id": leave.apply_id,
                    "faculty_code": leave.faculty_computer_code,
                    "leave_type": leave.leave_type,
                    "start_date": leave.start_date,
                    "end_date": leave.end_date,
                    "reason": leave.reason,
                    "status": get_leave_status_label(leave.hod_approval, leave.principal_approval)
                }, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_leave_limits() -> str:
        """
        Fetch leave application limits and criteria configurations.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(LMSApplyLimit)
                res = await db.execute(stmt)
                limits = res.scalars().all()
                if not limits:
                    return "No records found."
                return json.dumps([{
                    "leave_type": l.leave_type,
                    "days": l.days,
                    "active": l.active
                } for l in limits])
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_assigned_leave_faculties(apply_id: str) -> str:
        """
        Fetch faculty assignments for substitute teaching during a leave.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(LMSAssignFaculty).where(LMSAssignFaculty.apply_id == apply_id)
                res = await db.execute(stmt)
                assignments = res.scalars().all()
                if not assignments:
                    return "No records found."
                return json.dumps([{
                    "assign_faculty_id": a.assign_faculty_id,
                    "apply_id": a.apply_id,
                    "assigned_faculty_code": a.faculty_computer_code,
                    "status": a.status
                } for a in assignments], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

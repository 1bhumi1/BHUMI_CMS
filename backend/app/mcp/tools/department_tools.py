import json
import logging
from sqlalchemy import select
from app.mcp.database import get_mcp_db
from app.models.academic import Department

logger = logging.getLogger(__name__)

def register_department_tools(mcp):
    @mcp.tool()
    async def get_all_departments() -> str:
        """
        Fetch all active academic departments in the institution.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Department)
                res = await db.execute(stmt)
                depts = res.scalars().all()
                if not depts:
                    return "No records found."
                return json.dumps([{
                    "id": d.id,
                    "name": d.name,
                    "code": d.dept_code
                } for d in depts])
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_department_details(department_id: int) -> str:
        """
        Fetch details of a department including code, name, and size metrics.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Department).where(Department.id == department_id)
                res = await db.execute(stmt)
                dept = res.scalars().first()
                if not dept:
                    return "No records found."
                return json.dumps({
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.dept_code,
                    "have_student": dept.have_student,
                    "have_staff": dept.have_staff,
                    "active": dept.active
                })
            except Exception as e:
                return json.dumps({"error": str(e)})

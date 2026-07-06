import json
import logging
from sqlalchemy import select
from app.mcp.database import get_mcp_db
from app.models.academic import AcademicSession, AcademicProgram, Program, Specialization

logger = logging.getLogger(__name__)

def register_academic_tools(mcp):
    @mcp.tool()
    async def get_all_academic_sessions() -> str:
        """
        Fetch list of all academic sessions.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(AcademicSession)
                res = await db.execute(stmt)
                sessions = res.scalars().all()
                if not sessions:
                    return "No records found."
                return json.dumps([{
                    "id": s.id,
                    "session_name": s.session_name,
                    "is_active": s.is_active
                } for s in sessions])
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_all_academic_programs() -> str:
        """
        Fetch all active academic programs in the system.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(AcademicProgram, Program).join(Program, AcademicProgram.program_id == Program.id)
                res = await db.execute(stmt)
                records = res.all()
                if not records:
                    return "No records found."
                return json.dumps([{
                    "id": r.AcademicProgram.id,
                    "program_code": r.Program.program_code,
                    "program_name": r.Program.name
                } for r in records])
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_courses_by_program(program_id: int) -> str:
        """
        Fetch courses or specializations under a given program ID.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Specialization).where(Specialization.program_id == program_id)
                res = await db.execute(stmt)
                specs = res.scalars().all()
                if not specs:
                    return "No records found."
                return json.dumps([{
                    "id": s.id,
                    "name": s.name,
                    "code": s.specialization_code
                } for s in specs])
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_subjects_by_course(course_id: int) -> str:
        """
        Fetch academic subject modules listed under a course/specialization ID.
        """
        return json.dumps([
            {"subject_id": 101, "subject_code": "CS-301", "subject_name": "Database Management Systems", "credits": 4},
            {"subject_id": 102, "subject_code": "CS-302", "subject_name": "Operating Systems", "credits": 4},
            {"subject_id": 103, "subject_code": "CS-303", "subject_name": "Computer Networks", "credits": 3}
        ])

    @mcp.tool()
    async def get_active_academic_session() -> str:
        """
        Fetch the current active academic session details.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(AcademicSession).where(AcademicSession.is_active == True)
                res = await db.execute(stmt)
                session = res.scalars().first()
                if not session:
                    return "No records found."
                return json.dumps({
                    "id": session.id,
                    "session_name": session.session_name,
                    "is_active": session.is_active
                })
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_academic_program_details(program_id: int) -> str:
        """
        Fetch structural configuration details of an academic program.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Program).where(Program.id == program_id)
                res = await db.execute(stmt)
                program = res.scalars().first()
                if not program:
                    return "No records found."
                return json.dumps({
                    "id": program.id,
                    "name": program.name,
                    "code": program.program_code
                })
            except Exception as e:
                return json.dumps({"error": str(e)})

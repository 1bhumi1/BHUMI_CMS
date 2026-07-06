from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from app.models.api360 import API360Info, API360Confidential
from app.repositories.feedback import FeedbackRepository

class FeedbackService:
    def __init__(self, repo: FeedbackRepository):
        self.repo = repo

    async def get_faculty_details(self, db: AsyncSession, computer_code: int) -> dict:
        """
        Helper method to fetch faculty's name, department, and designation.
        """
        from app.models.staff import Staff, StaffDetails, Designation
        from app.models.academic import Department
        stmt = (
            select(Staff, StaffDetails, Department, Designation)
            .outerjoin(StaffDetails, StaffDetails.staff_id == Staff.id)
            .outerjoin(Department, Department.id == StaffDetails.dept_id)
            .outerjoin(Designation, Designation.id == StaffDetails.designation_id)
            .where(Staff.computer_code == computer_code)
        )
        res = await db.execute(stmt)
        row = res.first()
        if row:
            staff_obj, details_obj, dept_obj, desig_obj = row
            title = staff_obj.title or ""
            first = staff_obj.first_name or ""
            last = staff_obj.last_name or ""
            name = f"{title} {first} {last}".strip()
            dept_name = dept_obj.name if dept_obj else "Not assigned"
            desig_name = desig_obj.designation if desig_obj else "Not assigned"
            dept_id = dept_obj.id if dept_obj else None
            return {
                "name": name,
                "department": dept_name,
                "dept_id": dept_id,
                "designation": desig_name,
                "computer_code": computer_code
            }
        return {
            "name": f"Faculty {computer_code}",
            "department": "Not assigned",
            "dept_id": None,
            "designation": "Not assigned",
            "computer_code": computer_code
        }

    async def get_hod_codes(self, db: AsyncSession) -> set:
        """
        Fetch computer codes of all HODs.
        """
        from app.models.staff import Staff, StaffRole
        from app.models.system import Role
        stmt = select(Staff.computer_code).join(StaffRole).join(Role).where(Role.role_type == "HOD")
        res = await db.execute(stmt)
        return set(res.scalars().all())

    async def _check_access(
        self, db: AsyncSession, target_code: int, caller_context: dict, allow_confidential: bool = False
    ) -> bool:
        """
        Validate role-based access before returning data.
        """
        role = caller_context.get("role", "").lower()
        caller_code = int(caller_context.get("computer_code", -1))
        session_id = caller_context.get("session_id", 9)
        
        if "admin" in role:
            return True
            
        if target_code == caller_code:
            # Faculty can access their own data, EXCEPT confidential reports
            if allow_confidential:
                raise HTTPException(status_code=403, detail="Faculty cannot view their own confidential reports")
            return True
            
        if "hod" in role:
            # HOD can access faculty in their department, excluding themselves
            hod_dept_id = caller_context.get("dept_id")
            if not hod_dept_id:
                raise HTTPException(status_code=403, detail="HOD department not configured")
                
            fac_details = await self.get_faculty_details(db, target_code)
            if fac_details.get("dept_id") == hod_dept_id:
                return True
                
        if "principal" in role:
            # Principal can view HOD appraisals or forwarded records
            hod_codes = await self.get_hod_codes(db)
            if target_code in hod_codes:
                return True
                
            record = await self.repo.get_feedback_record(db, target_code, session_id)
            if record:
                metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
                if metadata_row and metadata_row.ccnc:
                    try:
                        meta = json.loads(metadata_row.ccnc)
                        if meta.get("status") in ["Forwarded to Principal", "Principal Approved", "Principal Rejected"]:
                            return True
                    except:
                        pass
            else:
                return True
                
        raise HTTPException(status_code=403, detail="You do not have permission to access this record")

    def calculate_annexure1_score(self, record: API360Info) -> dict:
        """
        Calculate scores for Category 1 / Annexure I based on teaching, feedback, dept, inst, society.
        """
        # 1. Teaching (cat1i)
        cat1i = [x for x in record.cat1i if x.sno != -999]
        if not cat1i:
            teaching_score = 0.0
        else:
            total_t_score = 0.0
            for row in cat1i:
                scheduled = float(row.nsc or 0)
                held = float((row.nahcof or 0) + (row.nahcon or 0))
                if scheduled > 0:
                    total_t_score += min(25.0, (held / scheduled) * 25.0)
            teaching_score = min(25.0, round((total_t_score / len(cat1i)) * 10.0) / 10.0)

        # 2. Feedback (cat1ii)
        cat1ii = record.cat1ii
        if not cat1ii:
            feedback_score = 0.0
        else:
            total_f_score = sum(float(row.asf or 0) for row in cat1ii)
            feedback_score = min(25.0, total_f_score)

        # 3. Dept Activities (cat1iii)
        cat1iii = record.cat1iii
        dept_score = min(20.0, len(cat1iii) * 5.0)

        # 4. Inst Activities (cat1iv)
        cat1iv = record.cat1iv
        inst_score = min(10.0, sum(float(row.pe or 0) for row in cat1iv))

        # 5. Society Activities (cat1v)
        cat1v = record.cat1v
        society_score = min(10.0, sum(float(row.pe or 0) for row in cat1v))

        total_score = round((teaching_score + feedback_score + dept_score + inst_score + society_score) * 10.0) / 10.0

        return {
            "teaching_score": teaching_score,
            "feedback_score": feedback_score,
            "department_score": dept_score,
            "institute_score": inst_score,
            "society_score": society_score,
            "total_score": total_score
        }

    def calculate_annexure2_score(self, record: API360Info) -> float:
        """
        Calculate total API score from Category 2 / Annexure II.
        """
        return sum(float(c.score or 0) for c in record.cat2)

    def calculate_annexure3_score(self, record: API360Info) -> float:
        """
        Calculate total API score from Category 3 / Annexure III.
        """
        return sum(float(c.score or 0) for c in record.cat3)

    def get_appraisal_status(self, record: API360Info) -> str:
        """
        Get the current status of the appraisal record.
        """
        metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
        if metadata_row and metadata_row.ccnc:
            try:
                meta = json.loads(metadata_row.ccnc)
                return meta.get("status", "Draft")
            except Exception:
                pass
        if record.hod_approval:
            return "Principal Approved"
        if record.submited:
            return "Under HOD Review"
        return "Draft"

    async def get_annexure1(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
        
        scores = self.calculate_annexure1_score(record)
        fac = await self.get_faculty_details(db, computer_code)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "scores": scores,
            "teaching_activities": [{"sno": r.sno, "sas": r.sas, "ccnc": r.ccnc, "nsc": r.nsc, "nahcof": r.nahcof, "nahcon": r.nahcon} for r in record.cat1i if r.sno != -999],
            "student_feedback": [{"sno": r.sno, "sas": r.sas, "cnctp": r.cnctp, "asf": r.asf} for r in record.cat1ii],
            "department_activities": [{"sno": r.sno, "sas": r.sas, "activity": r.activity, "pe": r.pe} for r in record.cat1iii],
            "institute_activities": [{"sno": r.sno, "sas": r.sas, "activity": r.activity, "pe": r.pe} for r in record.cat1iv],
            "society_activities": [{"sno": r.sno, "sas": r.sas, "activity": r.activity, "pe": r.pe} for r in record.cat1v]
        }

    async def get_annexure2(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
        
        total = self.calculate_annexure2_score(record)
        fac = await self.get_faculty_details(db, computer_code)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "category2_total_score": total,
            "publications_and_research": [{"sno": r.sno, "score": r.score} for r in record.cat2]
        }

    async def get_annexure3(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
        
        total = self.calculate_annexure3_score(record)
        fac = await self.get_faculty_details(db, computer_code)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "category3_total_score": total,
            "other_activities": [{"sno": r.sno, "score": r.score} for r in record.cat3]
        }

    async def get_api_score(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
        
        cat2_total = self.calculate_annexure2_score(record)
        cat3_total = self.calculate_annexure3_score(record)
        fac = await self.get_faculty_details(db, computer_code)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "annexure2_api_score": cat2_total,
            "annexure3_api_score": cat3_total,
            "combined_api_score": cat2_total + cat3_total
        }

    async def get_summary(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
        
        status_str = self.get_appraisal_status(record)
        fac = await self.get_faculty_details(db, computer_code)
        
        # Parse metadata
        submitted_at = ""
        hod_remarks = ""
        last_modified = ""
        metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
        if metadata_row and metadata_row.ccnc:
            try:
                meta = json.loads(metadata_row.ccnc)
                submitted_at = meta.get("submitted_at", "")
                hod_remarks = meta.get("hod_remarks", "")
                last_modified = meta.get("last_modified", "")
            except:
                pass

        annexure1_scores = self.calculate_annexure1_score(record)
        annexure2_total = self.calculate_annexure2_score(record)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "status": status_str,
            "submitted": record.submited,
            "hod_approval": record.hod_approval,
            "submitted_at": submitted_at,
            "last_modified": last_modified,
            "hod_remarks": hod_remarks,
            "annexure1_score_summary": annexure1_scores,
            "annexure2_score_total": annexure2_total
        }

    async def get_confidential_report(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context, allow_confidential=True)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
        
        conf = record.confidential
        if not conf:
            return {
                "computer_code": computer_code,
                "academic_session": session_id,
                "status": "Not Filled",
                "message": "No HOD confidential assessment has been saved for this faculty."
            }
            
        fac = await self.get_faculty_details(db, computer_code)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "status": conf.status,
            "parameters": {
                "parameter_1_punctuality_classes": conf.parameter_1,
                "parameter_2_punctuality_reporting": conf.parameter_2,
                "parameter_3_leave_record": conf.parameter_3,
                "parameter_4_behaviour_students": conf.parameter_4,
                "parameter_5_responsibility": conf.parameter_5,
                "parameter_6_completion_assigned_work": conf.parameter_6,
                "parameter_7_contribution_dept": conf.parameter_7
            },
            "total_marks": conf.total_marks,
            "remarks": conf.remarks,
            "created_at": conf.created_at.isoformat() if conf.created_at else "",
            "updated_at": conf.updated_at.isoformat() if conf.updated_at else ""
        }

    async def get_pending_feedback_list(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view pending reviews list")
            
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            if not hod_dept_id:
                raise HTTPException(status_code=403, detail="HOD department not configured")
            department_id = hod_dept_id
            
        records = await self.repo.get_pending_feedbacks(db, department_id, academic_session)
        result = []
        for r in records:
            fac = await self.get_faculty_details(db, r.faculty_computer_code)
            result.append({
                "faculty_name": fac["name"],
                "computer_code": r.faculty_computer_code,
                "department": fac["department"],
                "designation": fac["designation"],
                "api_id": r.api_id,
                "academic_session": r.academic_session,
                "status": "Draft/Unsubmitted"
            })
        return result

    async def get_submitted_feedback_list(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view submitted appraisals list")
            
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            if not hod_dept_id:
                raise HTTPException(status_code=403, detail="HOD department not configured")
            department_id = hod_dept_id
            
        records = await self.repo.get_submitted_feedbacks(db, department_id, academic_session)
        result = []
        for r in records:
            fac = await self.get_faculty_details(db, r.faculty_computer_code)
            status_str = self.get_appraisal_status(r)
            result.append({
                "faculty_name": fac["name"],
                "computer_code": r.faculty_computer_code,
                "department": fac["department"],
                "designation": fac["designation"],
                "api_id": r.api_id,
                "academic_session": r.academic_session,
                "status": status_str,
                "cr_total_marks": r.confidential.total_marks if r.confidential else 0
            })
        return result

    async def get_faculty_feedback(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
            
        scores = self.calculate_annexure1_score(record)
        cat2_total = self.calculate_annexure2_score(record)
        cat3_total = self.calculate_annexure3_score(record)
        fac = await self.get_faculty_details(db, computer_code)
        
        status_str = self.get_appraisal_status(record)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "department": fac["department"],
            "designation": fac["designation"],
            "academic_session": session_id,
            "status": status_str,
            "annexure1_scaled_score": round(scores["total_score"] / 10, 1),
            "annexure1_detailed_scores": scores,
            "annexure2_api_score": cat2_total,
            "annexure3_api_score": cat3_total
        }

    async def get_department_feedback_summary(self, db: AsyncSession, department_id: int, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot access department summaries")
            
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            if not hod_dept_id:
                raise HTTPException(status_code=403, detail="HOD department not configured")
            if department_id != hod_dept_id:
                raise HTTPException(status_code=403, detail="HOD can only access own department summaries")
                
        records = await self.repo.get_department_feedbacks(db, department_id, session_id)
        
        from app.models.academic import Department
        dept_stmt = select(Department.name).where(Department.id == department_id)
        dept_res = await db.execute(dept_stmt)
        dept_name = dept_res.scalar() or f"Department ID {department_id}"
        
        faculty_summaries = []
        total_a1_score = 0.0
        total_a2_score = 0.0
        submitted_count = 0
        total_count = len(records)
        
        for r in records:
            fac = await self.get_faculty_details(db, r.faculty_computer_code)
            a1_scores = self.calculate_annexure1_score(r)
            a2_score = self.calculate_annexure2_score(r)
            
            if r.submited:
                submitted_count += 1
                
            total_a1_score += a1_scores["total_score"]
            total_a2_score += a2_score
            
            faculty_summaries.append({
                "faculty_name": fac["name"],
                "computer_code": r.faculty_computer_code,
                "status": self.get_appraisal_status(r),
                "annexure1_score": a1_scores["total_score"],
                "annexure2_score": a2_score
            })
            
        avg_a1 = round(total_a1_score / total_count, 2) if total_count > 0 else 0.0
        avg_a2 = round(total_a2_score / total_count, 2) if total_count > 0 else 0.0
        
        return {
            "department_name": dept_name,
            "department_id": department_id,
            "academic_session": session_id,
            "total_faculty_records": total_count,
            "submitted_count": submitted_count,
            "pending_count": total_count - submitted_count,
            "average_annexure1_score": avg_a1,
            "average_annexure2_score": avg_a2,
            "faculty_records": faculty_summaries
        }

    async def get_final_score(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            raise HTTPException(status_code=404, detail="Feedback record not found")
            
        fac = await self.get_faculty_details(db, computer_code)
        
        a1_score = self.calculate_annexure1_score(record)
        a1_total = a1_score["total_score"]
        a1_scaled = round(a1_total / 10.0, 1)
        a2_total = self.calculate_annexure2_score(record)
        
        cr_score = 0
        cr_status = "Not Submitted"
        if record.confidential:
            cr_status = record.confidential.status
            if cr_status == "Submitted":
                cr_score = record.confidential.total_marks
                
        final_score = round(a1_scaled + a2_total + cr_score, 1)
        recommended = "Yes" if final_score >= 60.0 else "No"
        status_str = self.get_appraisal_status(record)
        
        return {
            "faculty_name": fac["name"],
            "computer_code": computer_code,
            "academic_session": session_id,
            "status": status_str,
            "annexure1_score": a1_total,
            "annexure1_scaled_to_10": a1_scaled,
            "annexure2_api_score": a2_total,
            "confidential_report_score": cr_score,
            "confidential_report_status": cr_status,
            "overall_final_score": final_score,
            "recommended_for_increment": recommended
        }

    def _check_dept_access(self, dept_id: int, caller_context: dict):
        role = caller_context.get("role", "").lower()
        if "admin" in role or "principal" in role:
            return
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            if hod_dept_id == dept_id:
                return
        raise HTTPException(status_code=403, detail="You do not have permission to access department data")

    def _check_principal_access(self, caller_context: dict):
        role = caller_context.get("role", "").lower()
        if "admin" in role or "principal" in role:
            return
        raise HTTPException(status_code=403, detail="Access denied. Only Principal or Admin can retrieve these metrics.")

    async def get_hod_profile(self, db: AsyncSession, hod_computer_code: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        caller_code = int(caller_context.get("computer_code", -1))
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view HOD profile")
        if "hod" in role and caller_code != hod_computer_code:
            raise HTTPException(status_code=403, detail="HOD can only view their own HOD profile")
        
        fac = await self.get_faculty_details(db, hod_computer_code)
        return {
            "hod_name": fac["name"],
            "computer_code": hod_computer_code,
            "department": fac["department"],
            "designation": fac["designation"],
            "role": "HOD"
        }

    async def get_principal_profile(self, db: AsyncSession, principal_computer_code: int, caller_context: dict) -> dict:
        self._check_principal_access(caller_context)
        fac = await self.get_faculty_details(db, principal_computer_code)
        return {
            "principal_name": fac["name"],
            "computer_code": principal_computer_code,
            "role": "Principal",
            "department": fac["department"],
            "designation": fac["designation"]
        }

    async def get_faculty_above_score(self, db: AsyncSession, threshold_score: float, session_id: int, caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view this score list")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        result = []
        for r in records:
            scores = self.calculate_annexure1_score(r)
            a1_scaled = round(scores["total_score"] / 10.0, 1)
            a2_total = self.calculate_annexure2_score(r)
            cr_score = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final_score = round(a1_scaled + a2_total + cr_score, 1)
            
            if final_score >= threshold_score:
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"],
                    "final_score": final_score,
                    "recommended_for_increment": "Yes" if final_score >= 60.0 else "No"
                })
        return result

    async def get_faculty_below_score(self, db: AsyncSession, threshold_score: float, session_id: int, caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view this score list")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        result = []
        for r in records:
            scores = self.calculate_annexure1_score(r)
            a1_scaled = round(scores["total_score"] / 10.0, 1)
            a2_total = self.calculate_annexure2_score(r)
            cr_score = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final_score = round(a1_scaled + a2_total + cr_score, 1)
            
            if final_score < threshold_score:
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"],
                    "final_score": final_score,
                    "recommended_for_increment": "Yes" if final_score >= 60.0 else "No"
                })
        return result

    async def get_top_faculty(self, db: AsyncSession, limit: int, session_id: int, caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view score leaderboards")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        result = []
        for r in records:
            scores = self.calculate_annexure1_score(r)
            a1_scaled = round(scores["total_score"] / 10.0, 1)
            a2_total = self.calculate_annexure2_score(r)
            cr_score = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final_score = round(a1_scaled + a2_total + cr_score, 1)
            
            fac = await self.get_faculty_details(db, r.faculty_computer_code)
            result.append({
                "faculty_name": fac["name"],
                "computer_code": r.faculty_computer_code,
                "department": fac["department"],
                "final_score": final_score
            })
        result.sort(key=lambda x: x["final_score"], reverse=True)
        return result[:limit]

    async def get_bottom_faculty(self, db: AsyncSession, limit: int, session_id: int, caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view score leaderboards")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        result = []
        for r in records:
            scores = self.calculate_annexure1_score(r)
            a1_scaled = round(scores["total_score"] / 10.0, 1)
            a2_total = self.calculate_annexure2_score(r)
            cr_score = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final_score = round(a1_scaled + a2_total + cr_score, 1)
            
            fac = await self.get_faculty_details(db, r.faculty_computer_code)
            result.append({
                "faculty_name": fac["name"],
                "computer_code": r.faculty_computer_code,
                "department": fac["department"],
                "final_score": final_score
            })
        result.sort(key=lambda x: x["final_score"])
        return result[:limit]

    async def get_highest_api_score(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view API score metrics")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        if not records:
            return {}
            
        best_rec = None
        max_api = -1.0
        for r in records:
            api_score = self.calculate_annexure2_score(r) + self.calculate_annexure3_score(r)
            if api_score > max_api:
                max_api = api_score
                best_rec = r
                
        if not best_rec:
            return {}
        fac = await self.get_faculty_details(db, best_rec.faculty_computer_code)
        return {
            "faculty_name": fac["name"],
            "computer_code": best_rec.faculty_computer_code,
            "department": fac["department"],
            "highest_api_score": max_api
        }

    async def get_lowest_api_score(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view API score metrics")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        if not records:
            return {}
            
        worst_rec = None
        min_api = 99999.0
        for r in records:
            api_score = self.calculate_annexure2_score(r) + self.calculate_annexure3_score(r)
            if api_score < min_api:
                min_api = api_score
                worst_rec = r
                
        if not worst_rec:
            return {}
        fac = await self.get_faculty_details(db, worst_rec.faculty_computer_code)
        return {
            "faculty_name": fac["name"],
            "computer_code": worst_rec.faculty_computer_code,
            "department": fac["department"],
            "lowest_api_score": min_api
        }

    async def get_highest_cr_score(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view confidential metrics")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        best_rec = None
        max_cr = -1
        for r in records:
            if r.confidential and r.confidential.status == "Submitted":
                cr_score = r.confidential.total_marks
                if cr_score > max_cr:
                    max_cr = cr_score
                    best_rec = r
        if not best_rec:
            return {"message": "No submitted confidential reports found"}
        fac = await self.get_faculty_details(db, best_rec.faculty_computer_code)
        return {
            "faculty_name": fac["name"],
            "computer_code": best_rec.faculty_computer_code,
            "department": fac["department"],
            "highest_cr_score": max_cr
        }

    async def get_lowest_cr_score(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view confidential metrics")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        worst_rec = None
        min_cr = 99999
        for r in records:
            if r.confidential and r.confidential.status == "Submitted":
                cr_score = r.confidential.total_marks
                if cr_score < min_cr:
                    min_cr = cr_score
                    worst_rec = r
        if not worst_rec:
            return {"message": "No submitted confidential reports found"}
        fac = await self.get_faculty_details(db, worst_rec.faculty_computer_code)
        return {
            "faculty_name": fac["name"],
            "computer_code": worst_rec.faculty_computer_code,
            "department": fac["department"],
            "lowest_cr_score": min_cr
        }

    async def get_pending_confidential_reports(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view pending confidential reports list")
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            department_id = hod_dept_id
            
        records = await self.repo.get_all_feedbacks(db, academic_session or 9, department_id)
        result = []
        for r in records:
            if not r.confidential or r.confidential.status != "Submitted":
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"],
                    "status": r.confidential.status if r.confidential else "Not Started"
                })
        return result

    async def get_submitted_confidential_reports(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view submitted confidential reports list")
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            department_id = hod_dept_id
            
        records = await self.repo.get_all_feedbacks(db, academic_session or 9, department_id)
        result = []
        for r in records:
            if r.confidential and r.confidential.status == "Submitted":
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"],
                    "total_marks": r.confidential.total_marks,
                    "remarks": r.confidential.remarks
                })
        return result

    async def get_pending_api_reports(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view pending approvals list")
        if "hod" in role:
            hod_dept_id = caller_context.get("dept_id")
            department_id = hod_dept_id
            
        records = await self.repo.get_all_feedbacks(db, academic_session or 9, department_id)
        result = []
        for r in records:
            status_str = self.get_appraisal_status(r)
            if status_str in ["Under HOD Review", "Forwarded to Principal"]:
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"],
                    "status": status_str
                })
        return result

    async def get_department_average_score(self, db: AsyncSession, department_id: int, session_id: int, caller_context: dict) -> dict:
        self._check_dept_access(department_id, caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id, department_id)
        if not records:
            return {"message": "No appraisals found for this department"}
            
        total_a1 = 0.0
        total_a2 = 0.0
        total_a3 = 0.0
        total_final = 0.0
        for r in records:
            a1 = self.calculate_annexure1_score(r)["total_score"]
            a2 = self.calculate_annexure2_score(r)
            a3 = self.calculate_annexure3_score(r)
            cr_score = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final = round((a1 / 10.0) + a2 + cr_score, 1)
            
            total_a1 += a1
            total_a2 += a2
            total_a3 += a3
            total_final += final
            
        count = len(records)
        return {
            "department_id": department_id,
            "academic_session": session_id,
            "faculty_count": count,
            "average_annexure1_score": round(total_a1 / count, 2),
            "average_annexure2_score": round(total_a2 / count, 2),
            "average_annexure3_score": round(total_a3 / count, 2),
            "average_final_score": round(total_final / count, 2)
        }

    async def get_department_statistics(self, db: AsyncSession, department_id: int, session_id: int, caller_context: dict) -> dict:
        self._check_dept_access(department_id, caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id, department_id)
        if not records:
            return {"message": "No records found"}
            
        sub_count = sum(1 for r in records if r.submited)
        total_count = len(records)
        avg_data = await self.get_department_average_score(db, department_id, session_id, caller_context)
        
        # Recommendations
        rec_count = 0
        for r in records:
            a1 = self.calculate_annexure1_score(r)["total_score"]
            a2 = self.calculate_annexure2_score(r)
            cr = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final = round((a1 / 10.0) + a2 + cr, 1)
            if final >= 60.0:
                rec_count += 1
                
        return {
            "department_id": department_id,
            "total_faculty": total_count,
            "submitted_count": sub_count,
            "pending_count": total_count - sub_count,
            "average_final_score": avg_data.get("average_final_score"),
            "increment_recommendation_rate_pct": round((rec_count / total_count) * 100.0, 1) if total_count > 0 else 0.0
        }

    async def get_hod_dashboard(self, db: AsyncSession, department_id: int, session_id: int, caller_context: dict) -> dict:
        self._check_dept_access(department_id, caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id, department_id)
        total_count = len(records)
        sub_count = sum(1 for r in records if r.submited)
        cr_pending = sum(1 for r in records if not r.confidential or r.confidential.status != "Submitted")
        
        scores = [round((self.calculate_annexure1_score(r)["total_score"] / 10.0) + self.calculate_annexure2_score(r) + (r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0), 1) for r in records]
        avg_score = round(sum(scores) / total_count, 1) if total_count > 0 else 0.0
        
        return {
            "department_id": department_id,
            "academic_session": session_id,
            "total_faculty": total_count,
            "submitted_appraisals": sub_count,
            "pending_appraisals": total_count - sub_count,
            "pending_confidential_reports": cr_pending,
            "average_final_score": avg_score
        }

    async def get_principal_dashboard(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        self._check_principal_access(caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id)
        total_count = len(records)
        sub_count = sum(1 for r in records if r.submited)
        approved_count = sum(1 for r in records if r.hod_approval)
        
        scores = [round((self.calculate_annexure1_score(r)["total_score"] / 10.0) + self.calculate_annexure2_score(r) + (r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0), 1) for r in records]
        avg_score = round(sum(scores) / total_count, 1) if total_count > 0 else 0.0
        
        return {
            "academic_session": session_id,
            "total_faculty": total_count,
            "total_submitted": sub_count,
            "total_approved": approved_count,
            "pending_approvals": total_count - approved_count,
            "average_campus_score": avg_score
        }

    async def get_annexure_completion(self, db: AsyncSession, computer_code: int, session_id: int, caller_context: dict) -> dict:
        await self._check_access(db, computer_code, caller_context)
        record = await self.repo.get_feedback_record(db, computer_code, session_id)
        if not record:
            return {"annexure_1": "Not Started", "annexure_2": "Not Started", "annexure_3": "Not Started"}
            
        return {
            "annexure_1": "Filled" if len(record.cat1i) > 0 else "Not Started",
            "annexure_2": "Filled" if len(record.cat2) > 0 else "Not Started",
            "annexure_3": "Filled" if len(record.cat3) > 0 else "Not Started"
        }

    async def get_faculty_without_annexure2(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "hod" in role:
            department_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view this report")
            
        records = await self.repo.get_all_feedbacks(db, academic_session or 9, department_id)
        result = []
        for r in records:
            if not r.cat2:
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"]
                })
        return result

    async def get_faculty_without_annexure3(self, db: AsyncSession, department_id: Optional[int], academic_session: Optional[int], caller_context: dict) -> List[dict]:
        role = caller_context.get("role", "").lower()
        if "hod" in role:
            department_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view this report")
            
        records = await self.repo.get_all_feedbacks(db, academic_session or 9, department_id)
        result = []
        for r in records:
            if not r.cat3:
                fac = await self.get_faculty_details(db, r.faculty_computer_code)
                result.append({
                    "faculty_name": fac["name"],
                    "computer_code": r.faculty_computer_code,
                    "department": fac["department"]
                })
        return result

    async def get_feedback_by_department(self, db: AsyncSession, department_id: int, session_id: int, caller_context: dict) -> List[dict]:
        self._check_dept_access(department_id, caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id, department_id)
        result = []
        for r in records:
            fac = await self.get_faculty_details(db, r.faculty_computer_code)
            scores = self.calculate_annexure1_score(r)
            a1_scaled = round(scores["total_score"] / 10.0, 1)
            a2_total = self.calculate_annexure2_score(r)
            cr_score = r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0
            final_score = round(a1_scaled + a2_total + cr_score, 1)
            result.append({
                "faculty_name": fac["name"],
                "computer_code": r.faculty_computer_code,
                "annexure1_score": scores["total_score"],
                "annexure2_api_score": a2_total,
                "final_score": final_score
            })
        return result

    async def get_feedback_by_session(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        self._check_principal_access(caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id)
        total = len(records)
        submitted = sum(1 for r in records if r.submited)
        return {
            "academic_session": session_id,
            "total_records": total,
            "submitted_records": submitted,
            "pending_records": total - submitted
        }

    async def get_total_submissions(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view submissions summary")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        total_sub = sum(1 for r in records if r.submited)
        return {
            "academic_session": session_id,
            "total_submitted_appraisals": total_sub
        }

    async def get_total_pending(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        role = caller_context.get("role", "").lower()
        dept_id = None
        if "hod" in role:
            dept_id = caller_context.get("dept_id")
        elif "faculty" in role:
            raise HTTPException(status_code=403, detail="Faculty cannot view submissions summary")
            
        records = await self.repo.get_all_feedbacks(db, session_id, dept_id)
        total_pending = sum(1 for r in records if not r.submited)
        return {
            "academic_session": session_id,
            "total_pending_appraisals": total_pending
        }

    async def get_overall_statistics(self, db: AsyncSession, session_id: int, caller_context: dict) -> dict:
        self._check_principal_access(caller_context)
        records = await self.repo.get_all_feedbacks(db, session_id)
        if not records:
            return {"message": "No appraisals submitted for this session"}
            
        scores = []
        for r in records:
            scores.append(round((self.calculate_annexure1_score(r)["total_score"] / 10.0) + self.calculate_annexure2_score(r) + (r.confidential.total_marks if (r.confidential and r.confidential.status == "Submitted") else 0), 1))
            
        return {
            "academic_session": session_id,
            "total_faculty": len(records),
            "average_score": round(sum(scores) / len(records), 2),
            "highest_score": max(scores) if scores else 0.0,
            "lowest_score": min(scores) if scores else 0.0
        }


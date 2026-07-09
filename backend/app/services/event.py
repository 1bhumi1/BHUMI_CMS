import csv
import io
import os
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import joinedload

from app.models.event import Event, EventRegistration, EventPayment, EventAttendance, EventCertificate, WorkshopDetails
from app.models.payment import TransactionDetails
from app.models.system import Notification
from app.models.auth import Login
from app.models.student import Student, StudentAdmission
from app.models.staff import Staff, StaffDetails
from app.models.academic import AcademicProgram
from app.repositories import (
    event_repo,
    event_registration_repo,
    event_payment_repo,
    event_attendance_repo,
    event_certificate_repo,
)

class EventService:
    async def create_event(self, db: AsyncSession, obj_in: Dict[str, Any], user_id: int) -> Event:
        obj_in["created_by"] = user_id
        obj_in["status"] = "Draft"
        ev = await event_repo.create(db, obj_in=obj_in)
        await db.flush()
        
        if ev.event_type == "Workshop":
            wd = WorkshopDetails(
                event_id=ev.id,
                title=ev.title,
                description=ev.description,
                start_date=ev.start_date,
                end_date=ev.end_date,
                venue=ev.venue,
                max_seats=ev.max_seats,
                fee_amount=ev.fee_amount
            )
            db.add(wd)
            await db.flush()
        return ev

    async def update_event(self, db: AsyncSession, event_id: int, obj_in: Dict[str, Any]) -> Event:
        event = await event_repo.get(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        if event.status == "Closed":
            raise HTTPException(status_code=400, detail="Cannot update a closed event")
        ev = await event_repo.update(db, db_obj=event, obj_in=obj_in)
        await db.flush()
        
        if ev.event_type == "Workshop":
            stmt = select(WorkshopDetails).where(WorkshopDetails.event_id == ev.id)
            res = await db.execute(stmt)
            wd = res.scalars().first()
            if not wd:
                wd = WorkshopDetails(event_id=ev.id)
            wd.title = ev.title
            wd.description = ev.description
            wd.start_date = ev.start_date
            wd.end_date = ev.end_date
            wd.venue = ev.venue
            wd.max_seats = ev.max_seats
            wd.fee_amount = ev.fee_amount
            db.add(wd)
            await db.flush()
        else:
            stmt = select(WorkshopDetails).where(WorkshopDetails.event_id == ev.id)
            res = await db.execute(stmt)
            wd = res.scalars().first()
            if wd:
                await db.delete(wd)
                await db.flush()
        return ev

    async def delete_event(self, db: AsyncSession, event_id: int) -> Event:
        event = await event_repo.get(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return await event_repo.remove(db, id=event_id)

    async def publish_event(self, db: AsyncSession, event_id: int) -> Event:
        event = await event_repo.get(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        if event.status != "Draft":
            raise HTTPException(status_code=400, detail="Event is already published or closed")

        # Set status to Published
        event.status = "Published"
        db.add(event)
        await db.flush()

        # Trigger Notifications for eligible users
        user_ids = await self.get_eligible_user_ids(db, event)
        message = f"New Event Published: {event.title} ({event.event_type}) on {event.start_date.strftime('%d-%m-%Y %H:%M')}. Register before {event.registration_deadline.strftime('%d-%m-%Y')}."
        
        # Batch insert notifications
        for uid in user_ids:
            notification = Notification(
                user_id=uid,
                message=message,
                is_read=False
            )
            db.add(notification)
        
        await db.flush()
        return event

    async def get_eligible_user_ids(self, db: AsyncSession, event: Event) -> List[int]:
        uids = []
        # Find eligible students
        if event.audience in ["Students", "Both"]:
            stmt = (
                select(Login.id)
                .join(Student, Login.student_id == Student.id)
                .where(Student.active == True)
            )
            if event.department_id is not None or event.program_id is not None or event.semester is not None:
                stmt = stmt.join(StudentAdmission, StudentAdmission.student_id == Student.id)
                stmt = stmt.join(AcademicProgram, AcademicProgram.id == StudentAdmission.academic_program_id)
                if event.department_id is not None:
                    stmt = stmt.where(AcademicProgram.department_id == event.department_id)
                if event.program_id is not None:
                    stmt = stmt.where(AcademicProgram.program_id == event.program_id)
                if event.semester is not None:
                    stmt = stmt.where(StudentAdmission.entry_semester == event.semester)
                
            res = await db.execute(stmt)
            uids.extend(res.scalars().all())

        # Find eligible faculty
        if event.audience in ["Faculty", "Both"]:
            stmt = (
                select(Login.id)
                .join(Staff, Login.staff_id == Staff.id)
                .where(Staff.active == True)
            )
            if event.department_id is not None:
                stmt = stmt.join(StaffDetails, StaffDetails.staff_id == Staff.id)
                stmt = stmt.where(StaffDetails.dept_id == event.department_id)
                
            res = await db.execute(stmt)
            uids.extend(res.scalars().all())

        return list(set(uids))

    async def register_for_event(self, db: AsyncSession, event_id: int, user_id: int) -> Dict[str, Any]:
        event = await event_repo.get(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if event.status != "Published":
            raise HTTPException(status_code=400, detail="Registration is not open for this event")
            
        if datetime.now() > event.registration_deadline:
            raise HTTPException(status_code=400, detail="Registration deadline has passed")

        # Check existing registration
        existing = await event_registration_repo.get_by_event_and_user(db, event_id, user_id)
        if existing:
            if existing.status == "Confirmed":
                raise HTTPException(status_code=400, detail="You are already registered for this event")
            elif existing.status == "Pending" and event.fee_required == 1:
                # Return payment instructions for pending payment
                payment = await db.execute(
                    select(EventPayment).where(EventPayment.registration_id == existing.id, EventPayment.status == "Pending")
                )
                p_obj = payment.scalars().first()
                return {
                    "registration": existing,
                    "payment_required": True,
                    "transaction_id": p_obj.transaction_id if p_obj else None,
                    "amount": event.fee_amount
                }

        # Check seat availability
        reg_count = await db.execute(
            select(func.count(EventRegistration.id))
            .where(EventRegistration.event_id == event_id, EventRegistration.status == "Confirmed")
        )
        current_seats = reg_count.scalar() or 0
        if current_seats >= event.max_seats:
            raise HTTPException(status_code=400, detail="Event is fully booked")

        # Create registration
        # If fee required = No, registration status is Confirmed. Otherwise Pending.
        reg_status = "Confirmed" if event.fee_required == 0 else "Pending"
        reg_dict = {
            "event_id": event_id,
            "user_id": user_id,
            "status": reg_status
        }
        reg = await event_registration_repo.create(db, obj_in=reg_dict)

        if event.fee_required == 1:
            txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            pay_dict = {
                "registration_id": reg.id,
                "transaction_id": txn_id,
                "amount": event.fee_amount,
                "status": "Pending"
            }
            await event_payment_repo.create(db, obj_in=pay_dict)

            # Map student/faculty details dynamically
            firstname = "USER"
            email = "billing@college.edu"
            phone = 9999999999
            enrollment = "N/A"
            computer_code = 0
            semester = 1
            dept_id = 0
            
            login_res = await db.execute(select(Login).where(Login.id == user_id))
            login = login_res.scalar()
            if login:
                computer_code = int(login.computer_code)
                if login.student_id:
                    stu_stmt = (
                        select(Student, StudentAdmission, AcademicProgram)
                        .join(StudentAdmission, StudentAdmission.student_id == Student.id)
                        .join(AcademicProgram, AcademicProgram.id == StudentAdmission.academic_program_id)
                        .where(Student.id == login.student_id)
                    )
                    stu_res = await db.execute(stu_stmt)
                    stu_rec = stu_res.first()
                    if stu_rec:
                        student, admission, program = stu_rec[0], stu_rec[1], stu_rec[2]
                        firstname = student.first_name.upper()
                        email = student.email or email
                        phone = student.mobile or phone
                        enrollment = student.enrollment_no or f"ENR{computer_code}"
                        semester = admission.entry_semester
                        dept_id = program.department_id
                elif login.staff_id:
                    staff_stmt = (
                        select(Staff, StaffDetails)
                        .join(StaffDetails, StaffDetails.staff_id == Staff.id)
                        .where(Staff.id == login.staff_id)
                    )
                    staff_res = await db.execute(staff_stmt)
                    staff_rec = staff_res.first()
                    if staff_rec:
                        staff, details = staff_rec[0], staff_rec[1]
                        firstname = staff.first_name.upper()
                        email = staff.email or email
                        phone = staff.mobile or phone
                        enrollment = f"FAC{computer_code}"
                        semester = 1
                        dept_id = details.dept_id

            from datetime import date
            txn = TransactionDetails(
                computer_code=computer_code,
                enrollment=enrollment,
                firstname=firstname,
                email=email,
                phone=phone,
                student_section_id=0,
                study_department_id=dept_id,
                semester=semester,
                academic_session=event.academic_session_id,
                amount=float(event.fee_amount),
                extra_charge=0.0,
                productinfo=event.title[:50],
                txn_key=os.getenv("PAYU_KEY", "TEST_KEY"),
                txnid=txn_id,
                txn_date=date.today(),
                resphash="",
                status="pending",
                status_to_show="Pending",
                msg="Event/Workshop payment initiated",
                msg1="Pending Payment"
            )
            db.add(txn)
            await db.flush()

            return {
                "registration": reg,
                "payment_required": True,
                "transaction_id": txn_id,
                "amount": event.fee_amount
            }

        return {
            "registration": reg,
            "payment_required": False
        }

    async def handle_payu_callback(self, db: AsyncSession, transaction_id: str, status_str: str, gateway_ref: Optional[str] = None) -> EventPayment:
        payment = await event_payment_repo.get_by_txn_id(db, transaction_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Transaction payment record not found")

        registration = payment.registration
        if status_str.lower() == "success":
            payment.status = "Success"
            payment.paid_at = datetime.now()
            payment.payment_gateway_ref = gateway_ref
            
            registration.status = "Confirmed"
            
            # Create default attendance record
            att_dict = {
                "event_id": registration.event_id,
                "registration_id": registration.id,
                "attended": 0
            }
            await event_attendance_repo.create(db, obj_in=att_dict)
        else:
            payment.status = "Failed"
            registration.status = "Cancelled"

        # Update general txn_details table entry
        txn_stmt = select(TransactionDetails).where(TransactionDetails.txnid == transaction_id)
        txn_res = await db.execute(txn_stmt)
        txn = txn_res.scalars().first()
        if txn:
            txn.status = status_str.lower()
            if status_str.lower() == "success":
                txn.status_to_show = "Success"
                txn.msg = "Transaction Successful, Hash Verified...Payment Verified..."
                txn.msg1 = "Transaction Successful."
            else:
                txn.status_to_show = "Failed"
                txn.msg = "Payment failed"
                txn.msg1 = "Transaction Failed."
            db.add(txn)

        db.add(payment)
        db.add(registration)
        await db.flush()
        return payment

    async def mark_attendance(self, db: AsyncSession, payload_list: List[Dict[str, Any]], user_id: int) -> List[EventAttendance]:
        results = []
        for mark in payload_list:
            reg_id = mark["registration_id"]
            attended = mark["attended"]
            
            reg = await event_registration_repo.get(db, reg_id)
            if not reg:
                continue
                
            att = await event_attendance_repo.get_by_event_and_reg(db, reg.event_id, reg_id)
            if att:
                att.attended = attended
                att.marked_at = datetime.now()
                att.marked_by = user_id
                db.add(att)
            else:
                att_dict = {
                    "event_id": reg.event_id,
                    "registration_id": reg_id,
                    "attended": attended,
                    "marked_at": datetime.now(),
                    "marked_by": user_id
                }
                att = await event_attendance_repo.create(db, obj_in=att_dict)
            results.append(att)
        await db.flush()
        return results

    async def issue_certificate(self, db: AsyncSession, registration_id: int) -> EventCertificate:
        reg = await event_registration_repo.get(db, registration_id)
        if not reg or reg.status != "Confirmed":
            raise HTTPException(status_code=400, detail="Valid registration required to issue certificate")

        # Verify attendance
        att = await event_attendance_repo.get_by_event_and_reg(db, reg.event_id, registration_id)
        if not att or att.attended != 1:
            raise HTTPException(status_code=400, detail="User must attend the event to receive a certificate")

        # Check existing
        existing = await db.execute(
            select(EventCertificate).where(EventCertificate.registration_id == registration_id)
        )
        cert = existing.scalars().first()
        if cert:
            return cert

        cert_code = f"CERT-{reg.event_id}-{registration_id}-{uuid.uuid4().hex[:6].upper()}"
        file_url = f"/certificates/download/{cert_code}"
        
        cert_dict = {
            "event_id": reg.event_id,
            "registration_id": registration_id,
            "certificate_code": cert_code,
            "file_url": file_url
        }
        return await event_certificate_repo.create(db, obj_in=cert_dict)

    async def get_report_summary(self, db: AsyncSession, event_id: Optional[int] = None) -> Dict[str, Any]:
        reg_filter = []
        if event_id is not None:
            reg_filter.append(EventRegistration.event_id == event_id)

        # Count metrics
        stmt_total = select(func.count(EventRegistration.id))
        if reg_filter:
            stmt_total = stmt_total.where(and_(*reg_filter))
        total_res = await db.execute(stmt_total)
        total = total_res.scalar() or 0

        # Confirmed / Paid
        stmt_paid = select(func.count(EventRegistration.id)).where(EventRegistration.status == "Confirmed")
        if reg_filter:
            stmt_paid = stmt_paid.where(and_(*reg_filter))
        paid_res = await db.execute(stmt_paid)
        paid = paid_res.scalar() or 0

        # Pending
        stmt_pending = select(func.count(EventRegistration.id)).where(EventRegistration.status == "Pending")
        if reg_filter:
            stmt_pending = stmt_pending.where(and_(*reg_filter))
        pending_res = await db.execute(stmt_pending)
        pending = pending_res.scalar() or 0

        # Cancelled
        stmt_cancelled = select(func.count(EventRegistration.id)).where(EventRegistration.status == "Cancelled")
        if reg_filter:
            stmt_cancelled = stmt_cancelled.where(and_(*reg_filter))
        cancelled_res = await db.execute(stmt_cancelled)
        cancelled = cancelled_res.scalar() or 0

        # Attendance Count
        stmt_att = select(func.count(EventAttendance.id)).where(EventAttendance.attended == 1)
        if event_id is not None:
            stmt_att = stmt_att.where(EventAttendance.event_id == event_id)
        att_res = await db.execute(stmt_att)
        att = att_res.scalar() or 0

        # Revenue
        stmt_rev = select(func.sum(EventPayment.amount)).join(EventRegistration, EventRegistration.id == EventPayment.registration_id).where(EventPayment.status == "Success")
        if event_id is not None:
            stmt_rev = stmt_rev.where(EventRegistration.event_id == event_id)
        rev_res = await db.execute(stmt_rev)
        revenue = rev_res.scalar() or Decimal("0.00")

        return {
            "total_registrations": total,
            "paid_registrations": paid,
            "pending_registrations": pending,
            "cancelled_registrations": cancelled,
            "attendance_count": att,
            "total_revenue": revenue
        }

    async def export_registrations_csv(self, db: AsyncSession, event_id: Optional[int] = None) -> Tuple[bytes, str]:
        regs = await event_registration_repo.get_event_registrations_detailed(db, event_id=event_id, limit=5000)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Registration ID", "Event Title", "Event Type", "User Name", 
            "Computer Code", "Role", "Registered At", "Status", "Payment Amount", "Payment Status", "Attended"
        ])
        
        for r in regs:
            # Get payment detail
            pay_amt = r.payments[0].amount if r.payments else Decimal("0.00")
            pay_status = r.payments[0].status if r.payments else "Free"
            attended_str = "Yes" if (r.attendance and r.attendance[0].attended == 1) else "No"
            
            # Resolve user details
            u_name = "Unknown"
            cc = 0
            u_role = "Student"
            if r.user:
                cc = r.user.computer_code
                if r.user.student:
                    s = r.user.student
                    u_name = f"{s.first_name} {s.last_name}"
                    u_role = "Student"
                elif r.user.staff:
                    st = r.user.staff
                    u_name = f"{st.first_name} {st.last_name}"
                    u_role = "Faculty"
            
            writer.writerow([
                r.id, r.event.title, r.event.event_type, u_name,
                cc, u_role, r.registered_at.strftime('%Y-%m-%d %H:%M'), r.status, pay_amt, pay_status, attended_str
            ])
            
        return output.getvalue().encode('utf-8'), "event_registrations_report.csv"

event_service = EventService()

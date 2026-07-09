import os
import hashlib
import uuid
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.payment import TransactionDetails, FeeStructure, StudentFee, PaymentReceipt
from app.models.student import Student, StudentAdmission
from app.models.academic import AcademicProgram
from app.repositories import txn_details_repo, fee_structure_repo, student_fee_repo, payment_receipt_repo

# PDF Generation imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PaymentService:
    def get_action_url(self) -> str:
        if settings.PAYU_MODE.lower() == "live":
            return "https://secure.payu.in/_payment"
        return "https://sandboxsecure.payu.in/_payment"

    async def initiate_payment(self, db: AsyncSession, student_fee_id: int, computer_code: int) -> Dict[str, Any]:
        # 1. Fetch student fee
        fee_stmt = select(StudentFee).options(joinedload(StudentFee.fee_structure)).where(StudentFee.id == student_fee_id, StudentFee.computer_code == computer_code)
        fee_res = await db.execute(fee_stmt)
        sf = fee_res.scalars().first()
        if not sf:
            raise Exception("Fee record not found or unauthorized.")
        if sf.status == "Success":
            raise Exception("This fee is already successfully paid.")

        # 2. Resolve Student Personal and Academic details
        stu_stmt = (
            select(Student, StudentAdmission, AcademicProgram)
            .join(StudentAdmission, StudentAdmission.student_id == Student.id)
            .join(AcademicProgram, AcademicProgram.id == StudentAdmission.academic_program_id)
            .where(Student.computer_code == computer_code)
        )
        res = await db.execute(stu_stmt)
        record = res.first()
        if not record:
            raise Exception("Student admission profile not found.")
        
        student, admission, program = record[0], record[1], record[2]

        # 3. Generate unique transaction ID
        txnid = f"Txn{computer_code}{int(datetime.utcnow().timestamp())}"
        amount = float(sf.fee_structure.amount)
        productinfo = sf.fee_structure.title[:50]
        firstname = student.first_name.upper()
        email = student.email or "billing@college.edu"
        phone = student.mobile or 9999999999
        
        # Redirection callback endpoints on our frontend/backend
        # In typical PayU integration, PayU redirects back to the backend callback which processes hash and then redirects student to a success/failure screen on the React UI.
        # So surl and furl point to our backend callback, or point directly to the page. But since we need to verify hash server-side, they must point to our backend API!
        # PayU posts the transaction data to the callback URL.
        # surl: success url, furl: failure url
        # We will use our backend's payu-callback endpoint as both success and failure URL.
        # PayU will POST transaction status directly to this endpoint.
        host = os.getenv("APP_HOST_URL", "http://127.0.0.1:8000")
        callback_url = f"{host}/api/v1/payments/payu-callback"
        
        key = settings.PAYU_KEY
        salt = settings.PAYU_SALT

        # We store student_fee_id in udf2 and computer_code in udf1
        udf1 = str(computer_code)
        udf2 = str(student_fee_id)

        # 4. Generate SHA-512 Hash
        # Sequence: key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10|salt
        hash_seq = [
            key,
            txnid,
            f"{amount:.2f}",
            productinfo,
            firstname,
            email,
            udf1,
            udf2,
            "", "", "", "", "", "", "", "",  # UDF3 to UDF10 empty
            salt
        ]
        hash_string = "|".join(hash_seq)
        payu_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

        # 5. Insert transaction entry inside txn_details table
        txn = TransactionDetails(
            computer_code=computer_code,
            enrollment=student.enrollment_no or f"ENR{computer_code}",
            firstname=firstname,
            email=email,
            phone=phone,
            student_section_id=0,
            study_department_id=program.department_id,
            semester=admission.entry_semester,
            academic_session=sf.fee_structure.academic_session_id,
            amount=amount,
            extra_charge=0.0,
            productinfo=productinfo,
            txn_key=key,
            txnid=txnid,
            txn_date=date.today(),
            resphash="",
            status="pending",
            status_to_show="Pending",
            msg="Transaction initiated",
            msg1="Pending Payment"
        )
        db.add(txn)
        await db.flush()

        # Return PayU post variables
        return {
            "key": key,
            "txnid": txnid,
            "amount": amount,
            "productinfo": productinfo,
            "firstname": firstname,
            "email": email,
            "phone": str(phone),
            "surl": callback_url,
            "furl": callback_url,
            "hash": payu_hash,
            "action_url": self.get_action_url(),
            "udf1": udf1,
            "udf2": udf2
        }

    async def verify_and_process_callback(self, db: AsyncSession, callback_data: Dict[str, Any]) -> str:
        txnid = callback_data.get("txnid")
        status = callback_data.get("status")
        hash_from_callback = callback_data.get("hash")
        key = callback_data.get("key")
        amount = callback_data.get("amount")
        productinfo = callback_data.get("productinfo")
        firstname = callback_data.get("firstname")
        email = callback_data.get("email")
        
        udf1 = callback_data.get("udf1", "")  # computer_code
        udf2 = callback_data.get("udf2", "")  # student_fee_id
        
        # 1. Retrieve transaction details
        txn = await txn_details_repo.get_by_txnid(db, txnid)
        if not txn:
            raise Exception("Transaction not found for ID: " + str(txnid))

        # 2. Verify Hash
        # Reverse hash sequence: salt|status|additionalCharges|udf10|...|udf1|email|firstname|productinfo|amount|txnid|key
        salt = settings.PAYU_SALT
        additional_charges = callback_data.get("additionalCharges", "")
        
        seq = [salt, status]
        if additional_charges:
            seq.append(additional_charges)
        else:
            seq.append("")
            
        for i in range(10, 0, -1):
            seq.append(callback_data.get(f"udf{i}", ""))
            
        seq.extend([email, firstname, productinfo, amount, txnid, key])
        hash_str = "|".join(seq)
        calculated_hash = hashlib.sha512(hash_str.encode('utf-8')).hexdigest().lower()

        # Verify hash matches (bypass in test mode)
        if settings.PAYU_MODE.lower() != "test" and calculated_hash != hash_from_callback:
            # Let's update transaction as failed due to signature verification mismatch
            txn.status = "failure"
            txn.status_to_show = "Failed"
            txn.resphash = hash_from_callback or ""
            txn.msg = "Payment failed for Hash not verified..."
            txn.msg1 = "Hash verification failed."
            await db.flush()
            return "failed-hash"

        # Hash is verified! Now update transaction details
        txn.resphash = hash_from_callback
        txn.status = status
        
        if status == "success":
            txn.status_to_show = "Success"
            txn.msg = "Transaction Successful, Hash Verified...Payment Verified..."
            txn.msg1 = "Transaction Successful."
            
            # Update StudentFee table
            if udf2:
                sf_stmt = select(StudentFee).options(joinedload(StudentFee.fee_structure)).where(StudentFee.id == int(udf2))
                sf_res = await db.execute(sf_stmt)
                sf = sf_res.scalars().first()
                if sf:
                    sf.status = "Success"
                    sf.txn_details_id = txn.id
                    sf.updated_at = datetime.utcnow()
                    
                    # Generate PDF Receipt
                    receipt_no = f"REC{int(datetime.utcnow().timestamp())}{txn.id}"
                    pdf_relative_path = f"static/receipts/{receipt_no}.pdf"
                    
                    # Ensure directory exists
                    os.makedirs("static/receipts", exist_ok=True)
                    
                    await self.generate_pdf(txn, sf, receipt_no, pdf_relative_path)
                    
                    # Save receipt metadata
                    receipt = PaymentReceipt(
                        txn_details_id=txn.id,
                        receipt_no=receipt_no,
                        pdf_path=pdf_relative_path
                    )
                    db.add(receipt)
        else:
            txn.status_to_show = "Failed"
            txn.msg = callback_data.get("unmappedstatus", "Payment Failed")
            txn.msg1 = callback_data.get("error_Message", "Transaction Failed.")
            if udf2:
                sf_stmt = select(StudentFee).where(StudentFee.id == int(udf2))
                sf_res = await db.execute(sf_stmt)
                sf = sf_res.scalars().first()
                if sf:
                    sf.status = "Failed"
                    sf.txn_details_id = txn.id
                    sf.updated_at = datetime.utcnow()

        await db.flush()
        return status

    async def generate_pdf(self, txn: TransactionDetails, sf: StudentFee, receipt_no: str, file_path: str):
        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'ReceiptTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=1, # Center
            spaceAfter=15
        )
        
        meta_style = ParagraphStyle(
            'ReceiptMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor("#475569")
        )

        bold_label = ParagraphStyle(
            'BoldLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.HexColor("#1e293b")
        )

        # Header Title
        story.append(Paragraph("CAMPUS ACTIVE UNIVERSITY", title_style))
        story.append(Paragraph("<b>OFFICIAL PAYMENT RECEIPT</b>", ParagraphStyle('Sub', parent=title_style, fontSize=14, spaceAfter=20)))
        
        # Meta Table
        meta_data = [
            [Paragraph(f"<b>Receipt No:</b> {receipt_no}", meta_style), Paragraph(f"<b>Date:</b> {txn.txn_date.strftime('%d-%b-%Y')}", meta_style)],
            [Paragraph(f"<b>Transaction ID:</b> {txn.txnid}", meta_style), Paragraph(f"<b>Payment Mode:</b> PayU Gateway", meta_style)]
        ]
        meta_table = Table(meta_data, colWidths=[260, 260])
        meta_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW', (0,1), (1,1), 1, colors.HexColor("#cbd5e1")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Student Information Table
        story.append(Paragraph("STUDENT DETAILS", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#1e3a8a"), spaceAfter=8)))
        
        student_data = [
            [Paragraph("Name:", bold_label), Paragraph(txn.firstname, meta_style), Paragraph("Computer Code:", bold_label), Paragraph(str(txn.computer_code), meta_style)],
            [Paragraph("Enrollment No:", bold_label), Paragraph(txn.enrollment, meta_style), Paragraph("Semester:", bold_label), Paragraph(f"Semester {txn.semester}", meta_style)],
            [Paragraph("Email:", bold_label), Paragraph(txn.email, meta_style), Paragraph("Phone:", bold_label), Paragraph(str(txn.phone), meta_style)]
        ]
        student_table = Table(student_data, colWidths=[100, 160, 100, 160])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(student_table)
        story.append(Spacer(1, 25))

        # Payment Particulars Table
        story.append(Paragraph("PAYMENT PARTICULARS", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#1e3a8a"), spaceAfter=8)))
        
        particulars_data = [
            [Paragraph("<b>Description</b>", bold_label), Paragraph("<b>Amount (INR)</b>", bold_label)],
            [Paragraph(sf.fee_structure.title, meta_style), Paragraph(f"Rs. {sf.fee_structure.amount:,.2f}", meta_style)],
            [Paragraph("<b>Total Amount Paid</b>", bold_label), Paragraph(f"<b>Rs. {txn.amount:,.2f}</b>", bold_label)]
        ]
        particulars_table = Table(particulars_data, colWidths=[380, 140])
        particulars_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor("#f1f5f9")),
            ('LINEBELOW', (0,0), (1,0), 1, colors.HexColor("#cbd5e1")),
            ('LINEBELOW', (0,1), (1,1), 1, colors.HexColor("#f1f5f9")),
            ('LINEABOVE', (0,2), (1,2), 1, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 10),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ]))
        story.append(particulars_table)
        story.append(Spacer(1, 40))

        # Footer
        story.append(Paragraph("<i>This is a system generated receipt. No physical signature is required.</i>", ParagraphStyle('Foot', parent=styles['Normal'], alignment=1, fontSize=8, textColor=colors.HexColor("#64748b"))))
        
        doc.build(story)

    async def get_accountant_stats(self, db: AsyncSession) -> Dict[str, Any]:
        # Count revenue
        rev_stmt = select(func.sum(TransactionDetails.amount)).where(TransactionDetails.status_to_show == "Success")
        rev_res = await db.execute(rev_stmt)
        total_revenue = float(rev_res.scalar() or 0.0)
        
        # Count status occurrences
        stmt = select(TransactionDetails.status_to_show, func.count()).group_by(TransactionDetails.status_to_show)
        res = await db.execute(stmt)
        counts = {r[0].lower(): r[1] for r in res.all()}
        
        return {
            "total_revenue": total_revenue,
            "pending_count": counts.get("pending", 0),
            "success_count": counts.get("success", 0),
            "failed_count": counts.get("failed", 0) + counts.get("failure", 0),
            "refunded_count": counts.get("refunded", 0)
        }

payment_service = PaymentService()

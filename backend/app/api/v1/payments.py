import csv
import io
import os
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.auth import Login
from app.models.payment import TransactionDetails, StudentFee, PaymentReceipt
from app.models.system import Role
from app.models.staff import StaffRole
from app.schemas.response import StandardResponse
from app.schemas.payment import (
    StudentFeeResponse, PaymentInitiateResponse, TransactionResponse, PaymentStatsResponse
)
from app.services.payment import payment_service
from app.repositories import txn_details_repo, student_fee_repo, payment_receipt_repo

# PDF export imports
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter(prefix="/payments", tags=["Payment Gateway & Fees"])

# Helper roles verification
async def verify_accountant_role(
    current_user: Login = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Login:
    if not current_user.staff_id:
        raise HTTPException(status_code=403, detail="Access denied. Staff only.")
        
    stmt = select(Role.role_type).join(StaffRole, StaffRole.role_id == Role.id).where(StaffRole.staff_id == current_user.staff_id)
    res = await db.execute(stmt)
    roles = [r.lower() for r in res.scalars().all()]
    
    if "accountant" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Access denied. Accountant or Admin role required.")
        
    return current_user


# Student Endpoints
@router.get("/student/pending", response_model=StandardResponse[List[StudentFeeResponse]])
async def get_pending_fees(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    if not current_user.student_id:
        raise HTTPException(status_code=403, detail="Access denied. Students only.")
        
    items = await student_fee_repo.get_pending_fees(db, int(current_user.computer_code))
    return StandardResponse(data=[StudentFeeResponse.model_validate(x) for x in items])

@router.get("/student/history", response_model=StandardResponse[List[TransactionResponse]])
async def get_payment_history(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    if not current_user.student_id:
        raise HTTPException(status_code=403, detail="Access denied. Students only.")
        
    items = await txn_details_repo.get_student_history(db, int(current_user.computer_code))
    return StandardResponse(data=[TransactionResponse.model_validate(x) for x in items])

@router.post("/initiate/{fee_id}", response_model=StandardResponse[PaymentInitiateResponse])
async def initiate_payment(
    fee_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    if not current_user.student_id:
        raise HTTPException(status_code=403, detail="Access denied. Students only.")
        
    try:
        res = await payment_service.initiate_payment(db, fee_id, int(current_user.computer_code))
        await db.commit()
        return StandardResponse(message="Redirection payload generated", data=PaymentInitiateResponse.model_validate(res))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payu-callback")
async def payu_callback(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    form_data = await request.form()
    callback_dict = dict(form_data)
    
    # Process
    try:
        res_status = await payment_service.verify_and_process_callback(db, callback_dict)
        await db.commit()
    except Exception as e:
        await db.rollback()
        res_status = "error"
        
    # Redirect back to Student Fees screen
    frontend_host = os.getenv("FRONTEND_URL", "http://localhost:5173")
    txnid = callback_dict.get("txnid", "")
    redirect_url = f"{frontend_host}/dashboard/student/fees/pending?status={res_status}&txnid={txnid}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@router.get("/receipt/{txn_id}/download")
async def download_receipt(
    txn_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    # Check transaction exists
    txn = await txn_details_repo.get(db, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction record not found")
        
    # Security: student can only view their own receipts
    if current_user.student_id and int(current_user.computer_code) != txn.computer_code:
        raise HTTPException(status_code=403, detail="Access denied. Unauthorized to download this receipt.")
        
    # Get receipt metadata
    receipt = await payment_receipt_repo.get_by_txn_id(db, txn_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt document not generated/found for this transaction.")
        
    if not os.path.exists(receipt.pdf_path):
        raise HTTPException(status_code=404, detail="Physical PDF file does not exist on disk.")
        
    return FileResponse(
        path=receipt.pdf_path,
        media_type="application/pdf",
        filename=f"Receipt_{receipt.receipt_no}.pdf"
    )


# Accountant/Admin Dashboard Endpoints
@router.get("/accountant/stats", response_model=StandardResponse[PaymentStatsResponse])
async def get_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_accountant_role)
):
    stats = await payment_service.get_accountant_stats(db)
    return StandardResponse(data=PaymentStatsResponse.model_validate(stats))

@router.get("/accountant/transactions", response_model=StandardResponse[List[TransactionResponse]])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_accountant_role)
):
    items, total = await txn_details_repo.get_transactions_filtered(
        db, search=search, status=status, skip=skip, limit=limit
    )
    return StandardResponse(data=[TransactionResponse.model_validate(x) for x in items])

@router.get("/accountant/export/csv")
async def export_csv(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_accountant_role)
):
    items, _ = await txn_details_repo.get_transactions_filtered(
        db, search=search, status=status, skip=0, limit=1000
    )
    
    # Build CSV in memory stream
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Transaction ID", "Computer Code", "Enrollment", "Student Name", 
        "Email", "Phone", "Semester", "Fee Title", "Amount", "Status", "Date"
    ])
    
    for x in items:
        writer.writerow([
            x.txnid, x.computer_code, x.enrollment, x.firstname,
            x.email, x.phone, x.semester, x.productinfo, x.amount,
            x.status_to_show, x.txn_date.strftime("%d-%b-%Y")
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Transactions_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/accountant/export/pdf")
async def export_pdf(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_accountant_role)
):
    items, _ = await txn_details_repo.get_transactions_filtered(
        db, search=search, status=status, skip=0, limit=1000
    )
    
    # Generate temporary report path
    os.makedirs("static/receipts", exist_ok=True)
    report_path = f"static/receipts/Report_{int(datetime.utcnow().timestamp())}.pdf"
    
    # Setup document
    doc = SimpleDocTemplate(report_path, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1,
        spaceAfter=15
    )
    
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor("#334155")
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor("#0f172a")
    )

    story.append(Paragraph("CAMPUS ACTIVE UNIVERSITY - TRANSACTION LOG", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')}", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, spaceAfter=20)))
    
    # Construct grid data
    grid_data = [
        [
            Paragraph("<b>Txn ID</b>", table_header),
            Paragraph("<b>Roll No</b>", table_header),
            Paragraph("<b>Student</b>", table_header),
            Paragraph("<b>Semester</b>", table_header),
            Paragraph("<b>Fee Title</b>", table_header),
            Paragraph("<b>Amount</b>", table_header),
            Paragraph("<b>Status</b>", table_header),
            Paragraph("<b>Date</b>", table_header)
        ]
    ]
    
    for x in items:
        grid_data.append([
            Paragraph(x.txnid, table_text),
            Paragraph(str(x.computer_code), table_text),
            Paragraph(x.firstname[:20], table_text),
            Paragraph(f"Sem {x.semester}", table_text),
            Paragraph(x.productinfo[:25], table_text),
            Paragraph(f"Rs. {x.amount:.2f}", table_text),
            Paragraph(x.status_to_show, table_text),
            Paragraph(x.txn_date.strftime("%d-%b-%Y"), table_text)
        ])
        
    grid_table = Table(grid_data, colWidths=[110, 60, 110, 50, 130, 70, 70, 70])
    grid_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(grid_table)
    doc.build(story)
    
    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"Transactions_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

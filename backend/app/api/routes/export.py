"""Export endpoints for CSV/Excel."""

from datetime import date, datetime, timedelta
from typing import Optional
from io import BytesIO

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import xlsxwriter
import structlog

from app.db.session import get_db
from app.models.transaction import Transaction

router = APIRouter()
logger = structlog.get_logger()


@router.get("/transactions")
async def export_transactions(
    format: str = Query("csv", description="csv | xlsx"),
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Export transactions to CSV or Excel.
    """
    from datetime import datetime

    # Build query
    conditions = []
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)
    if status:
        conditions.append(Transaction.status == status)
    if from_date:
        conditions.append(Transaction.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        conditions.append(Transaction.created_at <= datetime.combine(to_date, datetime.max.time()))

    query = select(Transaction).order_by(Transaction.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))

    # Limit for safety
    query = query.limit(10000)

    result = await db.execute(query)
    transactions = result.scalars().all()

    # Column definitions (including USD amounts)
    columns = [
        ("ID", lambda t: str(t.id)),
        ("Source", lambda t: t.source),
        ("Source ID", lambda t: t.source_id),
        ("Reference ID", lambda t: t.reference_id or ""),
        ("Client Op ID", lambda t: t.client_operation_id or ""),
        ("Project", lambda t: t.project or ""),
        ("Amount", lambda t: float(t.amount)),
        ("Currency", lambda t: t.currency),
        ("Amount USD", lambda t: float(t.amount_usd) if t.amount_usd else 0.0),
        ("Fee", lambda t: float(t.fee) if t.fee else 0.0),
        ("Fee USD", lambda t: float(t.fee_usd) if t.fee_usd else 0.0),
        ("Exchange Rate", lambda t: float(t.exchange_rate) if t.exchange_rate else 0.0),
        ("Status", lambda t: t.status),
        ("Original Status", lambda t: t.original_status or ""),
        ("User Email", lambda t: t.user_email or ""),
        ("UTR", lambda t: t.utr or ""),
        ("Payment Method", lambda t: t.payment_method or ""),
        ("Created At", lambda t: t.created_at.isoformat() if t.created_at else ""),
        ("Updated At", lambda t: t.updated_at.isoformat() if t.updated_at else ""),
    ]

    if format == "xlsx":
        # Excel export
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Transactions")

        # Header format
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": "#4472C4",
            "font_color": "white",
        })

        # Write headers
        for col, (name, _) in enumerate(columns):
            worksheet.write(0, col, name, header_format)

        # Write data
        for row, txn in enumerate(transactions, start=1):
            for col, (_, getter) in enumerate(columns):
                worksheet.write(row, col, getter(txn))

        workbook.close()
        output.seek(0)

        filename = f"transactions_{date.today().isoformat()}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        # CSV export
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([name for name, _ in columns])

        # Write data
        for txn in transactions:
            writer.writerow([getter(txn) for _, getter in columns])

        output.seek(0)
        filename = f"transactions_{date.today().isoformat()}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.get("/payshack-report")
async def export_payshack_report(
    report_type: str = Query("payin", description="payin | payout"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
):
    """
    Generate and export PayShack report directly from API.
    
    Note: Reports are limited to 7-day periods.
    """
    from app.integrations.payshack import payshack_client
    
    # Default to last 7 days
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=6)
    
    # Enforce 7-day limit
    if (to_date - from_date).days > 7:
        raise HTTPException(
            status_code=400, 
            detail="Date range cannot exceed 7 days"
        )
    
    logger.info(
        "payshack_report_export",
        report_type=report_type,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
    )
    
    try:
        report_data = await payshack_client.generate_report(
            report_type=report_type,
            date_from=from_date.isoformat(),
            date_to=to_date.isoformat(),
        )
        
        filename = f"payshack_{report_type}_{from_date}_{to_date}.csv"
        
        return StreamingResponse(
            iter([report_data]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
        
    except Exception as e:
        logger.error("payshack_report_export_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payshack-clients")
async def export_payshack_clients(
    format: str = Query("csv", description="csv | xlsx"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export PayShack clients list.
    """
    from app.models.payshack_metadata import PayShackClient as PayShackClientModel
    
    result = await db.execute(
        select(PayShackClientModel).order_by(PayShackClientModel.name)
    )
    clients = result.scalars().all()
    
    columns = [
        ("Client ID", lambda c: c.client_id),
        ("Name", lambda c: c.name),
        ("Company Name", lambda c: c.company_name or ""),
        ("Email", lambda c: c.email or ""),
        ("Status", lambda c: c.status or ""),
        ("Balance", lambda c: float(c.balance or 0)),
        ("Wallet Balance", lambda c: float(c.wallet_balance or 0)),
        ("Currency", lambda c: c.currency),
        ("Commission Rate", lambda c: float(c.commission_rate or 0)),
        ("Is Active", lambda c: "Yes" if c.is_active else "No"),
        ("Synced At", lambda c: c.synced_at.isoformat() if c.synced_at else ""),
    ]
    
    if format == "xlsx":
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Clients")
        
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": "#28a745",
            "font_color": "white",
        })
        
        for col, (name, _) in enumerate(columns):
            worksheet.write(0, col, name, header_format)
        
        for row, client in enumerate(clients, start=1):
            for col, (_, getter) in enumerate(columns):
                worksheet.write(row, col, getter(client))
        
        workbook.close()
        output.seek(0)
        
        filename = f"payshack_clients_{date.today().isoformat()}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([name for name, _ in columns])
        
        for client in clients:
            writer.writerow([getter(client) for _, getter in columns])
        
        output.seek(0)
        filename = f"payshack_clients_{date.today().isoformat()}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.get("/metrics-summary")
async def export_metrics_summary(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    format: str = Query("csv", description="csv | xlsx"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export metrics summary by project and source.
    """
    from sqlalchemy import func, case
    
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=6)
    
    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    
    query = (
        select(
            Transaction.source,
            Transaction.project,
            func.count(Transaction.id).label("total_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.coalesce(
                func.sum(case((Transaction.status == "success", Transaction.amount))), 0
            ).label("success_amount"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
        )
        .where(and_(*conditions))
        .group_by(Transaction.source, Transaction.project)
        .order_by(func.sum(Transaction.amount).desc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    columns = [
        ("Source", lambda r: r.source),
        ("Project", lambda r: r.project or "unknown"),
        ("Total Count", lambda r: r.total_count),
        ("Total Amount", lambda r: float(r.total_amount or 0)),
        ("Success Count", lambda r: r.success_count),
        ("Success Amount", lambda r: float(r.success_amount or 0)),
        ("Failed Count", lambda r: r.failed_count),
        ("Conversion Rate", lambda r: round((r.success_count / r.total_count * 100) if r.total_count > 0 else 0, 2)),
    ]
    
    if format == "xlsx":
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Metrics Summary")
        
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": "#6f42c1",
            "font_color": "white",
        })
        
        for col, (name, _) in enumerate(columns):
            worksheet.write(0, col, name, header_format)
        
        for row_idx, row in enumerate(rows, start=1):
            for col, (_, getter) in enumerate(columns):
                worksheet.write(row_idx, col, getter(row))
        
        workbook.close()
        output.seek(0)
        
        filename = f"metrics_summary_{from_date}_{to_date}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([name for name, _ in columns])
        
        for row in rows:
            writer.writerow([getter(row) for _, getter in columns])
        
        output.seek(0)
        filename = f"metrics_summary_{from_date}_{to_date}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

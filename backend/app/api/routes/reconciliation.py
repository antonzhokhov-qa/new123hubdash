"""Reconciliation endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.reconciliation import ReconciliationRun, ReconciliationResult
from app.schemas.reconciliation import (
    ReconciliationSummary,
    DiscrepancyResponse,
    DiscrepancyListResponse,
    ReconciliationRunRequest,
)

router = APIRouter()


@router.get("/summary", response_model=ReconciliationSummary)
async def get_reconciliation_summary(
    recon_date: date = Query(..., description="Reconciliation date"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get reconciliation summary for a specific date.
    """
    result = await db.execute(
        select(ReconciliationRun)
        .where(ReconciliationRun.recon_date == recon_date)
        .order_by(ReconciliationRun.started_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()

    if not run:
        # No reconciliation run yet
        return ReconciliationSummary(
            recon_date=recon_date,
            status="not_run",
            total_vima=0,
            total_payshack=0,
            matched=0,
            discrepancies=0,
            missing_vima=0,
            missing_payshack=0,
            match_rate=0,
            discrepancy_rate=0,
        )

    total = run.total_vima + run.total_payshack
    match_rate = (run.matched / total * 100) if total > 0 else 0
    discrepancy_rate = (run.discrepancies / total * 100) if total > 0 else 0

    return ReconciliationSummary(
        recon_date=run.recon_date,
        run_id=run.id,
        started_at=run.started_at,
        completed_at=run.completed_at,
        status=run.status,
        total_vima=run.total_vima,
        total_payshack=run.total_payshack,
        matched=run.matched,
        discrepancies=run.discrepancies,
        missing_vima=run.missing_vima,
        missing_payshack=run.missing_payshack,
        match_rate=round(match_rate, 2),
        discrepancy_rate=round(discrepancy_rate, 2),
    )


@router.get("/discrepancies", response_model=DiscrepancyListResponse)
async def list_discrepancies(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    match_status: Optional[str] = Query(None, description="discrepancy | missing_vima | missing_payshack"),
    discrepancy_type: Optional[str] = Query(None, description="amount | status | time"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List reconciliation discrepancies with filters.
    """
    conditions = []
    
    if from_date:
        conditions.append(ReconciliationResult.recon_date >= from_date)
    if to_date:
        conditions.append(ReconciliationResult.recon_date <= to_date)
    if match_status:
        conditions.append(ReconciliationResult.match_status == match_status)
    else:
        # Exclude matched records by default
        conditions.append(ReconciliationResult.match_status != "matched")
    if discrepancy_type:
        conditions.append(ReconciliationResult.discrepancy_type == discrepancy_type)

    # Count query
    count_query = select(func.count(ReconciliationResult.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Data query
    query = select(ReconciliationResult).order_by(
        ReconciliationResult.recon_date.desc(),
        ReconciliationResult.created_at.desc(),
    )
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return DiscrepancyListResponse(
        items=[DiscrepancyResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("/run")
async def run_reconciliation(
    request: ReconciliationRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger reconciliation for a specific date.
    """
    from app.services.reconciliation_service import run_reconciliation_for_date

    # Check if already running
    result = await db.execute(
        select(ReconciliationRun)
        .where(
            and_(
                ReconciliationRun.recon_date == request.date,
                ReconciliationRun.status == "running",
            )
        )
    )
    existing_run = result.scalar_one_or_none()

    if existing_run and not request.force:
        raise HTTPException(
            status_code=400,
            detail="Reconciliation already running for this date",
        )

    background_tasks.add_task(run_reconciliation_for_date, request.date)

    return {
        "message": "Reconciliation started",
        "date": request.date.isoformat(),
    }

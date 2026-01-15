"""Transaction endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionResponse,
    TransactionListResponse,
)

router = APIRouter()


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    source: Optional[str] = Query(None, description="Filter by source: vima | payshack"),
    project: Optional[str] = Query(None, description="Filter by project"),
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    search: Optional[str] = Query(None, description="Search by ID, email, etc."),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order: asc | desc"),
    db: AsyncSession = Depends(get_db),
):
    """
    List transactions with filters and pagination.
    """
    # Build query
    query = select(Transaction)
    count_query = select(func.count(Transaction.id))

    # Apply filters
    conditions = []
    
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)
    if status:
        conditions.append(Transaction.status == status)
    if from_date:
        conditions.append(Transaction.created_at >= from_date)
    if to_date:
        conditions.append(Transaction.created_at <= to_date)
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Transaction.source_id.ilike(search_pattern),
                Transaction.reference_id.ilike(search_pattern),
                Transaction.client_operation_id.ilike(search_pattern),
                Transaction.user_email.ilike(search_pattern),
                Transaction.utr.ilike(search_pattern),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = getattr(Transaction, sort_by, Transaction.created_at)
    if order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute
    result = await db.execute(query)
    transactions = result.scalars().all()

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit if total > 0 else 0,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single transaction by ID."""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse.model_validate(transaction)

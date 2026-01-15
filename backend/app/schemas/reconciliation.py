"""Reconciliation schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel


class ReconciliationSummary(BaseModel):
    """Summary of reconciliation for a date."""

    recon_date: date
    run_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str  # running | completed | failed

    # Counts
    total_vima: int
    total_payshack: int
    matched: int
    discrepancies: int
    missing_vima: int
    missing_payshack: int

    # Rates
    match_rate: float  # matched / total * 100
    discrepancy_rate: float

    # Amounts
    matched_amount: Optional[Decimal] = None
    discrepancy_amount: Optional[Decimal] = None


class DiscrepancyResponse(BaseModel):
    """Single discrepancy record."""

    id: UUID
    recon_date: date
    client_operation_id: Optional[str] = None

    match_status: str  # discrepancy | missing_vima | missing_payshack
    discrepancy_type: Optional[str] = None  # amount | status | time

    vima_amount: Optional[Decimal] = None
    payshack_amount: Optional[Decimal] = None
    amount_diff: Optional[Decimal] = None

    vima_status: Optional[str] = None
    payshack_status: Optional[str] = None

    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DiscrepancyListResponse(BaseModel):
    """Paginated list of discrepancies."""

    items: List[DiscrepancyResponse]
    total: int
    page: int
    limit: int


class ReconciliationRunRequest(BaseModel):
    """Request to run reconciliation."""

    date: date
    force: bool = False  # Re-run even if already completed

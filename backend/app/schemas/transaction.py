"""Transaction schemas."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    """Base transaction schema."""

    source: str
    source_id: str
    reference_id: Optional[str] = None
    client_operation_id: Optional[str] = None
    order_id: Optional[str] = None
    project: Optional[str] = None
    amount: Decimal
    currency: str = "INR"
    amount_usd: Optional[Decimal] = None  # Amount in USD
    fee: Optional[Decimal] = None
    fee_usd: Optional[Decimal] = None  # Fee in USD
    exchange_rate: Optional[Decimal] = None  # Exchange rate used
    status: str
    original_status: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    country: Optional[str] = None
    utr: Optional[str] = None
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class TransactionResponse(TransactionBase):
    """Transaction response schema."""

    id: UUID
    ingested_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""

    items: List[TransactionResponse]
    total: int
    page: int
    limit: int
    pages: int


class TransactionFilters(BaseModel):
    """Transaction filter parameters."""

    source: Optional[str] = Field(None, description="Filter by source: vima | payshack")
    project: Optional[str] = Field(None, description="Filter by project")
    status: Optional[str] = Field(None, description="Filter by status: success | failed | pending")
    from_date: Optional[date] = Field(None, description="Start date")
    to_date: Optional[date] = Field(None, description="End date")
    search: Optional[str] = Field(None, description="Search by ID, email, etc.")
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)
    sort_by: str = Field("created_at", description="Sort field")
    order: str = Field("desc", description="Sort order: asc | desc")

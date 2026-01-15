"""Reconciliation models."""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    Date,
    Integer,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.session import Base


class ReconciliationRun(Base):
    """Track reconciliation runs."""

    __tablename__ = "reconciliation_runs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    recon_date = Column(Date, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))

    # Summary
    total_vima = Column(Integer, default=0)
    total_payshack = Column(Integer, default=0)
    matched = Column(Integer, default=0)
    discrepancies = Column(Integer, default=0)
    missing_vima = Column(Integer, default=0)
    missing_payshack = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="running")  # running | completed | failed
    error_message = Column(String(500))

    def __repr__(self) -> str:
        return f"<ReconciliationRun {self.id} date={self.recon_date} status={self.status}>"


class ReconciliationResult(Base):
    """Individual reconciliation results."""

    __tablename__ = "reconciliation_results"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Run info
    recon_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_runs.id"),
        nullable=False,
        index=True,
    )
    recon_date = Column(Date, nullable=False, index=True)

    # Transaction references
    vima_txn_id = Column(UUID(as_uuid=True))
    payshack_txn_id = Column(UUID(as_uuid=True))
    client_operation_id = Column(String(255), index=True)

    # Match result
    match_status = Column(String(30), nullable=False, index=True)
    # Values: matched | discrepancy | missing_vima | missing_payshack

    # Discrepancy details
    discrepancy_type = Column(String(50))  # amount | status | time | missing

    # Values comparison
    vima_amount = Column(Numeric(18, 4))
    payshack_amount = Column(Numeric(18, 4))
    amount_diff = Column(Numeric(18, 4))

    vima_status = Column(String(30))
    payshack_status = Column(String(30))

    # Additional details
    details = Column(JSONB)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        Index("idx_recon_date_status", "recon_date", "match_status"),
    )

    def __repr__(self) -> str:
        return f"<ReconciliationResult {self.id} status={self.match_status}>"

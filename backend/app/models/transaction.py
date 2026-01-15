"""Transaction model."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.session import Base


class Transaction(Base):
    """Unified transaction model for all sources."""

    __tablename__ = "transactions"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Source identification
    source = Column(String(20), nullable=False, index=True)  # 'vima' | 'payshack'
    source_id = Column(String(255), nullable=False)  # Original ID from source

    # Matching keys
    reference_id = Column(String(255), index=True)  # Vima reference_id
    client_operation_id = Column(String(255), index=True)  # c_id (KEY FOR MATCHING!)
    order_id = Column(String(255), index=True)  # PayShack order_id

    # Business data
    project = Column(String(100), index=True)  # monetix, caroussel, 91game
    merchant_id = Column(String(255))

    # Financial
    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    fee = Column(Numeric(18, 4))
    
    # USD conversion
    amount_usd = Column(Numeric(18, 4))  # Amount in USD
    fee_usd = Column(Numeric(18, 4))  # Fee in USD
    exchange_rate = Column(Numeric(12, 8))  # Rate used for conversion

    # Status
    status = Column(String(30), nullable=False, index=True)  # success | failed | pending
    original_status = Column(String(50))  # Original from source

    # Payer info
    user_id = Column(String(255))
    user_email = Column(String(255))
    user_phone = Column(String(50))
    user_name = Column(String(255))
    country = Column(String(2))

    # UTR (PayShack specific)
    utr = Column(String(100))

    # Payment method
    payment_method = Column(String(50))
    payment_product = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Cursors (Vima specific)
    source_create_cursor = Column(String(100))
    source_update_cursor = Column(String(100))

    # Raw data storage
    raw_data = Column(JSONB)

    # Deduplication
    data_hash = Column(String(64), unique=True, index=True)

    # System timestamps
    ingested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("NOW()"),
    )

    # Indexes
    __table_args__ = (
        Index("idx_txn_source_date", "source", "created_at"),
        Index("idx_txn_source_source_id", "source", "source_id"),
        Index("idx_txn_project_status", "project", "status"),
        Index("idx_txn_created_desc", created_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.id} source={self.source} amount={self.amount} status={self.status}>"

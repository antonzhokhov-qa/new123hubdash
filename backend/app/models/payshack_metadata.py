"""PayShack metadata models.

Stores PayShack clients, balances, and service providers
for dashboard analytics.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    Boolean,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.session import Base


class PayShackClient(Base):
    """
    PayShack client/merchant.
    
    Synced from /indigate-core-svc/api/v1/client/fetch-all-client
    """
    
    __tablename__ = "payshack_clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # PayShack identifiers
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    reseller_id = Column(String(100), nullable=True, index=True)
    
    # Client info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(50), nullable=True)  # active, inactive, etc.
    is_active = Column(Boolean, default=True)
    
    # Balance info
    balance = Column(Numeric(20, 4), default=0)
    wallet_balance = Column(Numeric(20, 4), default=0)
    currency = Column(String(10), default="INR")
    
    # Commission
    commission_rate = Column(Numeric(10, 4), nullable=True)
    
    # Raw data
    raw_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_payshack_clients_reseller", "reseller_id"),
        Index("ix_payshack_clients_status", "status"),
    )


class PayShackReseller(Base):
    """
    PayShack reseller.
    
    Synced from /indigate-core-svc/api/v1/reseller/fetch-all-reseller
    """
    
    __tablename__ = "payshack_resellers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # PayShack identifiers
    reseller_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=True)
    
    # Reseller info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Balance
    balance = Column(Numeric(20, 4), default=0)
    currency = Column(String(10), default="INR")
    
    # Raw data
    raw_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PayShackServiceProvider(Base):
    """
    PayShack service provider.
    
    Synced from /indigate-core-svc/api/v1/service-provider/fetch-all-sp
    """
    
    __tablename__ = "payshack_service_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # PayShack identifiers
    provider_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Provider info
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Capabilities
    supports_payin = Column(Boolean, default=True)
    supports_payout = Column(Boolean, default=True)
    
    # Raw data
    raw_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PayShackBalanceSnapshot(Base):
    """
    Balance snapshot for historical tracking.
    
    Created periodically to track balance changes over time.
    """
    
    __tablename__ = "payshack_balance_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference
    entity_type = Column(String(50), nullable=False)  # "client" or "reseller"
    entity_id = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(255), nullable=True)
    
    # Balance
    balance = Column(Numeric(20, 4), nullable=False)
    currency = Column(String(10), default="INR")
    
    # Timestamp
    snapshot_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_balance_snapshots_entity", "entity_type", "entity_id"),
        Index("ix_balance_snapshots_time", "snapshot_at"),
    )

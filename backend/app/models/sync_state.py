"""Sync state model for tracking ETL progress."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, text

from app.db.session import Base


class SyncState(Base):
    """Track synchronization state for each source."""

    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False, unique=True)  # 'vima' | 'payshack'

    # Cursors (Vima specific)
    last_create_cursor = Column(String(100))
    last_update_cursor = Column(String(100))

    # Timestamps
    last_sync_at = Column(DateTime(timezone=True))
    last_successful_sync = Column(DateTime(timezone=True))

    # Status
    sync_status = Column(String(20), default="idle")  # idle | running | failed
    error_message = Column(Text)
    records_synced = Column(Integer, default=0)
    total_records = Column(Integer, default=0)

    # Metadata
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("NOW()"),
    )

    def __repr__(self) -> str:
        return f"<SyncState {self.source} status={self.sync_status}>"

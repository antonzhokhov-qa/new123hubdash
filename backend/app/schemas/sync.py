"""Sync status schemas."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class SourceSyncStatus(BaseModel):
    """Sync status for a single source."""

    source: str
    status: str  # idle | running | failed
    last_sync_at: Optional[datetime] = None
    last_successful_sync: Optional[datetime] = None
    records_synced: int = 0
    total_records: int = 0
    error_message: Optional[str] = None
    next_sync_in_seconds: Optional[int] = None


class SyncStatusResponse(BaseModel):
    """Complete sync status response."""

    sources: List[SourceSyncStatus]
    overall_status: str  # healthy | syncing | error


class SyncTriggerRequest(BaseModel):
    """Request to trigger manual sync."""

    source: Optional[str] = None  # vima | payshack | None for all
    force: bool = False  # Force sync even if running

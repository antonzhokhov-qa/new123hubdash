"""Sync status and control endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.sync_state import SyncState
from app.schemas.sync import (
    SyncStatusResponse,
    SourceSyncStatus,
    SyncTriggerRequest,
)
from app.config import settings

router = APIRouter()


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Get synchronization status for all sources.
    Called frequently by frontend to show sync indicator.
    """
    result = await db.execute(select(SyncState))
    states = result.scalars().all()

    sources = []
    overall_status = "healthy"

    for state in states:
        # Calculate next sync time
        next_sync = None
        if state.last_sync_at:
            interval = (
                settings.vima_sync_interval_seconds
                if state.source == "vima"
                else settings.payshack_sync_interval_seconds
            )
            from datetime import datetime, timezone
            elapsed = (datetime.now(timezone.utc) - state.last_sync_at).total_seconds()
            next_sync = max(0, int(interval - elapsed))

        sources.append(
            SourceSyncStatus(
                source=state.source,
                status=state.sync_status,
                last_sync_at=state.last_sync_at,
                last_successful_sync=state.last_successful_sync,
                records_synced=state.records_synced or 0,
                total_records=state.total_records or 0,
                error_message=state.error_message,
                next_sync_in_seconds=next_sync,
            )
        )

        if state.sync_status == "failed":
            overall_status = "error"
        elif state.sync_status == "running" and overall_status != "error":
            overall_status = "syncing"

    return SyncStatusResponse(
        sources=sources,
        overall_status=overall_status,
    )


@router.post("/trigger")
async def trigger_sync(
    request: SyncTriggerRequest = SyncTriggerRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger synchronization.
    """
    from app.etl.scheduler import trigger_vima_sync, trigger_payshack_sync

    sources_triggered = []

    if request.source is None or request.source == "vima":
        # Check if already running
        result = await db.execute(
            select(SyncState).where(SyncState.source == "vima")
        )
        state = result.scalar_one_or_none()
        
        if state and state.sync_status == "running" and not request.force:
            pass  # Skip, already running
        else:
            background_tasks.add_task(trigger_vima_sync)
            sources_triggered.append("vima")

    if request.source is None or request.source == "payshack":
        result = await db.execute(
            select(SyncState).where(SyncState.source == "payshack")
        )
        state = result.scalar_one_or_none()
        
        if state and state.sync_status == "running" and not request.force:
            pass
        else:
            background_tasks.add_task(trigger_payshack_sync)
            sources_triggered.append("payshack")

    return {
        "message": "Sync triggered",
        "sources": sources_triggered,
    }

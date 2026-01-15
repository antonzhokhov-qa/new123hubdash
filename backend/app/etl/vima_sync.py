"""Vima ETL Sync Service."""

import asyncio
import time
from datetime import date, datetime, timezone, timedelta
from typing import Dict, Any, List

import structlog
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.db.session import async_session_maker
from app.models.transaction import Transaction
from app.models.sync_state import SyncState
from app.integrations.vima.client import VimaClient, VimaAPIError
from app.integrations.vima.normalizer import VimaNormalizer
from app.config import settings
from app.api.websocket import (
    broadcast_sync_started,
    broadcast_sync_progress,
    broadcast_sync_completed,
    broadcast_new_transactions,
)

logger = structlog.get_logger()


class VimaSyncService:
    """
    Service for synchronizing data from Vima API.
    
    Strategy:
    1. Get last cursor from sync_state
    2. Fetch new operations using cursor
    3. Normalize and upsert to database
    4. Update cursor in sync_state
    5. Broadcast updates via WebSocket
    """

    def __init__(self):
        self.client = VimaClient()
        self.normalizer = VimaNormalizer()
        self.source = "vima"

    async def sync(self) -> Dict[str, Any]:
        """
        Run synchronization.
        
        Returns:
            Dict with sync results
        """
        start_time = time.time()
        records_synced = 0
        
        async with async_session_maker() as session:
            try:
                # Update status to running
                await self._update_sync_state(
                    session,
                    sync_status="running",
                    error_message=None,
                )
                await session.commit()
                
                # Broadcast sync started
                await broadcast_sync_started(self.source)

                # Get last cursor
                state = await self._get_sync_state(session)
                cursor = state.last_create_cursor if state else None

                logger.info("vima_sync_starting", cursor=cursor)

                # Fetch and process operations using cursor-based pagination
                batch_num = 0
                async for operations in self.client.get_all_operations(
                    from_operation_create_id=cursor,
                    batch_size=100,
                    max_batches=settings.vima_max_batches,  # Configurable limit
                ):
                    if not operations:
                        break
                    batch_num += 1
                    
                    # Normalize operations
                    normalized = []
                    for op in operations:
                        try:
                            normalized.append(self.normalizer.normalize(op))
                        except Exception as e:
                            logger.warning(
                                "vima_normalize_skip",
                                operation_id=op.get("operation_id"),
                                error=str(e),
                            )

                    if normalized:
                        # Upsert to database
                        await self._upsert_transactions(session, normalized)
                        records_synced += len(normalized)

                        # Update cursor to last record
                        last_cursor = normalized[-1].get("source_create_cursor")
                        if last_cursor:
                            await self._update_sync_state(
                                session,
                                last_create_cursor=last_cursor,
                                records_synced=records_synced,
                            )

                        await session.commit()

                        # Broadcast progress
                        await broadcast_sync_progress(
                            self.source,
                            records_synced,
                            records_synced,  # We don't know total
                        )

                        logger.info(
                            "vima_batch_processed",
                            batch=batch_num,
                            records=len(normalized),
                            total=records_synced,
                        )

                # Mark sync as successful
                duration_ms = int((time.time() - start_time) * 1000)
                await self._update_sync_state(
                    session,
                    sync_status="idle",
                    last_sync_at=datetime.now(timezone.utc),
                    last_successful_sync=datetime.now(timezone.utc),
                    records_synced=records_synced,
                )
                await session.commit()

                # Broadcast completion
                await broadcast_sync_completed(self.source, records_synced)
                
                if records_synced > 0:
                    await broadcast_new_transactions(records_synced, self.source)

                return {
                    "status": "success",
                    "records_synced": records_synced,
                    "duration_ms": duration_ms,
                }

            except Exception as e:
                logger.error("vima_sync_failed", error=str(e))
                
                # Mark as failed
                await self._update_sync_state(
                    session,
                    sync_status="failed",
                    error_message=str(e)[:500],
                )
                await session.commit()

                return {
                    "status": "failed",
                    "error": str(e),
                    "records_synced": records_synced,
                }

    async def _get_sync_state(self, session) -> SyncState:
        """Get current sync state."""
        result = await session.execute(
            select(SyncState).where(SyncState.source == self.source)
        )
        state = result.scalar_one_or_none()
        
        if not state:
            # Create initial state
            state = SyncState(source=self.source, sync_status="idle")
            session.add(state)
            await session.commit()
            await session.refresh(state)
        
        return state

    async def _update_sync_state(self, session, **kwargs):
        """Update sync state."""
        result = await session.execute(
            select(SyncState).where(SyncState.source == self.source)
        )
        state = result.scalar_one_or_none()
        
        if state:
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            state.updated_at = datetime.now(timezone.utc)

    async def _upsert_transactions(
        self,
        session,
        transactions: List[Dict[str, Any]],
    ):
        """
        Upsert transactions with deduplication.
        
        Uses ON CONFLICT DO UPDATE on data_hash.
        """
        if not transactions:
            return

        # Build insert statement with ON CONFLICT
        stmt = insert(Transaction).values(transactions)
        
        # On conflict (data_hash), update status and timestamps
        stmt = stmt.on_conflict_do_update(
            index_elements=["data_hash"],
            set_={
                "status": stmt.excluded.status,
                "original_status": stmt.excluded.original_status,
                "updated_at": stmt.excluded.updated_at,
                "completed_at": stmt.excluded.completed_at,
                "source_update_cursor": stmt.excluded.source_update_cursor,
                "raw_data": stmt.excluded.raw_data,
            },
        )

        await session.execute(stmt)

    async def historical_sync(self, days: int = 7) -> Dict[str, Any]:
        """
        Load historical data for specified number of days.
        
        Uses date-based loading instead of cursor for complete data fetch.
        Loads ALL merchants and transactions for each day.
        
        Args:
            days: Number of days to load (default 7)
            
        Returns:
            Dict with sync results
        """
        start_time = time.time()
        total_records = 0
        
        logger.info("vima_historical_sync_starting", days=days)
        
        async with async_session_maker() as session:
            try:
                await self._update_sync_state(
                    session,
                    sync_status="running",
                    error_message=None,
                )
                await session.commit()
                
                await broadcast_sync_started(self.source)
                
                # Iterate through each day from oldest to newest
                for day_offset in range(days, -1, -1):
                    target_date = date.today() - timedelta(days=day_offset)
                    
                    logger.info(
                        "vima_historical_sync_date",
                        date=target_date.isoformat(),
                        day_offset=day_offset,
                    )
                    
                    day_records = await self._sync_date(session, target_date)
                    total_records += day_records
                    
                    await broadcast_sync_progress(
                        self.source,
                        days - day_offset + 1,
                        days + 1,
                    )
                    
                    # Small delay between days
                    await asyncio.sleep(0.5)
                
                # Update sync state
                duration_ms = int((time.time() - start_time) * 1000)
                await self._update_sync_state(
                    session,
                    sync_status="idle",
                    last_sync_at=datetime.now(timezone.utc),
                    last_successful_sync=datetime.now(timezone.utc),
                    records_synced=total_records,
                )
                await session.commit()
                
                await broadcast_sync_completed(self.source, total_records)
                
                logger.info(
                    "vima_historical_sync_completed",
                    total_records=total_records,
                    days=days,
                    duration_ms=duration_ms,
                )
                
                return {
                    "status": "success",
                    "records_synced": total_records,
                    "days": days,
                    "duration_ms": duration_ms,
                }
                
            except Exception as e:
                logger.error("vima_historical_sync_failed", error=str(e))
                
                await self._update_sync_state(
                    session,
                    sync_status="failed",
                    error_message=str(e)[:500],
                )
                await session.commit()
                
                return {
                    "status": "failed",
                    "error": str(e),
                    "records_synced": total_records,
                }

    async def _sync_date(self, session, target_date: date) -> int:
        """
        Sync all operations for a specific date.
        
        Fetches ALL pages of data for the given date to ensure
        all merchants are included.
        
        Returns:
            Number of records synced for this date
        """
        records_synced = 0
        cursor = None
        batch_count = 0
        max_batches = 200  # Safety limit per day
        
        while batch_count < max_batches:
            try:
                # Fetch operations for specific date
                operations = await self.client.get_operations(
                    date_filter=target_date,
                    count=100,
                    descending=False,
                    from_operation_create_id=cursor,
                )
                
                if not operations:
                    break
                
                # Normalize operations
                normalized = []
                for op in operations:
                    try:
                        normalized.append(self.normalizer.normalize(op))
                    except Exception as e:
                        logger.warning(
                            "vima_historical_normalize_skip",
                            operation_id=op.get("operation_id"),
                            error=str(e),
                        )
                
                if normalized:
                    await self._upsert_transactions(session, normalized)
                    records_synced += len(normalized)
                    
                    # Update cursor for next page
                    last_cursor = normalized[-1].get("source_create_cursor")
                    if last_cursor and last_cursor != cursor:
                        cursor = last_cursor
                    else:
                        break
                    
                    await session.commit()
                else:
                    break
                
                batch_count += 1
                
                # Small delay between batches
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(
                    "vima_historical_date_batch_error",
                    date=target_date.isoformat(),
                    batch=batch_count,
                    error=str(e),
                )
                break
        
        logger.info(
            "vima_historical_date_complete",
            date=target_date.isoformat(),
            records=records_synced,
            batches=batch_count,
        )
        
        return records_synced

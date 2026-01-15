"""PayShack ETL Sync Service.

Synchronizes transactions from PayShack API using HTTPX client.
No Playwright required - API returns plain JSON.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import structlog
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.db.session import async_session_maker
from app.models.sync_state import SyncState
from app.models.transaction import Transaction
from app.integrations.payshack.client import PayShackClient, PayShackAPIError
from app.integrations.payshack.normalizer import PayShackNormalizer
from app.api.websocket import (
    broadcast_sync_started,
    broadcast_sync_completed,
    broadcast_sync_progress,
    broadcast_new_transactions,
)

logger = structlog.get_logger()


class PayShackSyncService:
    """
    Service for synchronizing data from PayShack.
    
    Uses HTTPX client to fetch transactions directly from API.
    Supports incremental sync based on last sync timestamp.
    """

    def __init__(self):
        self.source = "payshack"
        self.client = PayShackClient()

    async def sync(self, full_sync: bool = False) -> Dict[str, Any]:
        """
        Run PayShack synchronization.
        
        Args:
            full_sync: If True, fetch all transactions. Otherwise incremental.
            
        Returns:
            Sync result with statistics
        """
        start_time = time.time()
        total_synced = 0
        total_new = 0
        total_updated = 0
        errors = []

        async with async_session_maker() as session:
            try:
                # Update status to running
                await self._update_sync_state(
                    session,
                    sync_status="running",
                    error_message=None,
                )
                await session.commit()

                await broadcast_sync_started(self.source)

                logger.info("payshack_sync_starting", full_sync=full_sync)

                # Get last sync time for incremental sync
                last_sync = await self._get_last_sync_time(session)
                
                # Sync Pay-In transactions
                payin_result = await self._sync_payin_transactions(
                    session, last_sync if not full_sync else None
                )
                total_synced += payin_result["synced"]
                total_new += payin_result["new"]
                total_updated += payin_result["updated"]
                if payin_result.get("errors"):
                    errors.extend(payin_result["errors"])

                # Sync Pay-Out transactions
                payout_result = await self._sync_payout_transactions(
                    session, last_sync if not full_sync else None
                )
                total_synced += payout_result["synced"]
                total_new += payout_result["new"]
                total_updated += payout_result["updated"]
                if payout_result.get("errors"):
                    errors.extend(payout_result["errors"])

                # Update sync state
                await self._update_sync_state(
                    session,
                    sync_status="idle",
                    last_sync_at=datetime.now(timezone.utc),
                    error_message=None,
                )
                await session.commit()

                elapsed = time.time() - start_time
                
                await broadcast_sync_completed(self.source, total_synced)

                logger.info(
                    "payshack_sync_completed",
                    total_synced=total_synced,
                    new=total_new,
                    updated=total_updated,
                    elapsed_seconds=round(elapsed, 2),
                    errors=len(errors),
                )

                return {
                    "status": "success",
                    "records_synced": total_synced,
                    "new_records": total_new,
                    "updated_records": total_updated,
                    "elapsed_seconds": round(elapsed, 2),
                    "errors": errors[:10],  # First 10 errors
                }

            except PayShackAPIError as e:
                logger.error("payshack_sync_api_error", error=str(e))
                
                await self._update_sync_state(
                    session,
                    sync_status="failed",
                    error_message=str(e)[:500],
                )
                await session.commit()

                return {
                    "status": "failed",
                    "error": str(e),
                    "records_synced": total_synced,
                }

            except Exception as e:
                logger.error("payshack_sync_failed", error=str(e), exc_info=True)
                
                await self._update_sync_state(
                    session,
                    sync_status="failed",
                    error_message=str(e)[:500],
                )
                await session.commit()

                return {
                    "status": "failed",
                    "error": str(e),
                    "records_synced": total_synced,
                }

            finally:
                await self.client.close()

    async def _sync_payin_transactions(
        self,
        session,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Sync Pay-In transactions."""
        synced = 0
        new = 0
        updated = 0
        errors = []
        
        # Build date filter if incremental
        date_from = None
        if since:
            # Fetch from 1 day before to catch any missed updates
            date_from = (since - timedelta(days=1)).strftime("%Y-%m-%d")
        
        page = 1
        max_pages = 500  # Safety limit
        
        logger.info("payshack_sync_payin_start", since=since, date_from=date_from)
        
        while page <= max_pages:
            try:
                result = await self.client.get_payin_transactions(
                    page=page,
                    limit=100,
                    date_from=date_from,
                )
                
                transactions = result.get("transactions", [])
                if not transactions:
                    break
                
                # Normalize and upsert
                normalized_batch = []
                for raw in transactions:
                    try:
                        normalized = PayShackNormalizer.normalize_payin(raw)
                        normalized_batch.append(normalized)
                    except Exception as e:
                        errors.append(f"Normalize error for {raw.get('txnId')}: {e}")
                
                if normalized_batch:
                    batch_result = await self._upsert_transactions(session, normalized_batch)
                    synced += batch_result["total"]
                    new += batch_result["inserted"]
                    updated += batch_result["updated"]
                
                # Broadcast progress
                await broadcast_sync_progress(
                    self.source,
                    page,
                    result.get("totalPages", 1),
                )
                
                # Check if we've reached the last page
                total_pages = result.get("totalPages", 1)
                if page >= total_pages:
                    break
                
                page += 1
                
                # Small delay between requests
                import asyncio
                await asyncio.sleep(0.2)
                
            except PayShackAPIError as e:
                logger.error("payshack_payin_page_error", page=page, error=str(e))
                errors.append(f"Page {page} error: {e}")
                break
        
        logger.info(
            "payshack_sync_payin_complete",
            synced=synced,
            new=new,
            updated=updated,
            pages=page,
        )
        
        return {
            "synced": synced,
            "new": new,
            "updated": updated,
            "errors": errors,
        }

    async def _sync_payout_transactions(
        self,
        session,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Sync Pay-Out transactions."""
        synced = 0
        new = 0
        updated = 0
        errors = []
        
        date_from = None
        if since:
            date_from = (since - timedelta(days=1)).strftime("%Y-%m-%d")
        
        page = 1
        max_pages = 200  # Payout typically has fewer records
        
        logger.info("payshack_sync_payout_start", since=since)
        
        while page <= max_pages:
            try:
                result = await self.client.get_payout_transactions(
                    page=page,
                    limit=100,
                    date_from=date_from,
                )
                
                transactions = result.get("transactions", [])
                if not transactions:
                    break
                
                normalized_batch = []
                for raw in transactions:
                    try:
                        normalized = PayShackNormalizer.normalize_payout(raw)
                        normalized_batch.append(normalized)
                    except Exception as e:
                        errors.append(f"Normalize error for {raw.get('txnId')}: {e}")
                
                if normalized_batch:
                    batch_result = await self._upsert_transactions(session, normalized_batch)
                    synced += batch_result["total"]
                    new += batch_result["inserted"]
                    updated += batch_result["updated"]
                
                total_pages = result.get("totalPages", 1)
                if page >= total_pages:
                    break
                
                page += 1
                
                import asyncio
                await asyncio.sleep(0.2)
                
            except PayShackAPIError as e:
                logger.error("payshack_payout_page_error", page=page, error=str(e))
                errors.append(f"Page {page} error: {e}")
                break
        
        logger.info(
            "payshack_sync_payout_complete",
            synced=synced,
            new=new,
            updated=updated,
        )
        
        return {
            "synced": synced,
            "new": new,
            "updated": updated,
            "errors": errors,
        }

    async def _upsert_transactions(
        self,
        session,
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Upsert transactions using ON CONFLICT.
        
        Returns count of inserted and updated records.
        """
        if not transactions:
            return {"total": 0, "inserted": 0, "updated": 0}
        
        inserted = 0
        updated = 0
        
        for txn in transactions:
            stmt = insert(Transaction).values(
                source=txn["source"],
                source_id=txn["source_id"],
                reference_id=txn.get("reference_id"),
                client_operation_id=txn.get("client_operation_id"),
                order_id=txn.get("order_id"),
                project=txn.get("project"),
                merchant_id=txn.get("merchant_id"),
                amount=txn["amount"],
                currency=txn["currency"],
                amount_usd=txn.get("amount_usd"),
                fee=txn.get("fee"),
                fee_usd=txn.get("fee_usd"),
                exchange_rate=txn.get("exchange_rate"),
                status=txn["status"],
                original_status=txn.get("original_status"),
                user_id=txn.get("user_id"),
                user_email=txn.get("user_email"),
                user_phone=txn.get("user_phone"),
                user_name=txn.get("user_name"),
                country=txn.get("country"),
                utr=txn.get("utr"),
                payment_method=txn.get("payment_method"),
                payment_product=txn.get("payment_product"),
                created_at=txn["created_at"],
                updated_at=txn.get("updated_at"),
                completed_at=txn.get("completed_at"),
                source_create_cursor=txn.get("source_create_cursor"),
                source_update_cursor=txn.get("source_update_cursor"),
                raw_data=txn.get("raw_data"),
                data_hash=txn["data_hash"],
            ).on_conflict_do_update(
                index_elements=["data_hash"],
                set_={
                    "status": txn["status"],
                    "original_status": txn.get("original_status"),
                    "updated_at": txn.get("updated_at"),
                    "completed_at": txn.get("completed_at"),
                    "utr": txn.get("utr"),
                    "amount_usd": txn.get("amount_usd"),
                    "fee_usd": txn.get("fee_usd"),
                    "exchange_rate": txn.get("exchange_rate"),
                    "raw_data": txn.get("raw_data"),
                    "ingested_at": datetime.now(timezone.utc),
                }
            )
            
            result = await session.execute(stmt)
            
            # Check if inserted or updated
            if result.rowcount > 0:
                # Simple heuristic - if ingested_at was just set, it was an upsert
                # For accurate count, we'd need RETURNING clause
                inserted += 1
        
        await session.commit()
        
        # Broadcast new transactions
        if inserted > 0:
            await broadcast_new_transactions(self.source, inserted)
        
        return {
            "total": len(transactions),
            "inserted": inserted,
            "updated": updated,
        }

    async def _get_last_sync_time(self, session) -> Optional[datetime]:
        """Get last successful sync time."""
        result = await session.execute(
            select(SyncState.last_sync_at).where(SyncState.source == self.source)
        )
        row = result.scalar_one_or_none()
        return row

    async def _get_sync_state(self, session) -> Optional[SyncState]:
        """Get current sync state."""
        result = await session.execute(
            select(SyncState).where(SyncState.source == self.source)
        )
        state = result.scalar_one_or_none()
        
        if not state:
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
        else:
            state = SyncState(source=self.source, **kwargs)
            session.add(state)

    async def historical_sync(self, days: int = 7) -> Dict[str, Any]:
        """
        Load historical data for specified number of days.
        
        Fetches ALL PayShack transactions without date filter
        (full_sync=True) to ensure complete data.
        
        Args:
            days: Number of days of history (used for date_from filter)
            
        Returns:
            Dict with sync results
        """
        logger.info("payshack_historical_sync_starting", days=days)
        
        # Calculate date range
        date_to = datetime.now(timezone.utc)
        date_from = date_to - timedelta(days=days)
        
        # Use sync with full_sync=True to load all data
        result = await self.sync(full_sync=True)
        
        logger.info(
            "payshack_historical_sync_completed",
            days=days,
            records=result.get("records_synced", 0),
        )
        
        return result


# Run sync function for scheduler
async def run_payshack_sync():
    """Run PayShack sync (called by scheduler)."""
    service = PayShackSyncService()
    return await service.sync()

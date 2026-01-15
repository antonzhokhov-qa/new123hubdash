"""ETL Scheduler for periodic data synchronization."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = structlog.get_logger()

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


async def start_scheduler():
    """Initialize and start the ETL scheduler."""
    global _scheduler
    
    _scheduler = AsyncIOScheduler(timezone="UTC")
    
    # Add Vima sync job - every 1 minute for fast updates
    _scheduler.add_job(
        run_vima_sync,
        trigger=IntervalTrigger(seconds=settings.vima_sync_interval_seconds),
        id="vima_sync",
        name="Vima API Sync",
        replace_existing=True,
        max_instances=1,  # Prevent concurrent runs
    )
    
    # Add PayShack sync job - every 5 minutes
    _scheduler.add_job(
        run_payshack_sync,
        trigger=IntervalTrigger(seconds=settings.payshack_sync_interval_seconds),
        id="payshack_sync",
        name="PayShack Sync",
        replace_existing=True,
        max_instances=1,
    )
    
    # Add PayShack metadata sync job - every 5 minutes for fresh balance data
    _scheduler.add_job(
        run_payshack_metadata_sync,
        trigger=IntervalTrigger(seconds=settings.payshack_metadata_sync_interval_seconds),
        id="payshack_metadata_sync",
        name="PayShack Metadata Sync",
        replace_existing=True,
        max_instances=1,
    )
    
    # Add currency rates refresh job - every 30 minutes
    _scheduler.add_job(
        refresh_currency_rates,
        trigger=IntervalTrigger(seconds=settings.currency_rate_refresh_seconds),
        id="currency_rates_refresh",
        name="Currency Rates Refresh",
        replace_existing=True,
        max_instances=1,
    )
    
    _scheduler.start()
    logger.info(
        "scheduler_started",
        vima_interval=settings.vima_sync_interval_seconds,
        payshack_interval=settings.payshack_sync_interval_seconds,
        payshack_metadata_interval=settings.payshack_metadata_sync_interval_seconds,
        currency_refresh_interval=settings.currency_rate_refresh_seconds,
    )
    
    # Pre-load currency rates at startup
    asyncio.create_task(refresh_currency_rates())
    
    # Run initial sync after short delay
    asyncio.create_task(initial_sync())


async def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
        logger.info("scheduler_stopped")


async def check_first_run() -> bool:
    """
    Check if this is the first run (no transactions in database).
    
    Returns:
        True if database is empty (first run), False otherwise
    """
    from sqlalchemy import select, func
    from app.db.session import async_session_maker
    from app.models.transaction import Transaction
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(func.count(Transaction.id))
        )
        count = result.scalar() or 0
        
        logger.info("check_first_run", transaction_count=count)
        return count == 0


async def initial_sync():
    """
    Run initial sync after startup.
    
    If this is the first run (empty database), loads historical data
    for the configured number of days from both Vima and PayShack.
    Otherwise, runs regular incremental sync.
    """
    await asyncio.sleep(5)  # Wait for app to fully start
    
    is_first_run = await check_first_run()
    
    if is_first_run:
        logger.info(
            "first_run_detected_loading_historical_data",
            days=settings.initial_sync_days,
        )
        
        # Load historical data from both sources in parallel
        await asyncio.gather(
            run_vima_historical_sync(days=settings.initial_sync_days),
            run_payshack_historical_sync(days=settings.initial_sync_days),
        )
        
        logger.info("first_run_historical_sync_completed")
    else:
        logger.info("running_incremental_sync")
        # Run regular incremental sync
        await asyncio.gather(
            run_vima_sync(),
            run_payshack_sync(),
        )


async def run_vima_sync():
    """Execute Vima sync job."""
    from app.etl.vima_sync import VimaSyncService
    
    logger.info("vima_sync_job_started")
    
    try:
        service = VimaSyncService()
        result = await service.sync()
        
        logger.info(
            "vima_sync_job_completed",
            records_synced=result.get("records_synced", 0),
            duration_ms=result.get("duration_ms", 0),
        )
    except Exception as e:
        logger.error("vima_sync_job_failed", error=str(e))


async def run_payshack_sync():
    """Execute PayShack sync job."""
    from app.etl.payshack_sync import PayShackSyncService
    
    logger.info("payshack_sync_job_started")
    
    try:
        service = PayShackSyncService()
        result = await service.sync()
        
        logger.info(
            "payshack_sync_job_completed",
            records_synced=result.get("records_synced", 0),
        )
    except Exception as e:
        logger.error("payshack_sync_job_failed", error=str(e))


async def trigger_vima_sync():
    """Manually trigger Vima sync."""
    logger.info("vima_sync_manual_trigger")
    await run_vima_sync()


async def trigger_payshack_sync():
    """Manually trigger PayShack sync."""
    logger.info("payshack_sync_manual_trigger")
    await run_payshack_sync()


async def run_payshack_metadata_sync():
    """Execute PayShack metadata sync job."""
    from app.etl.payshack_metadata_sync import run_payshack_metadata_sync as sync_metadata
    
    logger.info("payshack_metadata_sync_job_started")
    
    try:
        result = await sync_metadata()
        
        logger.info(
            "payshack_metadata_sync_job_completed",
            clients=result.get("clients", {}).get("fetched", 0),
            resellers=result.get("resellers", {}).get("fetched", 0),
            providers=result.get("providers", {}).get("fetched", 0),
        )
    except Exception as e:
        logger.error("payshack_metadata_sync_job_failed", error=str(e))


async def trigger_payshack_metadata_sync():
    """Manually trigger PayShack metadata sync."""
    logger.info("payshack_metadata_sync_manual_trigger")
    await run_payshack_metadata_sync()


async def run_vima_historical_sync(days: int = 7):
    """
    Execute Vima historical sync - loads data for specified days.
    
    Args:
        days: Number of days of history to load
    """
    from app.etl.vima_sync import VimaSyncService
    
    logger.info("vima_historical_sync_job_started", days=days)
    
    try:
        service = VimaSyncService()
        result = await service.historical_sync(days=days)
        
        logger.info(
            "vima_historical_sync_job_completed",
            records_synced=result.get("records_synced", 0),
            days=days,
            duration_ms=result.get("duration_ms", 0),
        )
        return result
    except Exception as e:
        logger.error("vima_historical_sync_job_failed", error=str(e), days=days)
        return {"status": "failed", "error": str(e)}


async def run_payshack_historical_sync(days: int = 7):
    """
    Execute PayShack historical sync - loads all data.
    
    Args:
        days: Number of days of history to load
    """
    from app.etl.payshack_sync import PayShackSyncService
    
    logger.info("payshack_historical_sync_job_started", days=days)
    
    try:
        service = PayShackSyncService()
        result = await service.historical_sync(days=days)
        
        logger.info(
            "payshack_historical_sync_job_completed",
            records_synced=result.get("records_synced", 0),
            days=days,
        )
        return result
    except Exception as e:
        logger.error("payshack_historical_sync_job_failed", error=str(e), days=days)
        return {"status": "failed", "error": str(e)}


async def trigger_historical_sync(days: int = None):
    """
    Manually trigger historical sync for both sources.
    
    Args:
        days: Number of days to load (defaults to settings.initial_sync_days)
    """
    if days is None:
        days = settings.initial_sync_days
    
    logger.info("historical_sync_manual_trigger", days=days)
    
    results = await asyncio.gather(
        run_vima_historical_sync(days=days),
        run_payshack_historical_sync(days=days),
    )
    
    return {
        "vima": results[0],
        "payshack": results[1],
    }


async def refresh_currency_rates():
    """
    Refresh currency exchange rates from external API.
    
    Called periodically by scheduler (default: every 30 minutes).
    """
    from app.services.currency import currency_service
    
    logger.info("currency_rates_refresh_started")
    
    try:
        success = await currency_service.refresh_rates()
        
        if success:
            # Get current rates for logging
            rates = await currency_service.get_rates()
            logger.info(
                "currency_rates_refresh_completed",
                inr_usd=rates.get("INR"),
                eur_usd=rates.get("EUR"),
                currencies_count=len(rates),
            )
        else:
            logger.warning("currency_rates_refresh_failed_using_cache")
            
    except Exception as e:
        logger.error("currency_rates_refresh_error", error=str(e))

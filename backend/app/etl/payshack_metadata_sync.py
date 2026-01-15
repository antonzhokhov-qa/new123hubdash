"""PayShack metadata synchronization.

Syncs clients, resellers, service providers from PayShack API.
Creates balance snapshots for historical tracking.
"""

from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.db.redis import cache
from app.integrations.payshack import PayShackClient, payshack_client
from app.models.payshack_metadata import (
    PayShackClient as PayShackClientModel,
    PayShackReseller,
    PayShackServiceProvider,
    PayShackBalanceSnapshot,
)
from app.api.websocket import broadcast_sync_event

logger = structlog.get_logger()


async def sync_payshack_clients(client: Optional[PayShackClient] = None) -> dict:
    """
    Sync all clients from PayShack API.
    
    Returns:
        Stats dict with counts
    """
    client = client or payshack_client
    
    logger.info("payshack_clients_sync_start")
    
    stats = {
        "fetched": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
    }
    
    try:
        # Fetch clients from API
        clients_data = await client.get_clients()
        stats["fetched"] = len(clients_data)
        
        if not clients_data:
            logger.warning("payshack_clients_sync_empty")
            return stats
        
        async with async_session_factory() as db:
            for client_data in clients_data:
                try:
                    client_id = (
                        client_data.get("clientId") or 
                        client_data.get("id") or 
                        client_data.get("_id")
                    )
                    
                    if not client_id:
                        logger.warning("payshack_client_no_id", data=client_data)
                        continue
                    
                    # Upsert client
                    stmt = insert(PayShackClientModel).values(
                        client_id=str(client_id),
                        reseller_id=client_data.get("resellerId"),
                        name=client_data.get("name") or client_data.get("companyName") or "Unknown",
                        email=client_data.get("email"),
                        company_name=client_data.get("companyName"),
                        status=client_data.get("status"),
                        is_active=client_data.get("isActive", True),
                        balance=client_data.get("balance") or 0,
                        wallet_balance=client_data.get("walletBalance") or 0,
                        currency="INR",
                        commission_rate=client_data.get("commissionRate"),
                        raw_data=client_data,
                        synced_at=datetime.now(timezone.utc),
                    ).on_conflict_do_update(
                        index_elements=["client_id"],
                        set_={
                            "name": client_data.get("name") or client_data.get("companyName") or "Unknown",
                            "email": client_data.get("email"),
                            "company_name": client_data.get("companyName"),
                            "status": client_data.get("status"),
                            "is_active": client_data.get("isActive", True),
                            "balance": client_data.get("balance") or 0,
                            "wallet_balance": client_data.get("walletBalance") or 0,
                            "commission_rate": client_data.get("commissionRate"),
                            "raw_data": client_data,
                            "updated_at": datetime.now(timezone.utc),
                            "synced_at": datetime.now(timezone.utc),
                        }
                    )
                    
                    result = await db.execute(stmt)
                    
                    # Check if insert or update
                    if result.rowcount > 0:
                        stats["updated"] += 1
                    else:
                        stats["created"] += 1
                        
                except Exception as e:
                    logger.error("payshack_client_sync_error", error=str(e), client_id=client_id)
                    stats["errors"] += 1
            
            await db.commit()
        
        logger.info("payshack_clients_sync_complete", stats=stats)
        
        # Broadcast event
        await broadcast_sync_event({
            "type": "metadata_sync",
            "entity": "clients",
            "stats": stats,
        })
        
    except Exception as e:
        logger.error("payshack_clients_sync_failed", error=str(e))
        stats["errors"] += 1
    
    return stats


async def sync_payshack_resellers(client: Optional[PayShackClient] = None) -> dict:
    """
    Sync all resellers from PayShack API.
    """
    client = client or payshack_client
    
    logger.info("payshack_resellers_sync_start")
    
    stats = {
        "fetched": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
    }
    
    try:
        resellers_data = await client.get_resellers()
        stats["fetched"] = len(resellers_data)
        
        if not resellers_data:
            logger.warning("payshack_resellers_sync_empty")
            return stats
        
        async with async_session_factory() as db:
            for reseller_data in resellers_data:
                try:
                    reseller_id = (
                        reseller_data.get("resellerId") or 
                        reseller_data.get("clientId") or 
                        reseller_data.get("id")
                    )
                    
                    if not reseller_id:
                        continue
                    
                    stmt = insert(PayShackReseller).values(
                        reseller_id=str(reseller_id),
                        user_id=reseller_data.get("userId"),
                        name=reseller_data.get("name") or "Unknown",
                        email=reseller_data.get("email"),
                        role=reseller_data.get("role"),
                        status=reseller_data.get("status"),
                        is_active=reseller_data.get("isActive", True),
                        balance=reseller_data.get("balance") or 0,
                        currency="INR",
                        raw_data=reseller_data,
                        synced_at=datetime.now(timezone.utc),
                    ).on_conflict_do_update(
                        index_elements=["reseller_id"],
                        set_={
                            "name": reseller_data.get("name") or "Unknown",
                            "email": reseller_data.get("email"),
                            "role": reseller_data.get("role"),
                            "status": reseller_data.get("status"),
                            "is_active": reseller_data.get("isActive", True),
                            "balance": reseller_data.get("balance") or 0,
                            "raw_data": reseller_data,
                            "updated_at": datetime.now(timezone.utc),
                            "synced_at": datetime.now(timezone.utc),
                        }
                    )
                    
                    await db.execute(stmt)
                    stats["updated"] += 1
                    
                except Exception as e:
                    logger.error("payshack_reseller_sync_error", error=str(e))
                    stats["errors"] += 1
            
            await db.commit()
        
        logger.info("payshack_resellers_sync_complete", stats=stats)
        
    except Exception as e:
        logger.error("payshack_resellers_sync_failed", error=str(e))
        stats["errors"] += 1
    
    return stats


async def sync_payshack_service_providers(client: Optional[PayShackClient] = None) -> dict:
    """
    Sync all service providers from PayShack API.
    """
    client = client or payshack_client
    
    logger.info("payshack_providers_sync_start")
    
    stats = {
        "fetched": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
    }
    
    try:
        providers_data = await client.get_service_providers()
        stats["fetched"] = len(providers_data)
        
        if not providers_data:
            logger.warning("payshack_providers_sync_empty")
            return stats
        
        async with async_session_factory() as db:
            for provider_data in providers_data:
                try:
                    provider_id = (
                        provider_data.get("spId") or 
                        provider_data.get("id") or 
                        provider_data.get("_id")
                    )
                    
                    if not provider_id:
                        continue
                    
                    stmt = insert(PayShackServiceProvider).values(
                        provider_id=str(provider_id),
                        name=provider_data.get("name") or "Unknown",
                        code=provider_data.get("code"),
                        status=provider_data.get("status"),
                        is_active=provider_data.get("isActive", True),
                        supports_payin=provider_data.get("supportsPayin", True),
                        supports_payout=provider_data.get("supportsPayout", True),
                        raw_data=provider_data,
                        synced_at=datetime.now(timezone.utc),
                    ).on_conflict_do_update(
                        index_elements=["provider_id"],
                        set_={
                            "name": provider_data.get("name") or "Unknown",
                            "code": provider_data.get("code"),
                            "status": provider_data.get("status"),
                            "is_active": provider_data.get("isActive", True),
                            "supports_payin": provider_data.get("supportsPayin", True),
                            "supports_payout": provider_data.get("supportsPayout", True),
                            "raw_data": provider_data,
                            "updated_at": datetime.now(timezone.utc),
                            "synced_at": datetime.now(timezone.utc),
                        }
                    )
                    
                    await db.execute(stmt)
                    stats["updated"] += 1
                    
                except Exception as e:
                    logger.error("payshack_provider_sync_error", error=str(e))
                    stats["errors"] += 1
            
            await db.commit()
        
        logger.info("payshack_providers_sync_complete", stats=stats)
        
    except Exception as e:
        logger.error("payshack_providers_sync_failed", error=str(e))
        stats["errors"] += 1
    
    return stats


async def create_balance_snapshots() -> dict:
    """
    Create balance snapshots for all clients and resellers.
    """
    logger.info("balance_snapshots_start")
    
    stats = {"created": 0, "errors": 0}
    now = datetime.now(timezone.utc)
    
    async with async_session_factory() as db:
        try:
            # Snapshot client balances
            result = await db.execute(select(PayShackClientModel))
            clients = result.scalars().all()
            
            for client in clients:
                snapshot = PayShackBalanceSnapshot(
                    entity_type="client",
                    entity_id=client.client_id,
                    entity_name=client.name,
                    balance=client.balance or 0,
                    currency="INR",
                    snapshot_at=now,
                )
                db.add(snapshot)
                stats["created"] += 1
            
            # Snapshot reseller balances
            result = await db.execute(select(PayShackReseller))
            resellers = result.scalars().all()
            
            for reseller in resellers:
                snapshot = PayShackBalanceSnapshot(
                    entity_type="reseller",
                    entity_id=reseller.reseller_id,
                    entity_name=reseller.name,
                    balance=reseller.balance or 0,
                    currency="INR",
                    snapshot_at=now,
                )
                db.add(snapshot)
                stats["created"] += 1
            
            await db.commit()
            
        except Exception as e:
            logger.error("balance_snapshots_error", error=str(e))
            stats["errors"] += 1
    
    logger.info("balance_snapshots_complete", stats=stats)
    return stats


async def run_payshack_metadata_sync():
    """
    Run full PayShack metadata sync.
    
    Syncs: clients, resellers, service providers.
    Creates balance snapshots.
    """
    logger.info("payshack_metadata_sync_start")
    
    results = {}
    
    try:
        # Sync clients
        results["clients"] = await sync_payshack_clients()
        
        # Sync resellers
        results["resellers"] = await sync_payshack_resellers()
        
        # Sync service providers
        results["providers"] = await sync_payshack_service_providers()
        
        # Create balance snapshots
        results["snapshots"] = await create_balance_snapshots()
        
        logger.info("payshack_metadata_sync_complete", results=results)
        
        # Broadcast completion
        await broadcast_sync_event({
            "type": "metadata_sync_complete",
            "results": results,
        })
        
    except Exception as e:
        logger.error("payshack_metadata_sync_failed", error=str(e))
        results["error"] = str(e)
    
    return results
